"""
Custom model fields.

"""
from django.db import models


class PriceField(models.DecimalField):
    def __init__(self, max_digits=30, decimal_places=2, default=0, **kwargs):
        super().__init__(max_digits=max_digits,
                         decimal_places=decimal_places,
                         default=default,
                         **kwargs)


class AmountField(models.DecimalField):
    def __init__(self, max_digits=30, decimal_places=8, default=0, **kwargs):
        super().__init__(max_digits=max_digits,
                         decimal_places=decimal_places,
                         default=default,
                         **kwargs)


class PercentField(models.DecimalField):

    def __init__(self, max_digits=6, decimal_places=3, **kwargs):
        super().__init__(max_digits=max_digits,
                         decimal_places=decimal_places,
                         **kwargs)
