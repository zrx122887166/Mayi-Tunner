from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomFunctionViewSet

router = DefaultRouter()
router.register('functions', CustomFunctionViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 