import time
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import (
    BaseUserManager,
    PermissionsMixin,
)
from ..qx_core.models import AbstractBaseModel
from ..qx_rest.models import RestModel
from .auth import UserJWT


class UserManager(BaseUserManager):
    """
    User Manager
    """

    def _create_user(self, account: str, mobile: str, email: str,
                     password: str, is_staff: bool, is_superuser: bool,
                     **extra_fields) -> "QxUser":
        """
        create user by and mobile
        """
        if not mobile and not email:
            raise ValueError('mobile or email is null')
        user = self.model(mobile=mobile,
                          account=account,
                          email=email,
                          is_active=True,
                          is_staff=is_staff,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, account, mobile: str, email: str,
                    password: str = None, **extra_fields) -> "QxUser":
        return self._create_user(account, mobile, email, password, False,
                                 False, **extra_fields)

    def create_superuser(self, account: str, password: str,
                         **extra_fields) -> "QxUser":
        user = self._create_user(account, account, account, password, True,
                                 True, **extra_fields)
        from ..settings import base_settings
        Userinfo = base_settings.USERINFO_MODEL
        _ = Userinfo.objects.get_or_create(
            user=user,)
        return user


class QxUser_Meta:
    verbose_name = '用户'
    verbose_name_plural = verbose_name
    swappable = 'AUTH_USER_MODEL'


class QxUser(PermissionsMixin, AbstractBaseModel):
    """
    User base info
    """

    account = models.CharField(
        verbose_name='账号', max_length=255, unique=True, db_index=True)
    mobile = models.CharField(
        max_length=25, null=True, blank=True,
        verbose_name="手机号", db_index=True, unique=True)
    email = models.EmailField(
        verbose_name="Email", null=True, blank=True,
        db_index=True, unique=True)
    is_active = models.BooleanField(
        verbose_name="Active", default=True)
    is_staff = models.BooleanField(
        verbose_name="Is Staff", default=False)
    last_access_time = models.DateTimeField(
        verbose_name='最近访问时间', default=timezone.now)
    created = models.DateTimeField(
        verbose_name='创建时间', default=timezone.now, editable=False)

    cache_config = {
        "default": {
            "UserInfoViewSet": {
                "actions": [
                    "list",
                ],
                "by_user_field": "user_id",
                "create": False,
            }
        },
    }

    objects = UserManager()

    USERNAME_FIELD = 'account'
    EMAIL_FIELD = 'account'

    def get_jwt_userinfo(self) -> dict:
        return {
            "user_id": self.id,
            "account": self.account,
            "mobile": self.mobile,
            "mobile": self.email,
            "timestamp": int(time.time()),
        }

    def get_new_token(self) -> str:
        token = UserJWT.encode(self)
        return token

    def clear_cache(self):
        self.user.userinfo.clear_cache()

    @classmethod
    def query_user(cls, account, mobile, email):
        if account:
            user = cls.objects.filter(account=account).first()
            return user, 'account'
        elif mobile:
            user = cls.objects.filter(mobile=mobile).first()
            return user, 'mobile'
        elif email:
            user = cls.objects.filter(email=email).first()
            return user, 'email'
        else:
            return None, ''

    def __str__(self):
        return self.account

    class Meta:
        abstract = True


class QxUserInfo(RestModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True,
        verbose_name="用户")

    cache_config = {
        "default": {
            "UserInfoViewSet": {
                "actions": [
                    "list",
                ],
                "by_user_field": "user_id",
                "create": False,
            }
        },
    }

    def clear_cache(self):
        raise NotImplementedError()

    class Meta:
        abstract = True
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
