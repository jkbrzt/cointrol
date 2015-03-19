"""
Custom colleciton pagination

"""
from collections import OrderedDict
from rest_framework import pagination
from rest_framework.response import Response


class CointrolPagination(pagination.LimitOffsetPagination):

    default_limit = 50

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('meta', {
                'next': self.get_next_link(),
            }),
            ('page', data),
        ]))

