from rest_framework import viewsets
from rest_framework.permissions import (
    AllowAny,
)
from qx_base.qx_rest.mixins import (
    RefViewMixin, RefCreateModelMixin, RefDestroyModelMixin,
    ListModelMixin, RetrieveModelMixin,
)
from .models import TGroup, GPermission, Baby
from .serializers import BabySerializer


class TGroupViewset(viewsets.GenericViewSet,
                    ListModelMixin,
                    RefViewMixin,
                    RefCreateModelMixin,
                    RefDestroyModelMixin):

    permission_classes = (
        AllowAny,
    )
    ref_queryset = GPermission.objects.all()
    ref_field = "perms"
    queryset = TGroup.objects.all()


class BabyViewset(viewsets.GenericViewSet,
                  ListModelMixin,
                  RetrieveModelMixin,):

    permission_classes = (
        AllowAny,
    )
    queryset = Baby.objects.all()
    filter_fields = ('user_id',)
    serializer_class = BabySerializer

    cache_config = {
        'list': {
            'is_paginate': False,
            'by_user': True,
        },
        'retrieve': {}
    }
