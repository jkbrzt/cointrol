"""
Django admin definition

"""
from django.contrib import admin

from cointrol.core.models import (
    Balance, Order, Transaction, Account, Ticker,
    TradingSession, FixedStrategyProfile, RelativeStrategyProfile,
)


class ModelWithBalanceAdminMixin:

    def usd_balance(self, obj):
        return '{}'.format(obj.balance.usd_balance)

    def btc_balance(self, obj):
        return '{}'.format(obj.balance.btc_balance)


class OrderAdmin(admin.ModelAdmin, ModelWithBalanceAdminMixin):

    list_display = [
        'id',
        'datetime',
        'type',
        'price',
        'amount',
        'total',
        'status',
        'usd_balance',
        'btc_balance',
    ]
    list_filter = [
        'status',
        'type',
    ]
    search_fields = [
        'id',
    ]
    date_hierarchy = 'datetime'


class TransactionAdmin(admin.ModelAdmin, ModelWithBalanceAdminMixin):
    date_hierarchy = 'datetime'

    list_display = [
        'id',
        'order_id',
        'datetime',
        'type',
        'trade_type',
        'btc',
        'usd',
        'btc_usd',
        'fee',
        'usd_balance',
        'btc_balance',
    ]
    list_filter = [
        'type',
    ]
    search_fields = [
        'id',
        'order_id',
    ]

    def order_id(self, obj):
        return obj.order_id


class BalanceAdmin(admin.ModelAdmin):
    list_filter = [
        'inferred',
    ]
    list_display = [
        'timestamp',
        'id',
        'inferred',
        'usd_balance',
        'btc_balance',
        'usd_reserved',
        'btc_reserved',
        'btc_available',
        'usd_available',
        'fee',
    ]


class TickerAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'last',
        'high',
        'low',
        'bid',
        'ask',
        'volume',
    ]


class TradingSessionAdmin(admin.ModelAdmin):
    list_filter = [
        'status'
    ]
    list_display = [
        'created',
        'status',
        'note',
        'strategy_profile',
        'repeat_times',
        'repeat_until',
    ]


class StrategyProfileAdmin(admin.ModelAdmin):

    list_display = [
        'created',
        'note',
        'buy',
        'sell',
    ]


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Balance, BalanceAdmin)
admin.site.register(Ticker, TickerAdmin)
admin.site.register(TradingSession, TradingSessionAdmin)
admin.site.register([RelativeStrategyProfile, FixedStrategyProfile],
                    StrategyProfileAdmin)
admin.site.register(Account)
