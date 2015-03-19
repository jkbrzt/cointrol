"""
Custom API exception classes.

"""
from rest_framework.exceptions import APIException
from rest_framework import status


class NotFound(APIException):
    """404 exception that allows for a custom message."""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'Not Found'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class BadRequest(APIException):

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Bad request.'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail
