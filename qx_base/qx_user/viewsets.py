from rest_framework import viewsets, decorators
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, BasePermission,
)
# from ..qx_core.storage import ProxyCache
from ..qx_rest import mixins
from ..qx_rest.response import ApiResponse
from .serializers import (
    User,
    UserInfo,
    SigninSerializer,
    SignupSerializer,
    SendCodeSerializer,
    UpdateMobileSerializer,
    UpdateEmailSerializer,
    UserInfoSerializer,
)

# Create your views here.


class UserPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['signin', 'signup', 'send_code']:
            return AllowAny().has_permission(request, view)
        return IsAuthenticated().has_permission(request, view)


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


class UserInfoViewSet(viewsets.GenericViewSet,
                      mixins.ListModelMixin,
                      mixins.PutModelMixin,
                      mixins.UserFilterMixin,):

    '''
    用户信息
    ---
    list:
        获取用户信息

        获取用户信息

    '''
    permission_classes = (
        UserPermission,
    )
    queryset = UserInfo.objects.all() if UserInfo else None

    serializer_class = UserInfoSerializer
