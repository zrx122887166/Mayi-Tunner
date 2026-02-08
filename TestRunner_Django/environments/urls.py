from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EnvironmentViewSet, EnvironmentVariableViewSet, GlobalRequestHeaderViewSet

router = DefaultRouter()
router.register('environments', EnvironmentViewSet)
router.register('variables', EnvironmentVariableViewSet)
router.register('global-headers', GlobalRequestHeaderViewSet)

app_name = 'environments'

urlpatterns = [
    path('', include(router.urls)),
] 