from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InterfaceViewSet, InterfaceResultViewSet

router = DefaultRouter()
router.register('', InterfaceViewSet, basename='interface')
router.register('results', InterfaceResultViewSet, basename='interface-result')

urlpatterns = [
    path('', include(router.urls)),
] 