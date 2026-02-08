from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Environment, EnvironmentVariable, GlobalRequestHeader

# ======================== 环境配置资源类 ========================
class EnvironmentResource(resources.ModelResource):
    class Meta:
        model = Environment
        skip_unchanged = True
        report_skipped = True
        # 排除自动生成字段和关联循环字段
        exclude = ('id', 'created_time', 'updated_time')
        export_order = (
            'name', 'project', 'base_url', 'verify_ssl',
            'description', 'parent', 'database_config',
            'is_active', 'created_by'
        )

# ======================== 环境配置Admin ========================
@admin.register(Environment)
class EnvironmentAdmin(ImportExportModelAdmin):
    resource_class = EnvironmentResource
    # 列表展示字段
    list_display = [
        'id', 'name', 'project', 'base_url', 'verify_ssl',
        'is_active', 'parent', 'database_config', 'created_by', 'created_time'
    ]
    # 筛选条件
    list_filter = [
        'is_active', 'verify_ssl', 'project', 'created_by', 'created_time'
    ]
    # 搜索字段
    search_fields = ['name', 'base_url', 'description', 'project__name']
    # 只读字段
    readonly_fields = ['created_time', 'updated_time']
    # 分页配置
    list_per_page = 20
    # 导出格式
    formats = ['csv', 'xlsx']
    # 关联字段搜索
    raw_id_fields = ['parent', 'database_config', 'created_by']
    # 字段分组（适配详情页展示）
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'project', 'base_url', 'verify_ssl', 'description', 'is_active')
        }),
        (_('关联配置'), {
            'fields': ('parent', 'database_config'),
            'description': _('父环境必须与当前环境属于同一项目；数据库配置同理')
        }),
        (_('元数据'), {
            'fields': ('created_by', 'created_time', 'updated_time'),
            'classes': ('collapse',)  # 可折叠
        }),
    )

    # 保存时自动触发模型的clean校验
    def save_model(self, request, obj, form, change):
        obj.clean()
        super().save_model(request, obj, form, change)

# ======================== 环境变量资源类 ========================
class EnvironmentVariableResource(resources.ModelResource):
    class Meta:
        model = EnvironmentVariable
        skip_unchanged = True
        report_skipped = True
        exclude = ('id', 'created_time', 'updated_time')
        export_order = ('environment', 'name', 'value', 'type', 'description', 'is_sensitive')

# ======================== 环境变量Admin ========================
@admin.register(EnvironmentVariable)
class EnvironmentVariableAdmin(ImportExportModelAdmin):
    resource_class = EnvironmentVariableResource
    list_display = [
        'id', 'environment', 'name', 'value', 'type',
        'is_sensitive', 'created_time'
    ]
    list_filter = ['type', 'is_sensitive', 'environment__project', 'created_time']
    search_fields = ['name', 'value', 'description', 'environment__name']
    readonly_fields = ['created_time', 'updated_time']
    list_per_page = 20
    formats = ['csv', 'xlsx']
    raw_id_fields = ['environment']
    # 按环境分组
    list_filter = ['environment', 'type', 'is_sensitive']

    def save_model(self, request, obj, form, change):
        obj.clean()  # 触发变量类型校验
        super().save_model(request, obj, form, change)

# ======================== 全局请求头资源类 ========================
class GlobalRequestHeaderResource(resources.ModelResource):
    class Meta:
        model = GlobalRequestHeader
        skip_unchanged = True
        report_skipped = True
        exclude = ('id', 'created_time', 'updated_time')
        export_order = ('name', 'project', 'value', 'description', 'is_enabled', 'created_by')

# ======================== 全局请求头Admin ========================
@admin.register(GlobalRequestHeader)
class GlobalRequestHeaderAdmin(ImportExportModelAdmin):
    resource_class = GlobalRequestHeaderResource
    list_display = [
        'id', 'name', 'project', 'value', 'is_enabled',
        'created_by', 'created_time'
    ]
    list_filter = ['is_enabled', 'project', 'created_by', 'created_time']
    search_fields = ['name', 'value', 'description', 'project__name']
    readonly_fields = ['created_time', 'updated_time']
    list_per_page = 20
    formats = ['csv', 'xlsx']
    raw_id_fields = ['project', 'created_by']
    fieldsets = (
        (_('基本配置'), {
            'fields': ('name', 'project', 'value', 'description', 'is_enabled')
        }),
        (_('元数据'), {
            'fields': ('created_by', 'created_time', 'updated_time'),
            'classes': ('collapse',)
        }),
    )