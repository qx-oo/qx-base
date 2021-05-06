# qx-base
my django project basic module

### Install:

    $ pip install -e git://github.com/qx-oo/qx-base.git@master#egg=qx-base

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
        'USERINFO_MODEL': "user.UserInfo",
        'USERINFO_SERIALIZER_CLASS': "qx_test.user.serializers.UserinfoSerializer",
        'JWT_EXPIRED_DAYS': '60',
    }

    # Verify Code Continue
    VERIFY_CODE_CHECK = False

User models.py:

    from django.contrib.auth.models import AbstractBaseUser
    from qx_base.qx_user.models import QxUser, QxUser_Meta, QxUserInfo


    class User(AbstractBaseUser, QxUser):

        Meta = QxUser_Meta

    class UserInfo(QxUserInfo):
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


Celery:

    QX_BASE_SETTINGS = {
        'USERLASTACCESS_CLASS': "qx_base.qx_user.tools.UserLastAccessTime",
    }

    CELERY_TASK_ROUTES = {
        # async cache clean
        "qx_base.qx_rest.tasks.AsyncClearCacheTask": {}
        # User access time update to db
        "qx_base.qx_user.tasks.UserAccessTimeTask": {}
    }
    CELERY_BEAT_SCHEDULE = {
        'UserAccessTimeTask': {
            'task': "qx_base.qx_user.tasks.UserAccessTimeTask",
            'schedule': crontab(hour=23, minute=59, day_of_week="*"),
        }
    }


asgi wb auth:

    from qx_base.qx_user.auth import AioJWTAuthMiddlewareStack

    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AioJWTAuthMiddlewareStack(
            URLRouter(
                wb_views,
            )
        ),
    })


### Mac OS:

gmp:

    $ brew install gmp
    $ export "CFLAGS=-I/usr/local/include -L/usr/local/Cellar/gmp/6.2.0/lib"

pscopg2:

    $ env LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pip install psycopg2==2.8.3

### Signature Keys

    $ openssl genrsa -out rsa_pri_key.pem 1024
    $ openssl rsa -in rsa_pri_key.pem -pubout -out rsa_pub_key.pem