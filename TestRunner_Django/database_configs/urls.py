from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DatabaseConfigViewSet

router = DefaultRouter()
router.register(r'', DatabaseConfigViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 