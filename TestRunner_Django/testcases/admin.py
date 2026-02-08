from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TestCase, TestCaseStep, TestReport, TestReportDetail,
    TestCaseTag, TestCaseGroup
)
from .services import TestExecutionService


@admin.register(TestCaseTag)
class TestCaseTagAdmin(admin.ModelAdmin):
    """测试用例标签管理"""
    list_display = ['name', 'color', 'project', 'created_by', 'created_time']
    list_filter = ['project', 'created_by']
    search_fields = ['name']
    readonly_fields = ['created_time']


@admin.register(TestCaseGroup)
class TestCaseGroupAdmin(admin.ModelAdmin):
    """测试用例分组管理"""
    list_display = ['name', 'parent', 'project', 'created_by', 'created_time']
    list_filter = ['project', 'parent', 'created_by']
    search_fields = ['name']
    readonly_fields = ['created_time']

    def get_queryset(self, request):
        """按项目过滤分组"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__members=request.user)


@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """测试用例管理"""
    list_display = [
        'name', 'project', 'group', 'priority',
        'created_by', 'created_time', 'execute_button'
    ]
    list_filter = ['project', 'group', 'priority', 'tags']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']
    filter_horizontal = ['tags']
    actions = ['execute_selected_testcases']

    def get_queryset(self, request):
        """按项目过滤用例"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(project__members=request.user)

    def execute_button(self, obj):
        """执行按钮"""
        button_html = f'''<button 
            type="button" 
            onclick="location.href='/admin/testcases/testcase/{obj.id}/execute/'"
            style="
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
                cursor: pointer;
            "
        >
            执行
        </button>'''
        return format_html(button_html)
    execute_button.short_description = '操作'

    def execute_selected_testcases(self, request, queryset):
        """执行选中的测试用例"""
        success = 0
        for testcase in queryset:
            try:
                report = TestExecutionService.run_testcase(
                    testcase=testcase,
                    user=request.user
                )
                success += 1
                self.message_user(
                    request,
                    f'用例 {testcase.name} 执行成功，报告ID: {report.id}'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'用例 {testcase.name} 执行失败: {str(e)}',
                    level='ERROR'
                )
        
        self.message_user(
            request,
            f'成功执行 {success} 个用例，失败 {len(queryset) - success} 个'
        )
    execute_selected_testcases.short_description = '执行选中的用例'


@admin.register(TestCaseStep)
class TestCaseStepAdmin(admin.ModelAdmin):
    """测试步骤管理"""
    list_display = [
        'name', 'testcase', 'order',
        'origin_interface', 'last_sync_time'
    ]
    list_filter = ['testcase', 'origin_interface']
    search_fields = ['name']
    readonly_fields = ['last_sync_time']
    ordering = ['testcase', 'order']

    def get_queryset(self, request):
        """按项目过滤步骤"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(testcase__project__members=request.user)


@admin.register(TestReport)
class TestReportAdmin(admin.ModelAdmin):
    """测试报告管理"""
    list_display = [
        'name', 'testcase', 'status', 'success_count',
        'fail_count', 'error_count', 'duration',
        'start_time', 'executed_by'
    ]
    list_filter = ['status', 'testcase', 'executed_by']
    search_fields = ['name', 'testcase__name']
    readonly_fields = [
        'name', 'status', 'success_count', 'fail_count',
        'error_count', 'duration', 'start_time', 'summary',
        'testcase', 'environment', 'executed_by'
    ]
    ordering = ['-start_time']

    def has_add_permission(self, request):
        """禁止手动添加报告"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁止修改报告"""
        return False

    def get_queryset(self, request):
        """按项目过滤报告"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(testcase__project__members=request.user)


@admin.register(TestReportDetail)
class TestReportDetailAdmin(admin.ModelAdmin):
    """测试报告详情管理"""
    list_display = [
        'report', 'step', 'success',
        'elapsed'
    ]
    list_filter = ['report', 'success']
    search_fields = ['report__name', 'step__name']
    readonly_fields = [
        'report', 'step', 'success', 'elapsed',
        'request', 'response', 'validators',
        'extracted_variables', 'attachment'
    ]
    ordering = ['report', 'id']

    def has_add_permission(self, request):
        """禁止手动添加报告详情"""
        return False

    def has_change_permission(self, request, obj=None):
        """禁止修改报告详情"""
        return False

    def get_queryset(self, request):
        """按项目过滤报告详情"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(report__testcase__project__members=request.user)
