from django.contrib.auth import get_user_model
from rest_framework import viewsets, decorators
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, BasePermission,
)
from ..qx_rest.mixins import (
    PostModelMixin,
)
from ..qx_rest.response import ApiResponse
from .serializers import (
    SigninSerializer,
    SignupSerializer,
    SendCodeSerializer,
    # UserInfoSerializer,
    # UpdateUserSerializer,
)

# Create your views here.


User = get_user_model()


class UserPermission(BasePermission):
    def has_permission(self, request, view):
        if view.action in ['signin', 'signup', ]:
            return AllowAny().has_permission(request, view)
        return IsAuthenticated().has_permission(request, view)


class UserViewSet(viewsets.GenericViewSet,
                  PostModelMixin,):
    '''
    登录注册
    ---
    signup:
        注册用户

        注册用户

    signin:
        登入

        登入

    info:
        用户信息

        用户信息

    update_info:
        更新用户信息

        更新用户信息
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
        # elif self.action == 'info':
        #     return UserInfoSerializer
        # elif self.action == 'update_info':
        #     return UpdateUserSerializer
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

    # def get_queryset(self):
    #     if self.request.user.is_authenticated:
    #         return self.queryset.filter(user=self.request.user)
    #     return self.queryset
