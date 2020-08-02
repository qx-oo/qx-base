import pytest
import json
from qx_base.qx_user.viewsets import UserViewSet
from qx_base.qx_user.tools import CodeMsg


class TestUserViewSet:

    def setup_class(self):
        self.url = "/api/tests/"
        self.viewset = UserViewSet

    def test_send_code(self, rf, signin_request):
        url = '{}/user/send-code/'.format(self.url)

        data = {
            'send_type': 'mobile',
            'mobile': '18866668888',
            'type': 'signup',
        }
        request = rf.post(
            url, data=data,
            content_type='application/json')
        response = self.viewset.as_view({'post': 'send_code'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['code'] == 200

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
    def test_sign(self, rf, user_data_init):
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
