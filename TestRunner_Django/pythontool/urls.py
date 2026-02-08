from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ToolViewSet, ToolsViewSet, PythonRunView

router = DefaultRouter()
router.register(r'pythontool', ToolViewSet, basename='pythontool')
router.register(r'tools', ToolsViewSet, basename='tools')

urlpatterns = [
    path('', include(router.urls)),

    # 兼容旧接口的路由
    path('testrunner/pythonlist/', ToolViewSet.as_view({'get': 'pythonlist'}), name='pythonlist'),
    path('testrunner/pythontool_detail/<int:pk>/', ToolViewSet.as_view({'get': 'detail'}), name='pythontool_detail'),
    path('python_run/', PythonRunView.as_view(), name='python_run'),

    # 依赖工具兼容接口
    path('testrunner/pythonlists/', ToolsViewSet.as_view({'get': 'list'}), name='pythonlists'),
    path('testrunner/pythontools/', ToolsViewSet.as_view({'post': 'create'}), name='pythontools'),
    path('testrunner/pythontool_updates/<int:pk>/', ToolsViewSet.as_view({'put': 'update'}), name='pythontool_updates'),
    path('testrunner/pythontool_details/<int:pk>/', ToolsViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}),
         name='pythontool_details'),
]