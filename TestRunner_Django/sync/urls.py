from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('configs', views.SyncConfigViewSet)
router.register('histories', views.SyncHistoryViewSet)
router.register('global-configs', views.GlobalSyncConfigViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 