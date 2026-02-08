from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import CustomFunction


# ======================== 自定义函数资源类 ========================
class CustomFunctionResource(resources.ModelResource):
    class Meta:
        model = CustomFunction
        skip_unchanged = True  # 跳过无变更的数据
        report_skipped = True  # 报告跳过的记录
        # 排除自动生成/无需导入的字段
        exclude = ('id', 'created_time', 'updated_time')
        # 导出字段顺序（贴合模型字段逻辑）
        export_order = (
            'name', 'project', 'code', 'description',
            'is_active', 'created_by'
        )


# ======================== 自定义函数Admin配置 ========================
@admin.register(CustomFunction)
class CustomFunctionAdmin(ImportExportModelAdmin):
    """自定义函数 - Admin管理配置"""
    resource_class = CustomFunctionResource  # 关联导入导出资源

    # 列表页展示字段（核心信息优先）
    list_display = [
        'id', 'name', 'project', 'is_active',
        'created_by', 'created_time'
    ]
    # 筛选条件（快速过滤）
    list_filter = [
        'is_active', 'project', 'created_by', 'created_time'
    ]
    # 搜索字段（支持跨表搜索项目名称）
    search_fields = [
        'name', 'code', 'description', 'project__name'
    ]
    # 只读字段（自动生成的时间字段）
    readonly_fields = ['created_time', 'updated_time']
    # 分页配置（避免数据过多卡顿）
    list_per_page = 20
    # 支持的导入导出格式
    formats = ['csv', 'xlsx']
    # 外键字段优化（数据量大时用raw_id避免加载卡顿）
    raw_id_fields = ['project', 'created_by']

    # 详情页字段分组（提升操作体验）
    fieldsets = (
        (_('基础配置'), {
            'fields': ('name', 'project', 'code', 'description', 'is_active'),
            'description': _('同一项目下函数名称不可重复，请确保函数代码语法正确')
        }),
        (_('元数据'), {
            'fields': ('created_by', 'created_time', 'updated_time'),
            'classes': ('collapse',)  # 可折叠（非核心信息）
        }),
    )

    # 保存时自动填充创建人（若未指定）
    def save_model(self, request, obj, form, change):
        # 新增数据且未指定创建人时，自动填充为当前登录用户
        if not change and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)