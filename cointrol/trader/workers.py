"""
Async workers for Bitstamp API polling, trading, etc.

"""
import logging
from itertools import groupby
from operator import itemgetter

import redis
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.db.models.query import QuerySet
from tornado.gen import coroutine, Task
from tornado.ioloop import IOLoop

from cointrol.utils import json
from cointrol.core.models import Transaction, User, Order, Ticker, Balance
from cointrol.core import serializers
from . import bitstamp
from . import strategies


redis_client = redis.Redis()
log = logging.getLogger(__name__)

# TODO: support multiple users/accounts
account = User.objects.get().account
bitstamp_client = bitstamp.BitstampClient(username=account.username,
                                          key=account.api_key,
                                          secret=account.api_secret)


class Worker:
    """Abstract async worker"""
    timeout = 3

    def __init__(self):
        self.log = log.getChild(type(self).__name__.replace('Watcher', ''))
        self.reset()
        self.is_running = False

    @property
    def successes(self):
        return self.iterations - self.failures

    @coroutine
    def work(self):
        raise NotImplementedError

    def run_once(self):
        return self.run_forever(until_number_of_successes=1)

    @coroutine
    def run_forever(self, until_number_of_successes=None):
        assert not self.is_running
        self.reset()
        self.is_running = True

        if until_number_of_successes is not None:
            self.log.info('running until %s successes',
                          until_number_of_successes)
        else:
            self.log.info('running forever')

        while not self.should_stop:
            try:
                result = yield self.work()
            except Exception as e:
                result = None
                self.failures += 1
                if isinstance(e, bitstamp.InvalidNonceError):
                    # Anything > info would send an email.
                    self.log.info('invalid nonce', exc_info=True)
                else:
                    self.log.exception('work failed')
                self.log.info('will try again')
            else:
                self.log.debug('work success')
            finally:
                self.iterations += 1

            if (until_number_of_successes is not None
                    and self.successes >= until_number_of_successes):
                self.stop()
                self.is_running = False
                # Only really useful with until_number_of_successes=1
                return result
            else:
                yield self.sleep()

    def stop(self):
        self.log.info('stopping')
        self.should_stop = True

    def reset(self):
        self.should_stop = False
        self.iterations = 0
        self.failures = 0

    def publish(self, model_or_models):
        if isinstance(model_or_models, QuerySet):
            models = list(model_or_models)
        elif not isinstance(model_or_models, list):
            models = [model_or_models]
        else:
            models = model_or_models
        model = models[0]
        serializer_class = serializers.MAPPING[type(model)]
        msg = json.dumps({
            'type': type(model).__name__,
            'models': serializer_class(models, many=True).data
        })
        self.log.debug('publishing change "%s": %s', msg)
        redis_client.publish('model_changes', msg)

    @coroutine
    def sleep(self):
        self.log.debug('sleeping for %d seconds', self.timeout)
        yield Task(IOLoop.instance().add_timeout,
                   IOLoop.instance().time() + self.timeout)
        self.log.debug('woken up')


class Monitoring(Worker):
    """Broadcasts beacon packets to indicate the backend is alive."""

    timeout = 1

    @coroutine
    def work(self):
        redis_client.publish('monitoring', json.dumps({'type': 'beacon'}))


class BalanceWatcher(Worker):
    """Polls Bitstamp account balance, saves & broadcasts it on changes."""

    timeout = 3

    @coroutine
    def work(self):
        current = yield Task(bitstamp_client.account_balance)

        try:
            latest = account.balances.latest()
        except Balance.DoesNotExist:
            differs = True
        else:
            differs = any(getattr(latest, k) != v for k, v in current.items())

        if not differs:
            self.log.debug('no balance change')
        else:
            self.log.info('current balance differs from latest, saving, %r',
                          current)
            self.publish(account.balances.create(
                inferred=False,
                timestamp=timezone.now(),
                **current
            ))


class Trader(Worker):
    # TODO: most of the logic here should be moved to `.strategies`.

    def get_trade_action(self, session):
        try:
            latest_order = Order.objects\
                .filter(status=Order.PROCESSED).latest()
        except Order.DoesNotExist:
            latest_order = None
        strategy = strategies.get_for_session(session, latest_order)
        trade_action = strategy.get_trade_action()
        self.log.info('trading strategy: %s, trade_action: %s',
                      type(strategy).__name__, trade_action)
        return trade_action

    @coroutine
    def work(self):

        trading_session = account.get_active_trading_session()
        self.log.info('active trading session: %r', trading_session)
        if not trading_session:
            return

        trade_action = self.get_trade_action(trading_session)
        if not trade_action:
            return
        yield balance_watcher.run_once()
        balance = account.balances.filter(inferred=False).latest()
        ticker = Ticker.objects.latest()

        fee_multiplier = (100 - balance.fee) / 100
        if trade_action.action == Order.SELL:
            order_task = bitstamp_client.sell_limit_order
            amount = balance.btc_available * fee_multiplier
            price = max(trade_action.price, ticker.ask)
        elif trade_action.action == Order.BUY:
            order_task = bitstamp_client.buy_limit_order
            amount = ((balance.usd_available / trade_action.price)
                      * fee_multiplier)
            price = min(trade_action.price, ticker.bid)
        else:
            raise TypeError(trade_action)

        price = round(price, 2)
        amount = round(amount, 8)
        # Warn to send email.
        self.log.warning('trade task: %s(amount=%s, price=%s)',
                         order_task.__name__, amount, price)

        if not settings.COINTROL_DO_TRADE:
            self.log.info('settings.COINTROL_DO_TRADE=False; not executing')
        else:
            self.log.info('settings.COINTROL_DO_TRADE=True; executing')
            open_order_response = yield Task(order_task, amount=amount, price=price)
            return trading_session, open_order_response


balance_watcher = BalanceWatcher()
trader = Trader()


class TransactionsWatcher(Worker):

    timeout = 15

    @coroutine
    def get_new_transactions(self):
        """Return new transactions sorted by created asc."""
        self.log.info('getting new transactions')
        try:
            latest = account.transactions.latest()
        except Transaction.DoesNotExist:
            latest = None
        self.log.debug('local latest transaction: %r', latest)
        offset = 0
        new_transactions = []
        done = False
        while not done:
            page = yield Task(bitstamp_client.user_transactions,
                              offset=offset, limit=10, )
            offset += 10
            if not page:
                break
            for transaction in page:
                if latest and transaction['id'] == latest.pk:
                    done = True
                    break
                new_transactions.append(transaction)
        if new_transactions:
            self.log.info('%d new transactions: %r',
                          len(new_transactions), new_transactions)
        return list(reversed(new_transactions))

    @coroutine
    def work(self):
        self.log.info('start syncing transactions')
        new_transactions = yield self.get_new_transactions()

        if not new_transactions:
            return

        by_order = groupby(new_transactions, itemgetter('order_id'))
        for order_id, transaction_group in by_order:
            transaction_group = [
                Transaction(account=account, **transaction)
                for transaction in transaction_group
            ]
            if order_id:
                usd = sum(t.usd for t in transaction_group)
                btc = sum(t.btc for t in transaction_group)
                dt = min(t.datetime for t in transaction_group)
                try:
                    order = account.orders.get(pk=order_id)
                except Order.DoesNotExist:
                    # Most like a historical order.
                    order = Order(
                        account=account,
                        pk=order_id,
                        datetime=dt,
                        type=Order.SELL if usd > 0 else Order.BUY,
                        status=Order.PROCESSED,
                    )
                    self.log.info('order for transaction group does not exist')
                order.amount += abs(btc)
                order.price = abs(usd / order.amount)
                order.total += abs(usd)
                order.save()
                self.publish(order)
                for transaction in transaction_group:
                    transaction.save()
                order.balance = transaction_group[-1].balance
                order.save()
            else:
                for transaction in transaction_group:
                    transaction.save()
            self.publish(transaction_group)

        yield balance_watcher.run_once()
        self.log.info('end syncing transactions')


class OrdersWatcher(Worker):

    timeout = 10

    @coroutine
    def work(self):
        open_orders_response = yield Task(bitstamp_client.open_orders)

        self.log.info('%s open orders: %r',
                      len(open_orders_response),
                      open_orders_response)

        if open_orders_response:
            # There are orders, but they must have been created manually.
            trading_session = None
        else:
            # No open orders - run trader: may create and return an open order,
            # which we process immediately in  this run.
            self.log.info('no orders, invoking trader')
            result = yield trader.run_once()
            self.log.info('trader returned order: %r', result)
            if not result:
                return
            trading_session, placed_order_response = result
            open_orders_response = [placed_order_response]

        if open_orders_response:
            for order in open_orders_response:
                if not Order.objects.filter(pk=order.id).exists():
                    self.log.info('saving %r', order)
                    order = account.orders.create(
                        trading_session=trading_session,
                        id=order.id,
                        price=order.price,
                        amount=order.amount,
                        type=order.type,
                        datetime=order.datetime,
                        balance=account.balances.latest(),
                        status=Order.OPEN,
                    )
                    self.publish(order)
                    self.log.info('saved %r', order)

        has_changes = yield self.update_existing_orders(
            open_order_ids=[order.id for order in open_orders_response])

        if open_orders_response or has_changes:
            yield balance_watcher.run_once()

    @coroutine
    def update_existing_orders(self, open_order_ids):

        now = timezone.now()

        # OPEN => PROCESSED
        now_processed = account.orders\
            .filter(status=Order.OPEN)\
            .exclude(Q(id__in=open_order_ids) | Q(transactions=None))
        now_processed_ids = list(now_processed.values_list('id', flat=True))
        if now_processed_ids:
            now_processed.update(status=Order.PROCESSED, status_changed=now)

        # OPEN => CANCELLED
        now_cancelled = account.orders\
            .filter(status=Order.OPEN, transactions=None)\
            .exclude(id__in=open_order_ids)
        now_cancelled_ids = list(now_cancelled.values_list('id', flat=True))
        if now_cancelled_ids:
            now_cancelled.update(status=Order.CANCELLED, status_changed=now)

        # Publish the updated ones.
        now_updated_ids = now_processed_ids + now_cancelled_ids
        if now_updated_ids:
            now_updated_orders = Order.objects.filter(id__in=now_updated_ids)
            self.publish(now_updated_orders)
            yield balance_watcher.run_once()

        return bool(now_updated_ids)


class TickerWatcher(Worker):

    timeout = 3

    @coroutine
    def work(self):
        self.log.debug('getting ticker')
        ticker = yield Task(bitstamp_client.ticker)
        if not Ticker.objects.filter(timestamp=ticker.timestamp).exists():
            ticker = Ticker.objects.create(**ticker)
            self.publish(ticker)
            self.log.debug('saved %r', ticker)
