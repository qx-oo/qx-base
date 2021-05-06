import jwt
import logging
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.db import close_old_connections
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.auth import AuthMiddlewareStack
from rest_framework_jwt.settings import api_settings
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.authentication import (
    BaseAuthentication,
)
from ..qx_rest.exceptions import (
    AuthenticationExpired,
    UserDisabled,
)
from ..qx_core.storage.caches import ProxyCache
from ..qx_core.storage.redis import OriginAioRedisClient
from .tools import UserLastAccessTime


logger = logging.getLogger(__name__)


AUTH_TOKEN_CACHE_KEY = "user:userinstance:{}"
AUTH_TOKEN_CACHE_TIME = 60 * 60 * 24 * 30


def get_authorization_header(request, header_name="HTTP_MYAUTHORIZATION"):
    """
    Return request's 'Authorization:' header, as a bytestring.
    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get(header_name, b'')
    if isinstance(auth, str):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


def get_token_by_request(request, header_name="HTTP_MYAUTHORIZATION") -> str:
    """
    """
    auth = get_authorization_header(request, header_name).split()
    if not auth or \
            auth[0].lower() != settings.JWT_TOKEN_KEYWORD.lower().encode():
        return None
    if len(auth) == 1 or len(auth) > 2:
        return None
    try:
        token = auth[1].decode()
    except UnicodeError:
        return None
    return token


class UserJWT():
    """
    User jwt encode and decode
    """

    @staticmethod
    def encode(user) -> str:
        UserModel = get_user_model()
        try:
            userinfo = user.get_jwt_userinfo()
        except UserModel.userinfo.RelatedObjectDoesNotExist:
            raise exceptions.AuthenticationFailed("用户不存在")
        return api_settings.JWT_ENCODE_HANDLER(userinfo)

    @staticmethod
    def decode(token) -> dict:
        return api_settings.JWT_DECODE_HANDLER(token)


class JwtAuthentication(BaseAuthentication):

    def authenticate(self, request):
        token = get_token_by_request(request)
        if not token:
            return None
        if hasattr(request, '_resource_user'):
            return (request._resource_user, token)
        return self.authenticate_credentials(token, request=request)

    def _verify_expire(self, timestamp):
        created = timezone.datetime.fromtimestamp(timestamp, tz=timezone.utc)
        if (timezone.now() - timezone.timedelta(
                days=settings.QX_BASE_SETTINGS.get('JWT_EXPIRED_DAYS', 90)
        )) > created:
            raise AuthenticationExpired()

    def authenticate_credentials(self, key, request=None):
        UserModel = get_user_model()
        try:
            userinfo = UserJWT.decode(key)
            if not userinfo.get("user_id"):
                raise exceptions.AuthenticationFailed("认证失败")
            self._verify_expire(userinfo['timestamp'])
            user_id = userinfo['user_id']
            proxy = ProxyCache(
                AUTH_TOKEN_CACHE_KEY, AUTH_TOKEN_CACHE_TIME,
                args=[user_id], convert='object')
            user = proxy.get()
            if user:
                if request:
                    # 设置用户最近访问时间
                    try:
                        UserLastAccessTime().update_access_time(
                            user_id, user_id)
                    except Exception:
                        logger.exception("UserLastAccessTime")
                return user, key
            user = UserModel.objects.get(id=userinfo['user_id'])
            if not user.is_active:
                raise UserDisabled()
            if user:
                proxy.set(user)
            return user, key
        except (jwt.DecodeError, TypeError, UnicodeDecodeError,
                jwt.InvalidAlgorithmError, KeyError):
            raise exceptions.AuthenticationFailed("token错误")
        except UserModel.DoesNotExist:
            raise exceptions.AuthenticationFailed("用户不存在")

    def authenticate_header(self, request):
        return settings.JWT_TOKEN_KEYWORD


class AioJWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        close_old_connections()
        try:
            if(jwt_token_list := parse_qs(
                    scope["query_string"].decode("utf8")).get('token', None)):
                jwt_token = jwt_token_list[0]
                userinfo = UserJWT.decode(jwt_token)

                if not userinfo.get("user_id"):
                    raise KeyError
                user_id = userinfo['user_id']

                client = await OriginAioRedisClient().get_conn()
                key = AUTH_TOKEN_CACHE_KEY.format(user_id)
                _data = client.get(key)
                user = ProxyCache.loads(_data, convert='object')

                if user:
                    scope['user'] = user
                else:
                    user = await self.get_user(user_id)
                    if user:
                        if not user.is_active:
                            user = AnonymousUser()
                    scope['user'] = user
            else:
                scope['user'] = AnonymousUser()
        except (jwt.DecodeError, TypeError, UnicodeDecodeError,
                jwt.InvalidAlgorithmError, KeyError):
            scope['user'] = AnonymousUser()
        return await self.app(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return AnonymousUser()


def AioJWTAuthMiddlewareStack(app):
    return AioJWTAuthMiddleware(AuthMiddlewareStack(app))
