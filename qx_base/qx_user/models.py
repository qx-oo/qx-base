import time
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from ..qx_core.models import AbstractBaseModel
from .auth import UserJWT


class UserManager(BaseUserManager):
    """
    User Manager
    """

    def _create_user(self, mobile: str, email: str, password: str,
                     is_staff: bool, is_superuser: bool,
                     **extra_fields) -> "User":
        """
        create user by and mobile
        """
        if not mobile and not email:
            raise ValueError('mobile or email is null')
        account = mobile or email
        user = self.model(mobile=mobile,
                          account=account,
                          is_active=True,
                          is_staff=is_staff,
                          is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, mobile: str, email: str, password: str = None,
                    **extra_fields) -> "User":
        return self._create_user(mobile, email, password, False, False,
                                 **extra_fields)

    def create_superuser(self, account: str, password: str,
                         **extra_fields) -> "User":
        return self._create_user(account, None, password, True, True,
                                 **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, AbstractBaseModel):
    """
    User base info
    """

    account = models.CharField(
        verbose_name='账号', max_length=255, unique=True, db_index=True)
    mobile = models.CharField(
        max_length=25, null=True, blank=True,
        verbose_name="手机号", db_index=True)
    email = models.EmailField(
        verbose_name="Email", null=True, blank=True,
        db_index=True)
    is_active = models.BooleanField(
        verbose_name="Active", default=True)
    is_staff = models.BooleanField(
        verbose_name="Is Staff", default=False)
    last_access_time = models.DateTimeField(
        verbose_name='最近访问时间', default=timezone.now)
    created = models.DateTimeField(
        verbose_name='创建时间', default=timezone.now, editable=False)

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

    def __str__(self):
        return self.account

    class Meta:
        abstract = True
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        swappable = 'AUTH_USER_MODEL'
        unique_together = (('mobile', 'email',),)


class UserInfo(AbstractBaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, primary_key=True,
        verbose_name="用户")

    def get_userinfo(self):
        raise NotImplementedError()

    class Meta:
        abstract = True
        verbose_name = '用户信息'
        verbose_name_plural = verbose_name
