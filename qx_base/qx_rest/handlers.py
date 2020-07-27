from django.http import Http404
from django.core.exceptions import PermissionDenied
from rest_framework.views import set_rollback
from rest_framework import exceptions
from .response import (
    ApiNotFoundResponse,
    AuthenticationFailedResponse,
    ApiErrorResponse,
    ApiDetailErrorResponse,
)
from .exceptions import (
    AuthenticationExpired,
    UserDisabled,
    SerializerFieldError,
)


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
