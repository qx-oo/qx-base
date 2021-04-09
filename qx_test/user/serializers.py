from rest_framework import serializers
from .models import UserInfo, Baby


class UserinfoSerializer(serializers.ModelSerializer):

    mobile = serializers.CharField(
        label='手机号', read_only=True, source="user.mobile")

    class Meta:
        model = UserInfo
        fields = ('user_id', 'mobile', 'name', 'age',)
        read_only_fields = ('user_id',)


class BabySerializer(serializers.ModelSerializer):

    class Meta:
        model = Baby
        fields = ('id', 'user_id', 'name',)
