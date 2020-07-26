from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework import status, exceptions
from rest_framework.views import set_rollback
from .response import (
    ApiNotFoundResponse,
    AuthenticationFailedResponse,
    ApiErrorResponse,
    ApiDetailErrorResponse,
)


class ApiError(exceptions.APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, detail: dict, code: int = 0):
        if 299 < code < 599:
            self.status_code = code
        self.detail = detail

    def __str__(self):
        return str(self.detail)

    def get_codes(self):
        return self.detail

    def get_full_details(self):
        return self.detail


class AuthenticationExpired(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'Token过期'
    default_code = 'token_expired'
    api_code = 4003


class UserDisabled(exceptions.APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '用户被禁用'
    default_code = 'user_disable'
    api_code = 4005


class SerializerFieldError(exceptions.APIException):

    api_code = 4007
    field = None

    def __init__(self, detail=None, code=None, field=None):
        super().__init__(detail, code)
        self.field = field


def rest_exception_handler(exc, context):
    """
    Rest exception handler
    """
    if isinstance(exc, Http404):
        return ApiNotFoundResponse()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, exceptions.AuthenticationFailed):
        return AuthenticationFailedResponse(exc.detail)
    elif isinstance(exc, exceptions.NotAuthenticated):
        return AuthenticationFailedResponse(exc.detail)
    elif isinstance(exc, AuthenticationExpired):
        return ApiErrorResponse(exc.detail, exc.api_code)
    elif isinstance(exc, UserDisabled):
        return ApiErrorResponse(exc.detail, exc.api_code)
    elif isinstance(exc, SerializerFieldError):
        return ApiDetailErrorResponse(exc.detail, fields=[exc.field])

    if isinstance(exc, exceptions.APIException):
        if isinstance(exc.detail, list):
            data = exc.detail
        elif isinstance(exc.detail, dict):
            data = []
            for key, msg in exc.detail.items():
                data.append("%s %s" % (key, msg))
        else:
            data = exc.detail

        set_rollback()
        return ApiErrorResponse(data)

    return None
