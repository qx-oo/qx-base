from django.urls import path, include
from rest_framework.routers import DefaultRouter
from qx_base.qx_user import viewsets


router = DefaultRouter()
router.register('user', viewsets.UserViewSet)
router.register('userinfo', viewsets.UserInfoViewSet)


urlpatterns_api = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('api/tests/', include(urlpatterns_api)),
]
