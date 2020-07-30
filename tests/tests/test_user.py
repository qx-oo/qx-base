import json
from qx_base.qx_user.viewsets import UserViewSet


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
