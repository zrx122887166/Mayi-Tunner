from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TestTaskSuiteViewSet, TestTaskExecutionViewSet

# 创建路由器
router = DefaultRouter()
router.register(r'suites', TestTaskSuiteViewSet)
router.register(r'executions', TestTaskExecutionViewSet)

# URL配置
urlpatterns = [
    path('', include(router.urls)),
] 