# qx-base
my django project basic module

### Install:

    pip install -e git://github.com/qx-oo/qx-base.git@master#egg=qx-base

### Usage:

settings.py:

    INSTALLED_APPS = [
        ...
        'qx_base.qx_core',
        'qx_base.qx_rest',
        'qx_base.qx_user',
        ...
    ]

    JWT_TOKEN_KEYWORD = "Token"

    # RestFramework
    REST_FRAMEWORK = {
        ...
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'qx_base.qx_user.auth.JwtAuthentication',
            ...
        ),
        'DEFAULT_PAGINATION_CLASS':
            'qx_base.qx_rest.paginations.Pagination',
        'EXCEPTION_HANDLER': 'qx_base.qx_rest.handlers.rest_exception_handler',
        ...
    }

    # Redis
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_PASSWORD = ""
    REDIS_URL = "redis://:{}@{}:{}".format(
        REDIS_PASSWORD,
        REDIS_HOST,
        REDIS_PORT)

    # ignore check sign url
    IGNORE_CHECK_SIGN_PATH = ['/test/api/test']
    # signature public key and private key
    SIGNATURE_PUBLIC_KEY = """xxxxx"""
    SIGNATURE_PRIVATE_KEY = """xxxxx"""

    QX_BASE_SETTINGS = {
        'SEND_MOBILE_MSG_CLASS': "qx_test.msg.TestMsg",
        'SEND_EMAIL_MSG_CLASS': "qx_test.msg.TestMsg",
        'USERINFO_MODEL_CLASS': "qx_test.user.models.UserInfo",
        'USERINFO_SERIALIZER_CLASS': "qx_test.user.serializers.UserinfoSerializer",
    }

User models.py:

    from django.contrib.auth.models import AbstractBaseUser
    from qx_base.qx_user.models import QxUser, QxUser_Meta, QxUserInfo


    class User(AbstractBaseUser, QxUser):

        Meta = QxUser_Meta

    class UserInfo(QxUserInfo, RestCacheModel):
    name = models.CharField(
        verbose_name="Name", default="", max_length=50)
    age = models.IntegerField(
        verbose_name="Age")

    class Meta:
        verbose_name = 'UserInfo'
        verbose_name_plural = verbose_name

User urls.py

    from django.urls import path, include
    from rest_framework.routers import DefaultRouter
    from qx_base.qx_user import viewsets

    router = DefaultRouter()
    router.register('user', viewsets.UserViewSet)
    router.register('userinfo', viewsets.UserInfoViewSet)

    urlpatterns = [
        path('', include(router.urls)),
    ]


### Mac OS:

    brew install gmp
    export "CFLAGS=-I/usr/local/include -L/usr/local/Cellar/gmp/6.2.0/lib"

### Signature Keys

    openssl genrsa -out rsa_pri_key.pem 1024
    openssl rsa -in rsa_pri_key.pem -pubout -out rsa_pub_key.pem