from django.http import Http404
from rest_framework import viewsets, decorators
from rest_framework.permissions import (
    IsAuthenticated,
)
from ..settings import base_settings
from ..qx_rest import mixins
from ..qx_rest.response import ApiResponse
from ..qx_rest.permissions import action_authenticated
from .serializers import (
    User,
    SigninSerializer,
    SignupSerializer,
    SendCodeSerializer,
    UpdateMobileSerializer,
    UpdateEmailSerializer,
    AccountExistSerializer,
    RefreshTokenSerializer,
)

# Create your views here.


UserInfo = base_settings.USERINFO_MODEL
UserInfoSerializer = base_settings.USERINFO_SERIALIZER_CLASS


class UserViewSet(viewsets.GenericViewSet,
                  mixins.PostModelMixin,
                  mixins.PutModelMixin,
                  mixins.GetOneModelMixin,
                  mixins.RestCacheNameMixin,):
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

    refresh_token:
        刷新token

        刷新token

    account_exists:
        账号是否被注册

        账号是否被注册, 参数: account=xxxxx
    '''
    permission_classes = (
        action_authenticated(
            ['signin', 'signup', 'send_code', 'account_exists']
        ),
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
        elif self.action == 'account_exists':
            return AccountExistSerializer
        elif self.action == 'refresh_token':
            return RefreshTokenSerializer
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

    @decorators.action(methods=['put'], url_path='refresh-token', detail=False)
    def refresh_token(self, request, *args, **kwargs):
        instance = request.user
        return ApiResponse(data=self._update(
            request, instance, *args, **kwargs))

    @decorators.action(methods=['get'], url_path='account-exists',
                       detail=False)
    def account_exists(self, request, *args, **kwargs):
        account = request.query_params.get('account')
        exists = False
        if account:
            exists = User.objects.filter(account=account).exists()
        return ApiResponse(data={
            'exists': exists
        })


class UserInfoViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.PutModelMixin,):

    '''
    用户信息
    ---
    list:
        获取用户信息

        获取用户信息

    update:
        更新用户信息

        更新用户信息
    '''
    permission_classes = (
        IsAuthenticated,
    )
    queryset = UserInfo.objects.all() if UserInfo else None
    serializer_class = UserInfoSerializer

    cache_config = {
        'list': {
            'by_user': True,
            'is_paginate': False,
        },
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return self.queryset.filter(user=self.request.user)
        return self.queryset

    def list(self, request, *args, **kwargs):
        data = self._list(request, *args, **kwargs)
        if data:
            data = data['results'][0]
        else:
            raise Http404()
        return ApiResponse(data)

    def update(self, request, *args, **kwargs):
        instance = request.user.userinfo
        return ApiResponse(data=self._update(
            request, instance, *args, **kwargs))
