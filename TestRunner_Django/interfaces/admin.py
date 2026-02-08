from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Interface, InterfaceResult


# ======================== 接口资源类 ========================
class InterfaceResource(resources.ModelResource):
    class Meta:
        model = Interface
        skip_unchanged = True
        report_skipped = True
        # 排除自动生成/关联清理字段
        exclude = ('id', 'created_time', 'updated_time')
        # 按接口类型分组导出字段
        export_order = (
            'name', 'project', 'module', 'type',
            # HTTP字段
            'method', 'url', 'headers', 'params', 'body',
            # SQL字段
            'sql_method', 'sql', 'sql_params', 'sql_size',
            # 通用字段
            'setup_hooks', 'teardown_hooks', 'variables', 'validators', 'extract',
            'created_by'
        )


# ======================== 接口Admin配置 ========================
@admin.register(Interface)
class InterfaceAdmin(ImportExportModelAdmin):
    resource_class = InterfaceResource
    # 列表页核心展示字段
    list_display = [
        'id', 'name', 'project', 'module', 'type',
        'method', 'sql_method', 'created_by', 'created_time'
    ]
    # 多维度筛选（按类型/项目/模块/创建人）
    list_filter = [
        'type', 'method', 'sql_method',
        'project', 'module', 'created_by', 'created_time'
    ]
    # 精准搜索（支持接口名、URL、SQL、项目名）
    search_fields = [
        'name', 'url', 'sql', 'project__name', 'module__name'
    ]
    # 只读字段（自动生成时间）
    readonly_fields = ['created_time', 'updated_time']
    # 分页配置
    list_per_page = 20
    # 支持的导入导出格式
    formats = ['csv', 'xlsx']
    # 外键优化（避免大数据量加载卡顿）
    raw_id_fields = ['project', 'module', 'created_by']

    # 详情页字段分组（按接口类型差异化展示）
    fieldsets = (
        (_('基础信息'), {
            'fields': ('name', 'project', 'module', 'type', 'created_by'),
            'description': _('同一项目下接口名称不可重复；模块必须属于当前项目')
        }),
        (_('HTTP接口配置'), {
            'fields': ('method', 'url', 'headers', 'params', 'body'),
            'classes': ('collapse',),  # 默认折叠
            'description': _('仅HTTP接口需要配置')
        }),
        (_('SQL接口配置'), {
            'fields': ('sql_method', 'sql', 'sql_params', 'sql_size'),
            'classes': ('collapse',),  # 默认折叠
            'description': _('仅SQL接口需要配置，sql_size仅用于fetchmany方法')
        }),
        (_('通用配置（Httprunner）'), {
            'fields': ('setup_hooks', 'teardown_hooks', 'variables', 'validators', 'extract'),
            'classes': ('collapse',),
            'description': _('断言规则格式：[{"eq": ["status_code", 200]}]；提取变量格式：{"token": "body.data.token"}')
        }),
        (_('元数据'), {
            'fields': ('created_time', 'updated_time'),
            'classes': ('collapse', 'wide'),
        }),
    )

    # 保存时触发模型校验和字段清理
    def save_model(self, request, obj, form, change):
        # 自动填充创建人（新增数据时）
        if not change and not obj.created_by:
            obj.created_by = request.user

        # 校验模块与项目的关联性
        if obj.module and obj.module.project != obj.project:
            raise ValidationError(_("模块必须属于当前项目"))

        # 调用模型自带的save方法（自动清理不同类型的字段）
        try:
            obj.save()
        except ValueError as e:
            raise ValidationError(str(e))

        super().save_model(request, obj, form, change)

    # 列表页优化：接口类型显示中文
    def get_list_display(self, request):
        return super().get_list_display(request)

    # 导入时过滤无效数据
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        for row in dataset.dict:
            # 校验接口类型与字段的匹配性
            if row.get('type') == 'http':
                # HTTP接口必须有method和url
                if not row.get('method') or not row.get('url'):
                    raise ValidationError(_("HTTP接口必须填写请求方法和URL"))
            elif row.get('type') == 'sql':
                # SQL接口必须有sql_method和sql
                if not row.get('sql_method') or not row.get('sql'):
                    raise ValidationError(_("SQL接口必须填写SQL方法和SQL语句"))


# ======================== 接口执行结果资源类（仅导出） ========================
class InterfaceResultResource(resources.ModelResource):
    class Meta:
        model = InterfaceResult
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)
        export_order = (
            'interface', 'environment', 'status', 'elapsed',
            'request', 'response', 'validation_results', 'extracted_variables',
            'executed_by', 'executed_time'
        )


# ======================== 接口执行结果Admin配置（只读） ========================
@admin.register(InterfaceResult)
class InterfaceResultAdmin(ImportExportModelAdmin):
    resource_class = InterfaceResultResource
    # 列表页展示字段
    list_display = [
        'id', 'interface', 'environment', 'status',
        'elapsed', 'executed_by', 'executed_time'
    ]
    # 多维度筛选（按执行状态/环境/接口/执行人）
    list_filter = [
        'status', 'environment__project', 'interface__project',
        'executed_by', 'executed_time'
    ]
    # 搜索字段（支持接口名、执行环境）
    search_fields = [
        'interface__name', 'environment__name', 'executed_by__username'
    ]
    # 执行结果只读（禁止修改）
    readonly_fields = [
        'interface', 'environment', 'status', 'elapsed',
        'request', 'response', 'validation_results', 'extracted_variables',
        'executed_by', 'executed_time'
    ]
    # 分页配置（结果数据通常较多）
    list_per_page = 50
    # 仅允许导出，禁止导入（避免篡改执行结果）
    import_enable = False
    # 导出格式
    formats = ['csv', 'xlsx', 'json']
    # 外键优化
    raw_id_fields = ['interface', 'environment', 'executed_by']

    # 详情页字段分组
    fieldsets = (
        (_('关联信息'), {
            'fields': ('interface', 'environment', 'executed_by')
        }),
        (_('执行结果'), {
            'fields': ('status', 'elapsed', 'validation_results', 'extracted_variables')
        }),
        (_('请求/响应详情'), {
            'fields': ('request', 'response'),
            'classes': ('collapse',)
        }),
        (_('执行时间'), {
            'fields': ('executed_time',)
        }),
    )

    # 禁止删除执行结果（可选，根据业务需求调整）
    def has_delete_permission(self, request, obj=None):
        return False  # 返回True则允许删除

    # 禁止修改执行结果
    def has_change_permission(self, request, obj=None):
        return False