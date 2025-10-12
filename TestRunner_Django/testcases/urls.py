from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('tags', views.TestCaseTagViewSet)
router.register('groups', views.TestCaseGroupViewSet)
router.register('reports', views.TestReportViewSet)
router.register('', views.TestCaseViewSet)  # 用例放在最后注册

app_name = 'testcases'

urlpatterns = [
    path('', include(router.urls)),
    # Admin执行路由
    path(
        'admin/testcases/testcase/<int:pk>/execute/',
        views.admin_execute_testcase,
        name='admin-execute-testcase'
    ),
]

# API路由说明:
# 1. 用例管理
# GET    /api/testcases/                    # 获取用例列表
# POST   /api/testcases/                    # 创建用例(包含步骤)
# GET    /api/testcases/{id}/              # 获取用例详情
# PUT    /api/testcases/{id}/              # 更新用例
# DELETE /api/testcases/{id}/              # 删除用例
# POST   /api/testcases/{id}/copy/         # 复制用例
# POST   /api/testcases/{id}/run/          # 执行用例
# POST   /api/testcases/batch_run/         # 批量执行用例
# PUT    /api/testcases/{id}/update_step/  # 修改单个测试步骤
# DELETE /api/testcases/{id}/delete_step/  # 删除单个测试步骤
# GET    /api/testcases/available_interfaces/  # 获取可用接口列表

# 2. 标签管理
# GET    /api/tags/                        # 获取标签列表
# POST   /api/tags/                        # 创建标签
# GET    /api/tags/{id}/                   # 获取标签详情
# PUT    /api/tags/{id}/                   # 更新标签
# DELETE /api/tags/{id}/                   # 删除标签
# GET    /api/tags/statistics/             # 获取标签使用统计

# 3. 分组管理
# GET    /api/groups/                      # 获取分组列表
# POST   /api/groups/                      # 创建分组
# GET    /api/groups/{id}/                 # 获取分组详情
# PUT    /api/groups/{id}/                 # 更新分组
# DELETE /api/groups/{id}/                 # 删除分组
# GET    /api/groups/tree/                 # 获取分组树结构
# GET    /api/groups/{id}/testcases/       # 获取分组下的用例

# 4. 报告管理
# GET    /api/reports/                     # 获取报告列表
# GET    /api/reports/{id}/                # 获取报告概要
# GET    /api/reports/{id}/details/        # 获取报告详情