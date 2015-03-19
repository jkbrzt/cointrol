"""
API views

"""
import logging

from rest_framework import viewsets
from rest_framework import authentication
from rest_framework import permissions
from rest_framework import renderers

import cointrol.utils
from cointrol.core import models
from cointrol.core import serializers
from .pagination import CointrolPagination


class JSONRenderer(renderers.JSONRenderer):
    encoder_class = cointrol.utils.JSONEncoder


log = logging.getLogger(__name__)


class APIViewMixin:

    pagination_class = CointrolPagination
    renderer_classes = [
        JSONRenderer,
        renderers.BrowsableAPIRenderer
    ]

    authentication_classes = [
        authentication.SessionAuthentication,
    ]

    permission_classes = [
        permissions.IsAuthenticated
    ]


class OrderViewSet(APIViewMixin, viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.OrderSerializer

    def get_queryset(self):
        return self.request.user.account.orders.all()


class TransactionViewSet(APIViewMixin, viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.TransactionSerializer

    def get_queryset(self):
        return self.request.user.account.transactions.all()


class TickerViewSet(APIViewMixin, viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.TickerSerializer

    def get_queryset(self):
        return models.Ticker.objects.all()


class BalanceViewSet(APIViewMixin, viewsets.ReadOnlyModelViewSet):

    serializer_class = serializers.BalanceSerializer

    def get_queryset(self):
        return self.request.user.account.balances.all()


class TradingSessionViewSet(APIViewMixin, viewsets.ModelViewSet):

    serializer_class = serializers.TradingSessionSerializer

    def get_queryset(self):
        return self.request.user.account.trading_sessions.all()
