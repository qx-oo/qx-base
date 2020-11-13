from rest_framework import viewsets
from rest_framework.permissions import (
    AllowAny,
)
from qx_base.qx_rest.mixins import (
    RefViewMixin, RefCreateModelMixin, RefDestroyModelMixin
)
from .models import TGroup, GPermission


class TGroupViewset(viewsets.GenericViewSet,
                    RefViewMixin,
                    RefCreateModelMixin,
                    RefDestroyModelMixin):

    permission_classes = (
        AllowAny,
    )
    ref_queryset = GPermission.objects.all()
    ref_field = "perms"
    queryset = TGroup.objects.all()
