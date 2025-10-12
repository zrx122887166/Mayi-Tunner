from django.contrib import admin
from .models import TestTaskSuite, TestTaskCase, TestTaskExecution, TestTaskCaseResult


@admin.register(TestTaskSuite)
class TestTaskSuiteAdmin(admin.ModelAdmin):
    """测试任务集管理"""
    list_display = ['id', 'name', 'project', 'priority', 'fail_fast', 'created_by', 'created_time']
    list_filter = ['project', 'priority', 'fail_fast', 'created_by']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_time'


@admin.register(TestTaskCase)
class TestTaskCaseAdmin(admin.ModelAdmin):
    """测试任务用例关联管理"""
    list_display = ['id', 'task_suite', 'testcase', 'order']
    list_filter = ['task_suite']
    search_fields = ['task_suite__name', 'testcase__name']


@admin.register(TestTaskExecution)
class TestTaskExecutionAdmin(admin.ModelAdmin):
    """测试任务执行记录管理"""
    list_display = ['id', 'task_suite', 'status', 'environment', 'start_time', 'end_time',
                   'total_count', 'success_count', 'fail_count', 'error_count', 'executed_by']
    list_filter = ['status', 'environment', 'executed_by']
    search_fields = ['task_suite__name']
    date_hierarchy = 'created_time'


@admin.register(TestTaskCaseResult)
class TestTaskCaseResultAdmin(admin.ModelAdmin):
    """测试任务用例执行结果管理"""
    list_display = ['id', 'execution', 'testcase', 'status', 'start_time', 'end_time', 'duration']
    list_filter = ['status']
    search_fields = ['execution__task_suite__name', 'testcase__name']
    date_hierarchy = 'start_time'
