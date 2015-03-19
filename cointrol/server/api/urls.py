"""
API URLs

"""
from rest_framework import routers

from . import views


router = routers.DefaultRouter(trailing_slash=False)
router.register('tickers', views.TickerViewSet, 'ticker')
router.register('balances', views.BalanceViewSet, 'balance')
router.register('orders', views.OrderViewSet, 'order')
router.register('transactions', views.TransactionViewSet, 'transaction')
router.register('sessions', views.TradingSessionViewSet, 'session')


urlpatterns = router.urls
