from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.contrib.auth import authenticate
from ..qx_rest.exceptions import SerializerFieldError
from ..settings import base_settings
from .tools import CodeMsg


User = get_user_model()


class SendCodeSerializer(serializers.Serializer):
    send_type = serializers.ChoiceField(
        ['mobile', 'email'], label="发送类型")
    mobile = serializers.CharField(
        label="手机号", max_length=20, required=False)
    email = serializers.CharField(
        label="邮箱", max_length=50, required=False)
    type = serializers.ChoiceField(
        ["default", "signup", "changepwd", ], label="类型")

    def create(self, validated_data):
        send_type = validated_data['send_type']
        if send_type == 'mobile':
            send_cls = base_settings.SEND_MOBILE_MSG_CLASS
        elif send_type == 'email':
            send_cls = base_settings.SEND_EMAIL_MSG_CLASS
        else:
            raise SerializerFieldError(
                '类型错误', field='send_type')
        mobile, email, uid = None, None, None
        if validated_data['type'] == 'default':
            if user := self.context['user'].user:
                uid = user.id
                mobile = user.mobile
                email = user.email
            else:
                raise serializers.ValidationError('请登录后发送')
        elif validated_data['type'] == 'signup':
            mobile = validated_data.pop('mobile', None)
            email = validated_data.pop('email', None)
        elif validated_data['type'] == 'changepwd':
            mobile = validated_data.pop('mobile', None)
            email = validated_data.pop('email', None)
        if not email or not mobile:
            raise serializers.ValidationError('email or mobile error')
        is_send, code = CodeMsg(uid, email, mobile).get_code()
        if is_send:
            raise serializers.ValidationError('5分钟后才能再次发送')
        if email:
            send_cls().send(email, code)
        elif mobile:
            send_cls().send(mobile, code)
        return {}


class SignupSerializer(serializers.Serializer):

    mobile = serializers.CharField(
        label="手机号", max_length=20, required=False)
    email = serializers.CharField(
        label="邮箱", max_length=50, required=False)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)

    def create(self, validated_data):
        pass

    class Meta:
        model = User


class SigninSerializer(serializers.Serializer):

    account = serializers.CharField(
        label="账号", max_length=50,)
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


class UpdateMobileSerializer(serializers.ModelSerializer):

    mobile = serializers.CharField(
        label="手机号", max_length=20)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)

    def update(self, instance, validated_data):
        code = validated_data.pop('code', None)
        mobile = validated_data['mobile']
        _code = CodeMsg(None, None, mobile).get_code()
        if code != _code:
            raise SerializerFieldError(
                '验证码错误', field='code')
        if instance.mobile == instance.account:
            validated_data['account'] = mobile

        instance = super().update(instance, validated_data)
        return instance

    class Meta:
        model = User
        fields = ('mobile', 'code',)


class UpdateEmailSerializer(serializers.ModelSerializer):

    email = serializers.CharField(
        label="邮箱", max_length=50)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)

    def update(self, instance, validated_data):
        code = validated_data.pop('code', None)
        email = validated_data['email']
        _code = CodeMsg(None, email, None).get_code()
        if code != _code:
            raise SerializerFieldError(
                '验证码错误', field='code')
        if instance.email == instance.account:
            validated_data['account'] = email
        instance = super().update(instance, validated_data)
        return instance

    class Meta:
        model = User
        fields = ('email', 'code',)

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
