import pytest
from qx_test.user.models import User, UserInfo
from qx_base.qx_core.storage import RedisClient


@pytest.fixture(scope='session', autouse=True)
@pytest.mark.django_db()
def redis_flushall():
    client = RedisClient().get_conn()
    client.flushall()


@pytest.fixture()
def user_data_init(db):
    for i in range(10):
        user = User.objects.create_user(
            mobile="1886666888%s" % i,
            email=None,
            password="12345678",
        )
        UserInfo.objects.create(
            name="test%s" % i,
            age=i,
            user=user,
        )


@pytest.fixture()
def signin_request(rf, user_data_init):
    """
    带认证信息的request
    """
    user = User.objects.get(mobile="18866668888")
    token = user.get_new_token()

    def _func(url, method='get', data=None):
        request = getattr(rf, method)(
            url, data=data,
            # HTTP_MYAUTHORIZATION="token %s" % token,
            **{"HTTP_MYAUTHORIZATION": "token %s" % token},
            content_type='application/json')
        return request
    return _func
