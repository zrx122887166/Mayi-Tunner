from django.shortcuts import render
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.core.cache import cache
from projects.models import Project
from interfaces.models import Interface
from testcases.models import TestCase, TestReport
from testtasks.models import TestTaskExecution

# Create your views here.

class DashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        # 获取当前用户
        user = request.user
        
        # 为每个用户单独设置缓存键
        cache_key = f'dashboard_summary_{user.id}'
        data = cache.get(cache_key)
        
        if not data:
            # 根据用户权限过滤项目
            # 同时检查 is_superuser 和 is_staff，确保权限判断一致
            if user.is_superuser and user.is_staff:
                # 只有同时具备超级管理员和员工权限才能看到所有项目
                projects = Project.objects.all()
                project_ids = projects.values_list('id', flat=True)
            else:
                # 普通用户只能看到自己加入的项目
                projects = Project.objects.filter(members=user)
                project_ids = projects.values_list('id', flat=True)
            
            # 根据项目权限过滤其他数据
            interfaces = Interface.objects.filter(project_id__in=project_ids)
            testcases = TestCase.objects.filter(project_id__in=project_ids)
            task_executions = TestTaskExecution.objects.filter(task_suite__project_id__in=project_ids)
            test_reports = TestReport.objects.filter(testcase__project_id__in=project_ids)
            
            # 如果缓存中没有，重新计算
            data = {
                'total_projects': projects.count(),
                'total_interfaces': interfaces.count(),
                'total_testcases': testcases.count(),
                'total_tasks': task_executions.count(),
                'success_rate': 0
            }
            
            total_tasks = task_executions.count()
            if total_tasks > 0:
                success_count = task_executions.filter(status='completed').count()
                # 成功率使用小数形式（0-1之间）
                data['success_rate'] = round(success_count / total_tasks, 2)
                
            # 获取最近的任务
            recent_tasks = list(task_executions.order_by('-created_time')[:5].values(
                'id', 'task_suite__name', 'status', 'created_time', 
                'success_count', 'total_count'
            ))
            
            # 计算每个任务的成功率（小数形式）
            for task in recent_tasks:
                if task['total_count'] > 0:
                    task['success_rate'] = round(task['success_count'] / task['total_count'], 2)
                else:
                    task['success_rate'] = 0
            
            data['recent_tasks'] = recent_tasks
            
            # 获取最近的测试报告
            recent_reports = list(test_reports.order_by('-start_time')[:5].values(
                'id', 'name', 'status', 'start_time', 'duration',
                'success_count', 'fail_count', 'error_count', 'testcase__name'
            ))
            
            # 计算每个报告的成功率（小数形式）
            for report in recent_reports:
                total_steps = report['success_count'] + report['fail_count'] + report['error_count']
                if total_steps > 0:
                    report['success_rate'] = round(report['success_count'] / total_steps, 2)
                else:
                    report['success_rate'] = 0
            
            data['recent_reports'] = recent_reports
            
            # 缓存1分钟
            cache.set(cache_key, data, 60)
        
        return Response({
            "status": "success",
            "code": 200,
            "message": "仪表盘数据获取成功",
            "data": data
        })
