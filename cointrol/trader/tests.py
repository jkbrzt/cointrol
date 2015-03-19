from django.db.models import Sum
from cointrol.core.models import Transaction


def test_balance_for_each_transaction():
    print()
    for t in Transaction.objects.order_by('datetime'):
        aggregate = Transaction.objects\
            .filter(datetime__lte=t.datetime)\
            .aggregate(
                usd=Sum('usd'),
                btc=Sum('btc'),
                fee=Sum('fee')
        )
        print('{id: >10} {btc: >18} {usd: >18} {fee: >18} {after_fee}'.format(
            id=t.pk,
            usd=aggregate['usd'],
            btc=aggregate['btc'],
            fee=aggregate['fee'],
            after_fee=aggregate['usd'] - aggregate['fee'],
        ))
        assert aggregate['usd'] >= 0
        assert aggregate['btc'] >= 0
