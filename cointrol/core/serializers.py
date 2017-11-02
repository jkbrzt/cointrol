"""
Model serialization for the REST and WebSocket APIs.

"""
from rest_framework import serializers

from cointrol.utils import json
from .models import (
    Account, Transaction, Order, Ticker, Balance,
    TradingSession, RelativeStrategyProfile, FixedStrategyProfile,
)


class ModelSerializer(serializers.ModelSerializer):

    def __str__(self):
        return json.dumps(self.data)


class OrderSerializer(ModelSerializer):

    trading_session = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'datetime',
            'status',
            'status_changed',
            'type',
            'price',
            'amount',
            'trading_session',
        ]


class TransactionSerializer(ModelSerializer):

    type = serializers.ReadOnlyField(source='get_type_display')
    trade_type = serializers.ReadOnlyField()
    order_id = serializers.ReadOnlyField()

    class Meta:
        model = Transaction
        fields = [
            'id',
            'order_id',
            'datetime',
            'type',
            'trade_type',
            'btc',
            'usd',
            'fee',
            'btc_usd',
        ]


class AccountSerializer(ModelSerializer):

    class Meta:
        model = Account
        fields = [
            'api_key',
            'api_secret',
        ]


class TickerSerializer(ModelSerializer):

    class Meta:
        model = Ticker
        fields = '__all__'


class BalanceSerializer(ModelSerializer):

    class Meta:
        model = Balance
        fields = '__all__'


class TradingSessionSerializer(ModelSerializer):

    profile = serializers.SerializerMethodField('get_strategy_profile')

    class Meta:
        model = TradingSession
        fields = [
            'id',
            'status',
            'created',
            'note',
            'repeat_times',
            'repeat_until',
            'became_active',
            'became_finished',
            'profile',
            'strategy_profile',
        ]

    def get_strategy_profile(self, obj):
        return MAPPING[type(obj.profile)](obj.profile).data


class BaseStrategyProfileSerializer(ModelSerializer):

    type_name = serializers.ReadOnlyField()
    description = serializers.SerializerMethodField()

    def get_description(self, obj):
        return str(obj)


class RelativeStrategyProfileSerializer(BaseStrategyProfileSerializer):

    class Meta:
        model = RelativeStrategyProfile
        fields = [
            'id',
            'type_name',
            'description',
            'created',
            'buy',
            'sell',
        ]


class FixedStrategyProfileSerializer(BaseStrategyProfileSerializer):

    class Meta:
        model = FixedStrategyProfile
        fields = [
            'id',
            'type_name',
            'description',
            'created',
            'buy',
            'sell',
        ]


MAPPING = {
    serializer_class.Meta.model: serializer_class
    for serializer_class in locals().values()
    if (isinstance(serializer_class, type)
        and issubclass(serializer_class, ModelSerializer)
        and hasattr(serializer_class, 'Meta')
        and getattr(serializer_class.Meta, 'model', None))
}

