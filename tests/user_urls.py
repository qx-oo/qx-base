from django.urls import path, include
from rest_framework.routers import DefaultRouter
from qx_base.qx_user import viewsets


router = DefaultRouter()
router.register('user', viewsets.UserViewSet)


urlpatterns_api = [
    path('', include(router.urls)),
]

urlpatterns = [
    path('api/1.0/tests/', include(urlpatterns_api)),
]
