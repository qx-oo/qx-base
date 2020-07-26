import logging
from django.http import JsonResponse


logger = logging.getLogger(__name__)


class SignErrJsonResponse(JsonResponse):
    def __init__(self):
        results = {
            'code': 4002,
            'msg': ['signature is error']
        }
        self._results = results
        super().__init__(data=results, status=400)


class SecurityErrResponse(JsonResponse):
    def __init__(self):
        data = {
            'code': 4006,
            'msg': ['Content is illegal']
        }
        super().__init__(data=data, status=400)


class ApiNotFoundResponse(JsonResponse):
    def __init__(self):
        results = {
            'code': 4004,
            'msg': ['Not Found']
        }
        self._results = results
        super().__init__(data=results, status=404)


class ApiResponse(JsonResponse):
    def __init__(self, data: dict):
        results = {
            "code": 200,
            "msg": ["success"],
            "data": data
        }
        self._results = results
        super().__init__(data=results, status=200)


class ApiErrorResponse(JsonResponse):
    def __init__(self, msg: str, code: int = 4000):
        if isinstance(msg, str):
            msg = [msg]
        results = {
            "code": code,
            "msg": msg
        }
        self._results = results
        super().__init__(data=results, status=200)


class ApiDetailErrorResponse(JsonResponse):
    def __init__(self, msg: str, code: int = 4007, fields=[]):
        if isinstance(msg, str):
            msg = [msg]
        results = {
            "code": code,
            "msg": msg,
            "detail": {
                "fields": fields,
            },
        }
        self._results = results
        super().__init__(data=results, status=200)


class AuthenticationFailedResponse(JsonResponse):
    def __init__(self, msg):
        if isinstance(msg, str):
            msg = [msg]
        results = {
            "code": 4001,
            "msg": msg,
        }
        self._results = results
        super().__init__(data=results, status=401)


class Api500ErrorResponse(JsonResponse):
    def __init__(self):
        results = {
            "code": 5000,
            "msg": ["error request"]
        }
        self._results = results
        super().__init__(data=results, status=500)
