"""
Implementation of various trading strategies.

"""
from cointrol.core.models import (
    Order, TradingSession,
    RelativeStrategyProfile, FixedStrategyProfile
)


class TradeAction:

    BUY, SELL = Order.BUY, Order.SELL

    def __init__(self, action, price):
        self.action = action
        self.price = price

    def __str__(self):
        return '{action} at ${price}'.format(
            action=Order.TYPES[self.action],
            price=self.price
        )


class BaseTradingStrategy:

    def __init__(self,
                 session: TradingSession,
                 last_order: Order):
        self.session = session
        self.profile = session.profile
        self.last_order = last_order

    def get_trade_action(self) -> TradeAction:
        if self.last_order.type == Order.SELL:
            return TradeAction(action=Order.BUY,
                               price=self.get_buy_price())
        else:
            return TradeAction(action=Order.SELL,
                               price=self.get_sell_price())

    def get_buy_price(self):
        raise NotImplementedError

    def get_sell_price(self):
        raise NotImplementedError


class FixedStrategy(BaseTradingStrategy):
    profile = None
    """:type: FixedStrategyProfile"""

    def get_buy_price(self):
        return self.profile.buy

    def get_sell_price(self):
        return self.profile.sell


class RelativeStrategy(BaseTradingStrategy):
    profile = None
    """:type: RelativeStrategyProfile"""

    def get_buy_price(self):
        return self.last_order.price * (self.profile.buy / 100)

    def get_sell_price(self):
        return self.last_order.price * (self.profile.sell / 100)


# {Profile model class: implementation class}
MAPPING = {
    FixedStrategyProfile: FixedStrategy,
    RelativeStrategyProfile: RelativeStrategy,
}


def get_for_session(session, latest_order) -> BaseTradingStrategy:
    implementation_class = MAPPING[type(session.profile)]
    return implementation_class(session, latest_order)
