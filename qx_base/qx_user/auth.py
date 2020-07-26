import jwt
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from rest_framework_jwt.settings import api_settings
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.authentication import (
    BaseAuthentication,
)
from ..qx_rest.exceptions import (
    AuthenticationExpired,
    UserDisabled,
)
from .tools import UserLastAccessTime


logger = logging.getLogger(__name__)


AUTH_TOKEN_CACHE_KEY = "user:userinstance:{}"


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
        if (timezone.now() - timezone.timedelta(days=30)) > created:
            raise AuthenticationExpired()

    def authenticate_credentials(self, key, request=None):
        UserModel = get_user_model()
        try:
            userinfo = UserJWT.decode(key)
            if not userinfo.get("user_id"):
                raise exceptions.AuthenticationFailed("认证失败")
            # TODO: 临时取消超时判断
            # self._verify_expire(userinfo['timestamp'])
            user_id = userinfo['user_id']
            cache_key, ts = AUTH_TOKEN_CACHE_KEY, 60 * 60 * 24 * 30
            cache_key = cache_key.format(user_id)
            user = cache.get(cache_key)
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
                cache.set(cache_key, user, ts)
            return user, key
        except (jwt.DecodeError, TypeError, UnicodeDecodeError,
                jwt.InvalidAlgorithmError, KeyError):
            raise exceptions.AuthenticationFailed("token错误")
        except UserModel.DoesNotExist:
            raise exceptions.AuthenticationFailed("用户不存在")

    def authenticate_header(self, request):
        return settings.JWT_TOKEN_KEYWORD
