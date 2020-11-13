from django.urls import path, include
# from rest_framework.routers import DefaultRouter
from qx_rest.routes import ResourceRoute
from qx_base.qx_user import viewsets
from .user.views import TGroupViewset


router = ResourceRoute()
router.register('user', viewsets.UserViewSet)
router.register('userinfo', viewsets.UserInfoViewSet)
router.register('tgroup', TGroupViewset)


urlpatterns_api = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('api/tests/', include(urlpatterns_api)),
]
