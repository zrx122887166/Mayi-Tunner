from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Tool, Tools
import json

# ======================== Python工具（Tool）资源类 ========================
class ToolResource(resources.ModelResource):
    class Meta:
        model = Tool
        skip_unchanged = True
        report_skipped = True
        # 排除自动生成字段，保留核心业务字段
        exclude = ('id', 'create_time', 'updated_time')
        # 导出字段顺序（贴合模型逻辑）
        export_order = (
            'name', 'group_name', 'remark', 'pythonScript',
            'params', 'connect_pools', 'creator'
        )


# ======================== Python工具（Tool）Admin配置 ========================
@admin.register(Tool)
class ToolAdmin(ImportExportModelAdmin):
    resource_class = ToolResource
    # 列表页核心展示字段（优化JSON字段预览）
    list_display = [
        'id', 'name', 'group_name', 'creator',
        'script_preview', 'params_preview', 'create_time'
    ]
    # 多维度筛选（适配索引字段）
    list_filter = [
        'group_name', 'creator', 'create_time'
    ]
    # 精准搜索（适配索引字段）
    search_fields = [
        'name', 'group_name', 'remark', 'pythonScript'
    ]
    # 只读字段（自动生成时间）
    readonly_fields = ['create_time', 'updated_time', 'params_formatted', 'connect_pools_formatted']
    # 分页配置（工具类数据通常较多）
    list_per_page = 20
    # 支持的导入导出格式
    formats = ['csv', 'xlsx', 'json']
    # 外键优化（避免大数据量加载卡顿）
    raw_id_fields = ['creator']

    # 详情页字段分组（提升操作体验）
    fieldsets = (
        (_('基础信息'), {
            'fields': ('name', 'group_name', 'remark', 'creator'),
            'description': _('工具名称唯一建议；分组名称用于归类管理（默认：未分组）')
        }),
        (_('脚本配置'), {
            'fields': ('pythonScript',),
            'description': _('请输入合法的Python脚本，支持参数化调用')
        }),
        (_('高级配置'), {
            'fields': ('params_formatted', 'connect_pools_formatted'),  # 替换原生JSON字段
            'classes': ('collapse',),
            'description': _('参数配置/连接池配置为JSON格式，示例：{"param1": "value1"}')
        }),
        (_('元数据'), {
            'fields': ('create_time', 'updated_time'),
            'classes': ('collapse',)
        }),
    )

    # ---------- 自定义列表页字段（优化JSON/长文本展示） ----------
    def script_preview(self, obj):
        """Python脚本预览（显示前100字符）"""
        if not obj.pythonScript:
            return '-'
        return format_html(
            '<span title="{}">{}</span>',
            obj.pythonScript,
            obj.pythonScript[:100] + '...' if len(obj.pythonScript) > 100 else obj.pythonScript
        )

    script_preview.short_description = 'Python脚本预览'

    def params_preview(self, obj):
        """参数配置预览（格式化JSON）"""
        if not obj.params:
            return '-'
        try:
            # 格式化JSON便于阅读
            formatted = json.dumps(obj.params, ensure_ascii=False, indent=2)
            return format_html('<pre style="max-height: 100px; overflow-y: auto;">{}</pre>',
                               formatted[:200] + '...' if len(formatted) > 200 else formatted)
        except Exception:
            return format_html('<span style="color: red;">JSON格式错误</span>')

    params_preview.short_description = '参数配置预览'

    # ---------- 自定义详情页字段（格式化JSON展示） ----------
    def params_formatted(self, obj):
        """详情页格式化展示参数配置"""
        if not obj.params:
            return '-'
        try:
            formatted = json.dumps(obj.params, ensure_ascii=False, indent=2)
            return format_html('<pre style="max-height: 200px; overflow-y: auto;">{}</pre>', formatted)
        except Exception:
            return format_html('<span style="color: red;">JSON解析失败</span>')

    params_formatted.short_description = '参数配置'

    def connect_pools_formatted(self, obj):
        """详情页格式化展示连接池配置"""
        if not obj.connect_pools:
            return '-'
        try:
            formatted = json.dumps(obj.connect_pools, ensure_ascii=False, indent=2)
            return format_html('<pre style="max-height: 200px; overflow-y: auto;">{}</pre>', formatted)
        except Exception:
            return format_html('<span style="color: red;">JSON解析失败</span>')

    connect_pools_formatted.short_description = '连接池配置'

    # ---------- 保存时自动填充创建人 ----------
    def save_model(self, request, obj, form, change):
        if not change and not obj.creator:  # 新增数据且未指定创建人
            obj.creator = request.user
        super().save_model(request, obj, form, change)


# ======================== 脚本依赖工具（Tools）资源类 ========================
class ToolsResource(resources.ModelResource):
    class Meta:
        model = Tools
        skip_unchanged = True
        report_skipped = True
        exclude = ('id', 'create_time')
        export_order = ('name', 'remark', 'pythonScript')


# ======================== 脚本依赖工具（Tools）Admin配置 ========================
@admin.register(Tools)
class ToolsAdmin(ImportExportModelAdmin):
    resource_class = ToolsResource
    # 列表页展示字段
    list_display = ['id', 'name', 'script_preview', 'create_time']
    # 筛选条件
    list_filter = ['create_time']
    # 搜索字段
    search_fields = ['name', 'remark', 'pythonScript']
    # 只读字段
    readonly_fields = ['create_time', 'script_formatted']
    # 分页配置
    list_per_page = 20
    # 导出格式
    formats = ['csv', 'xlsx']

    # 详情页字段分组
    fieldsets = (
        (_('基础信息'), {
            'fields': ('name', 'remark')
        }),
        (_('脚本内容'), {
            'fields': ('script_formatted',),  # 替换原生pythonScript字段
            'description': _('脚本依赖工具的核心代码，用于辅助主工具执行')
        }),
        (_('元数据'), {
            'fields': ('create_time',),
            'classes': ('collapse',)
        }),
    )

    # ---------- 自定义列表页脚本预览 ----------
    def script_preview(self, obj):
        """脚本依赖工具的脚本预览"""
        if not obj.pythonScript:
            return '-'
        return format_html(
            '<span title="{}">{}</span>',
            obj.pythonScript,
            obj.pythonScript[:80] + '...' if len(obj.pythonScript) > 80 else obj.pythonScript
        )

    script_preview.short_description = 'Python脚本预览'

    # ---------- 自定义详情页格式化展示脚本 ----------
    def script_formatted(self, obj):
        """详情页格式化展示脚本内容"""
        if not obj.pythonScript:
            return '-'
        return format_html(
            '<pre style="max-height: 300px; overflow-y: auto; background: #f5f5f5; padding: 10px;">{}</pre>',
            obj.pythonScript
        )

    script_formatted.short_description = 'Python脚本'