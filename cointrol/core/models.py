from collections import OrderedDict

from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property

from .castable import CastableModel
from .fields import PriceField, AmountField, PercentField


###############################################################################
# User models
###############################################################################


class User(AbstractUser):
    """Cointrol user"""

    class Meta:
        db_table = 'user'

    @property
    def account(self):
        # TODO: support multiple Bitstamp accounts per user
        return self.accounts.get()


class Account(models.Model):
    """Bitstamp account"""
    user = models.ForeignKey(User, related_name='accounts')
    username = models.CharField(max_length=255, blank=True, help_text='Bitstamp login number')
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'account'

    def __str__(self):
        return 'account for {}'.format(self.user)

    def get_active_trading_session(self):
        """
        Return the current `ACTIVE` and unfinished `TradingSession`, or `None`.

        This is the exclusive method to get the session. It has
        side-effects in the form of changing status from
        `ACTIVE` to `FINISHED`, and from `QUEUED` to `ACTIVE` before
        return a session.

        """
        ACTIVE, QUEUED, FINISHED = (TradingSession.ACTIVE,
                                    TradingSession.QUEUED,
                                    TradingSession.FINISHED)
        try:
            session = self.trading_sessions.get(status=ACTIVE)
        except TradingSession.DoesNotExist:
            try:
                session = self.trading_sessions\
                    .filter(status=QUEUED)\
                    .earliest()
            except TradingSession.DoesNotExist:
                session = None

        while session:
            if session.status == FINISHED:
                session = None
            elif session.status == QUEUED:
                session.set_status(ACTIVE)
            elif session.status == ACTIVE:
                if not session.is_finished():
                    return session
                else:
                    session.set_status(FINISHED)
                    try:
                        session = session.get_previous_by_created(account=self)
                    except TradingSession.DoesNotExist:
                        session = None
            else:
                raise TypeError('invalid session status: pk={}, {!r}'.format(
                    session.pk, session.status))


###############################################################################
# Trading
###############################################################################


class TradingStrategyProfile(CastableModel):
    """Base trading strategy configuration models class."""
    note = models.CharField(max_length=255, blank=True)
    account = models.ForeignKey(Account)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def type_name(self):
        if type(self) == TradingStrategyProfile:
            return self.cast().type_name
        return type(self).__name__

    def __str__(self):
        return str(self.cast())


class RelativeStrategyProfile(TradingStrategyProfile):
    """Configuration for relative trading strategy."""
    buy = PercentField()
    sell = PercentField()

    class Meta:
        db_table = 'strategy_profile_relative'

    def __str__(self):
        return 'relative buy at {buy}%, sell at ${sell}%'.format(
            buy=self.buy, sell=self.sell)

    def save(self, *args, **kwargs):
        min_fee = .2
        assert self.buy < 100 - min_fee
        assert self.sell > 100 + min_fee
        return super().save(*args, **kwargs)


class FixedStrategyProfile(TradingStrategyProfile):
    """Configuration for fixed trading strategy."""
    buy = PriceField()
    sell = PriceField()

    class Meta:
        db_table = 'strategy_profile_fixed'

    def __str__(self):
        return 'fixed buy at ${buy}, sell at ${sell}'.format(
            buy=self.buy, sell=self.sell)


class TradingSession(models.Model):
    QUEUED, ACTIVE, FINISHED = 'queued', 'active', 'finished'
    STATUSES = [QUEUED, ACTIVE, FINISHED]
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(Account, related_name='trading_sessions')
    status = models.CharField(
        choices=zip(STATUSES, STATUSES),
        max_length=255,
        db_index=True
    )
    became_active = models.DateTimeField(null=True, blank=True)
    became_finished = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    strategy_profile = models.ForeignKey(TradingStrategyProfile)

    # None - no limit; 1 - one repeat left; 0 - done
    repeat_times = models.PositiveSmallIntegerField(default=None,
                                                    null=True,
                                                    blank=True)
    # None - no limit
    repeat_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'trading_session'
        ordering = ['-created']
        get_latest_by = 'created'

    def __str__(self):
        return '{status} session with {strategy}'.format(
            status=self.status,
            strategy=self.strategy_profile,
        )

    def set_status(self, status):
        if status == self.ACTIVE:
            assert self.status == self.QUEUED
            assert self.became_active is None
            assert self.became_finished is None
            self.became_active = timezone.now()
        elif status == self.FINISHED:
            assert self.status == self.ACTIVE
            assert self.became_active is not None
            assert self.became_finished is None
            self.became_finished = timezone.now()
        self.status = status
        self.save()

    @cached_property
    def profile(self):
        """Accessor for casted strategy profile."""
        return self.strategy_profile.cast()

    def is_expired(self):
        return (self.repeat_until is not None
                and self.repeat_until > timezone.now())

    def is_done(self):
        return (self.repeat_times is not None
                and self.repeat_times >= self.orders.count())

    def is_finished(self):
        return self.is_expired() or self.is_done()


###############################################################################
# Bitstamp API-based models
# https://www.bitstamp.net/api/
###############################################################################


class Ticker(models.Model):
    """
    {
        high: "704.00",
        last: "678.57",
        timestamp: "1393958158",
        bid: "678.49",
        vwap: "677.88",
        volume: "39060.90623024",
        low: "633.64",
        ask: "678.57"
    }
    """
    timestamp = models.DateTimeField()
    volume = AmountField()
    vwap = PriceField()
    last = PriceField()
    high = PriceField()
    low = PriceField()
    bid = PriceField()
    ask = PriceField()
    open = PriceField()

    class Meta:
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'
        db_table = 'bitstamp_ticker'

    def __str__(self):
        return 'last={last}, timestamp={timestamp}'.format(**self.__dict__)


class Balance(models.Model):
    """
    usd_balance - USD balance
    btc_balance - BTC balance
    usd_reserved - USD reserved in open orders
    btc_reserved - BTC reserved in open orders
    usd_available- USD available for trading
    btc_available - BTC available for trading
    fee - customer trading fee

    """
    created = models.DateTimeField(auto_now_add=True)
    account = models.ForeignKey(Account, related_name='balances')
    inferred = models.BooleanField(default=False)
    timestamp = models.DateTimeField()

    # API fields
    fee = PercentField()
    usd_balance = AmountField()
    btc_balance = AmountField()
    usd_reserved = AmountField()
    btc_reserved = AmountField()
    btc_available = AmountField()
    usd_available = AmountField()

    eur_balance = AmountField()
    xrp_balance = AmountField()
    eur_reserved = AmountField()
    xrp_reserved = AmountField()
    eur_available = AmountField()
    xrp_available = AmountField()

    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']
        db_table = 'bitstamp_balance'

    def __str__(self):
        return '{usd:0>6} US$ | {btc:0>10} BTC'.format(
            usd=self.usd_balance,
            btc=self.btc_balance
        )


class Order(models.Model):
    OPEN, CANCELLED, PROCESSED = 'open', 'cancelled', 'processed'
    STATUSES = [OPEN, CANCELLED, PROCESSED]

    BUY, SELL = 0, 1
    TYPES = OrderedDict([(BUY, 'buy'),
                         (SELL, 'sell')])

    updated = models.DateTimeField(auto_now=True)
    account = models.ForeignKey(Account, related_name='orders')
    balance = models.ForeignKey(Balance, null=True, on_delete=models.PROTECT)
    total = AmountField()
    status = models.CharField(
        default=None,
        choices=zip(STATUSES, STATUSES),
        max_length=255,
        db_index=True
    )
    status_changed = models.DateTimeField(null=True, blank=True)
    trading_session = models.ForeignKey(
        TradingSession,
        null=True,
        on_delete=models.SET_NULL,
        related_name='orders'
    )

    # API fields.
    price = PriceField()
    amount = AmountField()
    type = models.IntegerField(choices=[(BUY, 'buy'), (SELL, 'sell')],
                               db_index=True)
    datetime = models.DateTimeField()

    def __str__(self):
        return '{type} {amount} BTC at {price} US$'.format(
            type=self.get_type_display(),
            amount=self.amount,
            price=self.price
        )

    class Meta:
        ordering = ['-datetime']
        get_latest_by = 'datetime'
        db_table = 'bitstamp_order'


class Transaction(models.Model):
    DEPOSIT, WITHDRAWAL, MARKET_TRADE = 0, 1, 2
    TYPES = [DEPOSIT, WITHDRAWAL, MARKET_TRADE]

    # MARKET_TRADE subtypes
    SELL, BUY = 'sell', 'buy'

    balance = models.ForeignKey(Balance, on_delete=models.PROTECT)
    account = models.ForeignKey(Account, related_name='transactions')
    updated = models.DateTimeField(auto_now=True)

    # API fields.
    datetime = models.DateTimeField()
    btc = AmountField()
    usd = AmountField()
    fee = AmountField()
    btc_usd = PriceField()
    order = models.ForeignKey(Order, related_name='transactions', null=True)
    type = models.PositiveSmallIntegerField(
        db_index=True,
        choices=[
            (DEPOSIT, 'deposit'),
            (WITHDRAWAL, 'withdrawal'),
            (MARKET_TRADE, 'trade'),
        ]
    )

    class Meta:
        ordering = ['-datetime']
        get_latest_by = 'datetime'
        db_table = 'bitstamp_transaction'

    def __str__(self):
        return '${usd} | {btc} BTC'.format(usd=self.usd, btc=self.btc)

    @property
    def trade_type(self):
        if self.type == Transaction.MARKET_TRADE:
            return Transaction.SELL if self.usd > 0 else Transaction.BUY

    def save(self, *args, **kwargs):
        if not self.balance_id:
            self._create_balance()
        return super().save(*args, **kwargs)

    def _create_balance(self):
        assert not self.balance_id
        older = self.account.transactions.filter(datetime__lte=self.datetime)
        aggregate = (
            {'usd': 0, 'btc': 0, 'fee': 0}
            if not older.exists() else
            older.aggregate(usd=Sum('usd'), btc=Sum('btc'), fee=Sum('fee'))
        )
        # Reflect current transaction as well.
        aggregate['usd'] += self.usd
        aggregate['fee'] += self.fee
        aggregate['btc'] += self.btc
        self.balance = self.account.balances.create(
            inferred=True,
            timestamp=self.datetime,
            usd_balance=aggregate['usd'] - aggregate['fee'],
            btc_balance=aggregate['btc'],
            fee=0,
        )


###############################################################################
# Signal listeners
###############################################################################


# noinspection PyUnusedLocal
@receiver(post_save, sender=User)
def create_default_account(instance, created, **kwargs):
    if created:
        instance.accounts.create()
