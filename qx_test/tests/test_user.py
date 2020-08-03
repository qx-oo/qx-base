import pytest
import json
from qx_base.qx_user.viewsets import UserViewSet, UserInfoViewSet
from qx_base.qx_user.tools import CodeMsg


class TestUserViewSet:

    def setup_class(self):
        self.url = "/api/tests/"
        self.viewset = UserViewSet

    def test_send_code(self, rf, signin_request):
        url = '{}/user/send-code/'.format(self.url)

        data = {
            'send_type': 'mobile',
            'type': 'changepwd',
            'mobile': '13344335544',
        }
        request = signin_request(url, "post", data=data)
        response = self.viewset.as_view({'post': 'send_code'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['code'] == 200

    @pytest.mark.django_db
    def test_signin(self, rf, user_data_init):
        url = '{}/user/signin/'.format(self.url)

        data = {
            "account": "18866668888",
            "password": "12345678"
        }
        request = rf.post(
            url, data=data,
            content_type='application/json')
        response = self.viewset.as_view({'post': 'signin'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['data']['token']

        _, code = CodeMsg(None, None, '18866668888',
                          _type='signin').get_new_code()
        data = {
            "account": "18866668888",
            "code": code
        }
        request = rf.post(
            url, data=data,
            content_type='application/json')
        response = self.viewset.as_view({'post': 'signin'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['data']['token']

    @pytest.mark.django_db
    def test_signup(self, rf, user_data_init):
        mobile = '18866668800'
        _, code = CodeMsg(None, None, mobile,
                          _type='signup').get_new_code()

        url = '{}/user/signup/'.format(self.url)

        data = {
            "mobile": mobile,
            "password": "12345678",
            "code": code,
            "userinfo": {
                "name": "test_user",
                "age": 15,
            }
        }
        request = rf.post(
            url, data=data,
            content_type='application/json')
        response = self.viewset.as_view({'post': 'signup'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['data']['token']


class TestUserInfoViewSet:

    def setup_class(self):
        self.url = "/api/tests/"
        self.viewset = UserInfoViewSet

    @pytest.mark.django_db
    def test_userinfo(self, rf, user_data_init, signin_request):

        url = '{}/user/userinfo/'.format(self.url)

        request = signin_request(url, "get")
        response = self.viewset.as_view({'get': 'list'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['code'] == 200

    @pytest.mark.django_db
    def test_userinfo_update(self, user_data_init, signin_request):

        url = '{}/user/userinfo/'.format(self.url)

        data = {
            "name": "test_update_name",
            "age": 100,
        }

        request = signin_request(url, "put", data=data)
        response = self.viewset.as_view({'put': 'update'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['code'] == 200
