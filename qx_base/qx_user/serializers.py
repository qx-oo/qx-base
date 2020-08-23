from rest_framework import serializers, exceptions
from django.db.models import Q
from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from ..qx_rest.exceptions import SerializerFieldError
from ..qx_core.tools import DictInstance
from ..settings import base_settings
from .tools import CodeMsg, generate_random_account
# from .models import _UserInfo as UserInfo


User = get_user_model()


# class UserInfoSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = UserInfo
#         fields = ('id', 'name',)


class SendCodeSerializer(serializers.Serializer):
    send_type = serializers.ChoiceField(
        ['mobile', 'email'], label="发送类型")
    mobile = serializers.CharField(
        label="手机号", max_length=20, required=False)
    email = serializers.CharField(
        label="邮箱", max_length=50, required=False)
    type = serializers.ChoiceField(
        ["default", "signup", "signin", "changepwd", ], label="类型")

    def create(self, validated_data):
        _type = validated_data['type']
        if _type in ['default', 'changepwd']:
            if not self.context['request'].user.is_authenticated:
                raise exceptions.AuthenticationFailed("认证失败")

        send_type = validated_data['send_type']
        if send_type == 'mobile':
            send_cls = base_settings.SEND_MOBILE_MSG_CLASS
        elif send_type == 'email':
            send_cls = base_settings.SEND_EMAIL_MSG_CLASS
        else:
            raise SerializerFieldError(
                '类型错误', field='send_type')

        mobile, email, uid = None, None, None
        if _type == 'default':
            # TODO:
            # if user := self.context['request'].user:
            user = self.context['request'].user
            if user:
                uid = user.id
                mobile = user.mobile
                email = user.email
            else:
                raise serializers.ValidationError('请登录后发送')
        elif _type in ['signup', 'signin']:
            mobile = validated_data.pop('mobile', None)
            if mobile and User.objects.filter(mobile=mobile).exists():
                raise serializers.ValidationError('手机号已注册')
            email = validated_data.pop('email', None)
            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError('邮箱已注册')
        elif _type == 'changepwd':
            mobile = validated_data.pop('mobile', None)
            email = validated_data.pop('email', None)
        if not email and not mobile:
            raise serializers.ValidationError('email or mobile error')

        object_id = mobile if send_type == 'mobile' else email
        object_id = uid or object_id

        c_ins = CodeMsg(object_id, _type=_type)
        is_send, code = c_ins.get_new_code()
        if is_send:
            raise serializers.ValidationError('5分钟后才能再次发送')
        try:
            if email:
                send_cls().send_msg(email, code)
            elif mobile:
                send_cls().send_msg(mobile, code)
        except Exception:
            c_ins.del_code()
        return DictInstance(**validated_data)


class SignupSerializer(serializers.Serializer):

    account = serializers.CharField(
        label="账号", max_length=20, required=False,)
    mobile = serializers.CharField(
        label="手机号", max_length=20, required=False)
    email = serializers.CharField(
        label="邮箱", max_length=50, required=False)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)
    password = serializers.CharField(
        label="密码", max_length=50, required=False, write_only=True)
    userinfo = base_settings.USERINFO_SERIALIZER_CLASS(
        label="用户信息")
    token = serializers.SerializerMethodField(
        label="token")

    def get_token(self, instance):
        return instance.get_new_token()

    def _create_user(self, account, mobile, email, password, userinfo):
        instance = User.objects.create_user(account, mobile, email, password)
        # userinfo
        serializer = base_settings.USERINFO_SERIALIZER_CLASS(data=userinfo)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=instance)
        return instance

    def _check_user_exists(self, email, mobile, account):
        if email:
            if User.objects.filter(email=email).exists():
                raise SerializerFieldError(
                    '用户已存在', field='email')
        if mobile:
            if User.objects.filter(mobile=mobile).exists():
                raise SerializerFieldError(
                    '用户已存在', field='mobile')
        if account:
            if User.objects.filter(account=account).exists():
                raise SerializerFieldError(
                    '用户已存在', field='account')

    def create(self, validated_data):
        code = validated_data.pop('code', None)
        account = validated_data.pop('account', None)
        mobile = validated_data.pop('mobile', None)
        email = validated_data.pop('email', None)
        password = validated_data.pop('password', None)
        userinfo = validated_data.pop('userinfo', None)
        if not email and not mobile:
            raise serializers.ValidationError('email and mobile empty')

        self._check_user_exists(email, mobile, account)

        if not account:
            account = generate_random_account()

        object_id = email or mobile
        _code = CodeMsg(
            object_id, _type='signup').get_code()
        if code != _code:
            raise SerializerFieldError(
                '验证码错误', field='code')

        # creaste user
        with transaction.atomic():
            instance = self._create_user(
                account, mobile, email, password, userinfo)
        return instance

    class Meta:
        model = User


class SigninSerializer(serializers.Serializer):

    account = serializers.CharField(
        label="账号", max_length=50, required=False)
    mobile = serializers.CharField(
        label="手机号", max_length=20, required=False)
    email = serializers.CharField(
        label="邮箱", max_length=50, required=False)
    password = serializers.CharField(
        label="密码", max_length=50, required=False, write_only=True)
    code = serializers.CharField(
        label="验证码", max_length=10, required=False, write_only=True)
    token = serializers.SerializerMethodField(
        label="token")

    def get_token(self, instance):
        return instance.get_new_token()

    def create(self, validated_data):
        account = validated_data.get('account')
        mobile = validated_data.get('mobile')
        email = validated_data.get('email')
        password = validated_data.get('password')
        code = validated_data.get('code')

        if not account and not mobile and not email:
            raise SerializerFieldError(
                '账号不能为空', field='account')

        if not password and not code:
            raise SerializerFieldError(
                '密码不能为空', field='password')

        user, field = User.query_user(account, mobile, email)
        if not user:
            raise SerializerFieldError(
                '用户不存在', field=field)

        if password:
            auth_user = authenticate(account=user.account, password=password)
            if not auth_user:
                raise SerializerFieldError(
                    '密码错误', field='password')
        elif code:
            mobile, email = None, None
            if account == user.mobile:
                mobile = account
            elif account == user.email:
                email = account
            else:
                raise serializers.Serializer('发送类型错误')
            object_id = email or mobile
            c_ins = CodeMsg(object_id, _type='signin')
            _code = c_ins.get_code()

            if _code != code:
                raise SerializerFieldError(
                    '验证码错误', field='code')
        else:
            raise SerializerFieldError(
                '未知错误', field='password')
        return user

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
        _code = CodeMsg(
            mobile, _type='default').get_code()
        if code != _code:
            raise SerializerFieldError(
                '验证码错误', field='code')
        if instance.mobile == instance.account:
            validated_data['account'] = mobile

        instance = super().update(instance, validated_data)
        instance.clear_cache()
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
        _code = CodeMsg(email, _type='default').get_code()
        if code != _code:
            raise SerializerFieldError(
                '验证码错误', field='code')
        if instance.email == instance.account:
            validated_data['account'] = email
        instance = super().update(instance, validated_data)
        instance.clear_cache()
        return instance

    class Meta:
        model = User
        fields = ('email', 'code',)


class AccountExistSerializer(serializers.Serializer):

    exists = serializers.BooleanField(label="是否存在")
