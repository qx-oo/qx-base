from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from qx_base.qx_user.models import QxUser, QxUser_Meta, QxUserInfo
from qx_base.qx_rest.models import RestCacheModel


class User(AbstractBaseUser, QxUser):
    """
    User Model
    """

    Meta = QxUser_Meta


class UserInfo(QxUserInfo, RestCacheModel):
    """
    User info
    """
    name = models.CharField(
        verbose_name="用户名称", default="",
        max_length=50)

    class Meta:
        verbose_name = 'UserInfo'
        verbose_name_plural = verbose_name
