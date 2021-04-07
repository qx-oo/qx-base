import pytest
import json
import django
from qx_base.qx_user.viewsets import UserViewSet, UserInfoViewSet
from qx_base.qx_user.tools import CodeMsg
from qx_test.user.models import User, Baby, TGroup, GPermission
from qx_test.user.views import TGroupViewset


class TestUserModel:

    @pytest.mark.django_db
    def test_user_unique(self):
        User.objects.create(
            account='123456',
            mobile="123456",
            email=None,
        )
        User.objects.create(
            account='123457',
            mobile="123457",
            email=None,
        )
        User.objects.create(
            account='123459',
            mobile=None,
            email='123456',
        )
        User.objects.create(
            account='123460',
            mobile=None,
            email=None,
        )
        User.objects.create(
            account='123461',
            mobile=None,
            email=None,
        )
        try:
            User.objects.create(
                account='123458',
                mobile="123456",
                email=None,
            )
            assert False
        except django.db.IntegrityError:
            assert True


class TestUserViewSet:

    def setup_class(self):
        self.url = "/api/tests/"
        self.viewset = UserViewSet

    def test_send_verify_code(self, rf, signin_request):
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
            "mobile": "18866668888",
            "password": "12345678"
        }
        request = rf.post(
            url, data=data,
            content_type='application/json')
        response = self.viewset.as_view({'post': 'signin'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['data']['token']

        _, code = CodeMsg('18866668888',
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
        _, code = CodeMsg(mobile,
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

    @pytest.mark.django_db
    def test_account_exists(self, rf, user_data_init):

        url = '{}/user/account-exists/?account={}'.format(
            self.url, '18866668880')

        request = rf.get(url)
        response = self.viewset.as_view({'get': 'account_exists'})(request)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['data']['exists']


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


class TestBaby:

    @pytest.mark.django_db
    def test_model(self, user_data_init):
        user1 = User.objects.get(account='18866668881')
        user2 = User.objects.get(account='18866668882')
        user3 = User.objects.get(account='18866668883')
        baby = Baby.objects.create(name='test1', type="user",
                                   object_id=user1.id, user_id=user1.id,)
        Baby.objects.create(name='test2', type="user",
                            object_id=user2.id, user_id=user2.id,)
        Baby.objects.create(name='test3', type="user",
                            object_id=user3.id, user_id=0,)
        Baby.objects.create(name='test4', type="test",
                            object_id=None, user_id=user1.id,)

        queryset = Baby.objects.all()
        queryset = Baby.prefetch_type_object(queryset)
        queryset = Baby.load_user(queryset)
        assert hasattr(queryset[0], 'type_object')
        c_baby = Baby.cache_get(id=baby.id)
        assert c_baby == baby
        try:
            c2_baby = Baby.cache_get(id=baby.id, user_id=3)
        except Baby.DoesNotExist:
            assert True
        else:
            assert False
        c2_baby = Baby.cache_get(id=baby.id, user_id=2)
        assert c2_baby == baby


class TestRefView:

    def setup_class(self):
        self.url = "/api/tests"
        self.viewset = TGroupViewset

    @pytest.mark.django_db
    def test_ref(self, rf, user_data_init, signin_request):

        groups = []
        perms = []
        for i in range(5):
            groups.append(TGroup.objects.create(name=str(i + 1)))
            perms.append(GPermission.objects.create(name=str(i + 1)))

        g1 = groups[0]

        id_query = {self.viewset.lookup_field: g1.id}
        url = '{}/tgroup/{}/ref/'.format(self.url, g1.id)

        data = {
            'ids': [p.id for p in perms[:3]]
        }

        request = rf.post(
            url, data=data,
            content_type='application/json')
        response = self.viewset.as_view(
            {'post': 'ref_create'})(request, **id_query)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['code'] == 200

        ids = [str(p.id) for p in perms[1:3]]
        url = '{}?ids={}'.format(url, ','.join(ids))
        request = rf.delete(url)
        response = self.viewset.as_view(
            {'delete': 'ref_destroy'})(request, **id_query)

        g1 = TGroup.objects.get(id=g1.id)
        assert g1.perms.all()[0].id == perms[0].id
