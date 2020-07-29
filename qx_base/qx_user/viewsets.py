from django.contrib.auth import get_user_model
from rest_framework import viewsets, decorators
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, BasePermission,
)
from ..settings import base_settings
from ..qx_core.storage import ProxyCache
from ..qx_rest.mixins import (
    PostModelMixin,
    PutModelMixin,
    GetOneModelMixin,
    RestCacheNameMixin,
)
from ..qx_rest.response import ApiResponse
from .serializers import (
    SigninSerializer,
    SignupSerializer,
    SendCodeSerializer,
    UpdateMobileSerializer,
    UpdateEmailSerializer,
)

# Create your views here.


User = get_user_model()


class UserPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['signin', 'signup', ]:
            return AllowAny().has_permission(request, view)
        return IsAuthenticated().has_permission(request, view)


class UserViewSet(viewsets.GenericViewSet,
                  PostModelMixin,
                  PutModelMixin,
                  GetOneModelMixin,
                  RestCacheNameMixin,):
    '''
    登录注册
    ---
    signup:
        注册用户

        注册用户

    signin:
        登入

        登入

    send_code:
        发送验证码

        发送验证码

    update_mobile:
        更新手机号

        更新手机号

    update_email:
        更新邮箱

        更新邮箱

    retrieve_info:
        获取用户信息

        获取用户信息
    '''
    permission_classes = (
        UserPermission,
    )
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'signin':
            return SigninSerializer
        elif self.action == 'signup':
            return SignupSerializer
        elif self.action == 'send_code':
            return SendCodeSerializer
        elif self.action == 'update_mobile':
            return UpdateMobileSerializer
        elif self.action == 'update_email':
            return UpdateEmailSerializer
        elif self.action == 'retrieve_info':
            return base_settings.USERINFO_SERIALIZER_CLASS
        return {}

    @decorators.action(methods=['post'], url_path='signup', detail=False)
    def signup(self, request, *args, **kwargs):
        return ApiResponse(data=self._create(request, *args, **kwargs))

    @decorators.action(methods=['post'], url_path='signin', detail=False)
    def signin(self, request, *args, **kwargs):
        return ApiResponse(data=self._create(request, *args, **kwargs))

    @decorators.action(methods=['post'], url_path='send-code', detail=False)
    def send_code(self, request, *args, **kwargs):
        return ApiResponse(data=self._create(request, *args, **kwargs))

    @decorators.action(methods=['put'], url_path='update-mobile', detail=False)
    def update_mobile(self, request, *args, **kwargs):
        instance = request.user
        return ApiResponse(data=self._update(
            request, instance, *args, **kwargs))

    @decorators.action(methods=['put'], url_path='update-email', detail=False)
    def update_email(self, request, *args, **kwargs):
        instance = request.user
        return ApiResponse(data=self._update(
            request, instance, *args, **kwargs))

    @decorators.action(methods=['get'], url_path='info', detail=False)
    def retrieve_info(self, request, *args, **kwargs):
        instance = request.user
        key = self.get_cache_name([instance.id])
        proxy = ProxyCache(key, 60 * 60 * 24 * 15)
        if data := proxy.get():
            return ApiResponse(data=data)
        data = self._get_one(instance)
        if data:
            proxy.set(data)
        return ApiResponse(data=data)

    # def get_queryset(self):
    #     if self.request.user.is_authenticated:
    #         return self.queryset.filter(user=self.request.user)
    #     return self.queryset
