"""
URL configuration for TestRunner project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.http import JsonResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# swagger文档配置
schema_view = get_schema_view(
    openapi.Info(
        title="TestRunner API",
        default_version='v1',
        description="TestRunner项目的API文档",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@testrunner.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

def health_check(request):
    """健康检查接口"""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API路由 - 注意顺序,更具体的路由应该在更通用的路由之前
    path('api/database-configs/', include('database_configs.urls')),
    path('api/environments/', include('environments.urls')),
    path('api/functions/', include('functions.urls')),
    path('api/health/', health_check),
    path('api/interfaces/', include('interfaces.urls')),
    path('api/modules/', include('modules.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/sync/', include('sync.urls')),
    path('api/testcases/', include('testcases.urls')),
    path('api/testtasks/', include('testtasks.urls')),
    path('api/users/', include('users.urls')),
    path('api/', include('pythontool.urls')),
    # dashboard路由放在最后,因为它匹配 'api/',避免覆盖其他更具体的路由
    path('api/', include('dashboard.urls')),
    
    # swagger文档
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
