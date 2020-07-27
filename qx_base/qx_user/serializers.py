from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth import authenticate
from ..qx_rest.exceptions import SerializerFieldError


User = get_user_model()


class SendCodeSerializer(serializers.Serializer):
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)
    type = serializers.ChoiceField([(
        ("mobile", "手机"),
        ("email", "邮箱"),
    )], label="类型")

    def create(self, validated_data):
        # TODO: send mobile code msg
        pass


class SignupSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        label="手机号", max_length=20, required=False)
    email = serializers.CharField(
        label="邮箱", max_length=100, required=False)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)

    def create(self, validated_data):
        pass

    class Meta:
        model = User


class SigninSerializer(serializers.Serializer):

    account = serializers.CharField(
        label="账号", max_length=100,)
    password = serializers.CharField(
        label="密码", max_length=50, required=False, write_only=True)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)
    token = serializers.SerializerMethodField(
        label="token")

    def get_token(self, instance):
        return instance.get_new_token()

    def create(self, validated_data):
        account = validated_data['account']
        password = validated_data.get('password')
        code = validated_data.get('code')

        if not password and not code:
            raise SerializerFieldError(
                '密码不能为空', field='password')

        user = User.objects.filter(
            Q(mobile=account) | Q(email=account)).first()
        if not user:
            raise SerializerFieldError(
                '用户不存在', field='account')
        if password:
            auth_user = authenticate(account=user.account, password=password)
            if not auth_user:
                raise SerializerFieldError(
                    '密码错误', field='password')
            return auth_user
        elif code:
            raise SerializerFieldError(
                '验证码错误', field='code')
        else:
            raise SerializerFieldError(
                '未知错误', field='password')

    class Meta:
        model = User


# class UserInfoSerializer(serializers.ModelSerializer):

#     nick_name = serializers.CharField(
#         label='用户昵称', source="userinfo.nick_name", max_length=25)

#     class Meta:
#         model = User
#         fields = ('mobile', 'email', 'nick_name')


# class UpdateUserSerializer(serializers.Serializer):

#     class Meta:
#         model = UserInfo
#         fields = ('nick_name',)
