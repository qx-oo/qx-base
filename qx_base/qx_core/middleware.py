import re
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .signature import ApiSignature
from .tools import param_sort
from ..qx_rest.response import (
    SignErrJsonResponse, ApiErrorResponse,
    Api500ErrorResponse,
)

logger = logging.getLogger(__name__)


class SignatureCheckMiddleware(MiddlewareMixin):
    '''
    Api Signature check
    '''

    def process_request(self, request):  # noqa
        p = re.compile(r'/api/.*')
        # 临时排除
        if request.user.is_authenticated or\
                request.META.get('HTTP_MYAUTHORIZATION') or\
                request.META.get('HTTP_MYANONYMOUS'):
            pass
        elif request.path in settings.IGNORE_CHECK_SIGN_PATH:
            pass
        elif p.match(request.path) and not settings.DEBUG:
            signature = request.META.get('HTTP_SIGN')
            if signature:
                if request.method in ['GET', 'DELETE']:
                    query_string = request.META['QUERY_STRING']
                    json_str = param_sort(
                        query_string, pop_keys=[])
                else:
                    if request.method == 'POST' and\
                            request.content_type == "multipart/form-data":
                        json_str = param_sort(
                            request.POST.dict(), pop_keys=['file'])
                    else:
                        try:
                            body = request.body.decode()
                        except Exception:
                            return ApiErrorResponse("param error")
                        json_str = param_sort(
                            body, _json=True)
                try:
                    if not ApiSignature().verify(signature, json_str):
                        return SignErrJsonResponse()
                except Exception as ex:
                    logger.error(ex, exc_info=True)
                    return SignErrJsonResponse()
            elif not signature:
                return SignErrJsonResponse()


class ErrorLogMiddleware(MiddlewareMixin):
    '''
    api error print to log
    '''

    def __call__(self, request):
        ret = super().__call__(request)
        try:
            if ret.status_code >= 500 and \
                    request.content_type in ['application/json', 'text/plain']:
                p = re.compile(r'/api/.*')
                if p.match(request.path):
                    logger.warning("ErrorLog: {}, {}, {}, {}, {}".format(
                        request.headers, request.path, request.method,
                        self._initial_http_body, ret.status_code))
                    return Api500ErrorResponse()
        except Exception:
            logger.exception("ErrorLogMiddleware")
        return ret

    def process_request(self, request):
        if request.content_type in ['application/json', 'text/plain']:
            self._initial_http_body = request.body

    def process_response(self, request, response):  # noqa
        if request.content_type in ['application/json', 'text/plain']:
            p = re.compile(r'/api/.*')
            if p.match(request.path):
                if response.status_code >= 400 and response.status_code < 500:
                    logger.warning("ErrorLog: {}, {}, {}, {}".format(
                        request.path, request.method,
                        self._initial_http_body, response.content))
        return response
