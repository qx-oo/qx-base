from rest_framework import status, exceptions


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


class ApiParamsError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    api_code = 4000

    def __init__(self, detail: str):
        self.detail = detail


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
