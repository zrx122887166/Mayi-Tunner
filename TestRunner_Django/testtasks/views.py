from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import TestTaskSuite, TestTaskCase, TestTaskExecution, TestTaskCaseResult
from .serializers import (
    TestTaskSuiteSerializer, TestTaskCaseSerializer, TestTaskCaseCreateSerializer,
    TestTaskExecutionSerializer, TestTaskExecutionCreateSerializer, TestTaskCaseResultSerializer,
    TestTaskExecutionListSerializer
)
from .services import TestTaskService, TestTaskExecutionService
from .tasks import execute_task_async
from .pagination import StandardResultsSetPagination


# 定义通用的响应模式
success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='操作状态', default='success'),
        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码', default=200),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应数据')
    }
)

error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'status': openapi.Schema(type=openapi.TYPE_STRING, description='操作状态', default='error'),
        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码', default=400),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='错误提示信息'),
        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应数据'),
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description='详细错误信息')
    }
)


def api_response(status_type="success", code=200, message="", data=None, errors=None):
    """
    统一API响应格式
    
    Args:
        status_type: 状态类型，"success"或"error"
        code: HTTP状态码
        message: 提示信息
        data: 响应数据
        errors: 错误信息，仅在status_type为"error"时有效
    
    Returns:
        Response: DRF响应对象
    """
    if data is None:
        data = {}
    
    response_data = {
        "status": status_type,
        "code": code,
        "message": message,
        "data": data
    }
    
    if status_type == "error" and errors:
        response_data["errors"] = errors
    
    return Response(response_data, status=code)


class BaseModelViewSet(viewsets.ModelViewSet):
    """基础视图集，统一处理响应格式"""
    pagination_class = StandardResultsSetPagination
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.paginator.get_paginated_response(serializer.data).data
            return api_response(
                message="获取列表成功",
                data=paginated_data
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            message="获取列表成功",
            data={
                "count": len(serializer.data),
                "next": None,
                "previous": None,
                "results": serializer.data
            }
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            message="获取详情成功",
            data=serializer.data
        )
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return api_response(
            code=status.HTTP_201_CREATED,
            message="创建成功",
            data=serializer.data
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return api_response(
            message="更新成功",
            data=serializer.data
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return api_response(
            message="删除成功",
            data={}
        )


class BaseGenericViewSet(viewsets.GenericViewSet):
    """基础通用视图集，统一处理响应格式"""
    pagination_class = StandardResultsSetPagination
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.paginator.get_paginated_response(serializer.data).data
            return api_response(
                message="获取列表成功",
                data=paginated_data
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return api_response(
            message="获取列表成功",
            data={
                "count": len(serializer.data),
                "next": None,
                "previous": None,
                "results": serializer.data
            }
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            message="获取详情成功",
            data=serializer.data
        )


class TestTaskSuiteViewSet(BaseModelViewSet):
    """测试任务集视图集"""
    queryset = TestTaskSuite.objects.all()
    serializer_class = TestTaskSuiteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'priority']
    search_fields = ['name', 'description']
    ordering_fields = ['created_time', 'updated_time', 'name']
    ordering = ['-created_time']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset().prefetch_related(
            'task_cases',
            'task_cases__testcase'
        )
        # 根据项目ID过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        # 添加调试日志
        for task_suite in queryset:
            print(f"任务集[{task_suite.id}]: {task_suite.name}")
            print(f"关联用例数: {task_suite.task_cases.count()}")
            for task_case in task_suite.task_cases.all():
                print(f"  - 用例[{task_case.testcase.id}]: {task_case.testcase.name}")
                
        return queryset
    
    @swagger_auto_schema(
        request_body=TestTaskCaseCreateSerializer,
        responses={
            201: openapi.Response(
                description="测试用例添加成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, default=201),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, default='测试用例添加成功'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'testcase': openapi.Schema(type=openapi.TYPE_OBJECT),
                                    'order': openapi.Schema(type=openapi.TYPE_INTEGER)
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(description="请求参数错误", schema=error_response_schema)
        }
    )
    @action(detail=True, methods=['post'], url_path='add-testcases')
    def add_testcases(self, request, pk=None):
        """添加测试用例到任务集"""
        task_suite = self.get_object()
        
        # 验证请求数据
        serializer = TestTaskCaseCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 添加测试用例
        testcase_ids = serializer.validated_data['testcase_ids']
        task_cases = TestTaskService.add_testcases(task_suite, testcase_ids)
        
        # 序列化结果
        result_serializer = TestTaskCaseSerializer(task_cases, many=True)
        
        return api_response(
            code=status.HTTP_201_CREATED,
            message="测试用例添加成功",
            data=result_serializer.data
        )
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="测试用例移除成功", schema=success_response_schema),
            404: openapi.Response(description="测试用例不存在或移除失败", schema=error_response_schema)
        }
    )
    @action(detail=True, methods=['delete'], url_path='remove-testcase/(?P<testcase_id>[^/.]+)')
    def remove_testcase(self, request, pk=None, testcase_id=None):
        """从任务集中移除测试用例"""
        task_suite = self.get_object()
        
        # 移除测试用例
        success = TestTaskService.remove_testcase(task_suite, testcase_id)
        
        if success:
            return api_response(
                message="测试用例移除成功",
                data={}
            )
        else:
            return api_response(
                status_type="error",
                code=status.HTTP_404_NOT_FOUND,
                message="测试用例不存在或移除失败",
                data={},
                errors={"testcase_id": ["测试用例不存在或移除失败"]}
            )


class TestTaskExecutionViewSet(mixins.CreateModelMixin,
                              mixins.RetrieveModelMixin,
                              mixins.ListModelMixin,
                              BaseGenericViewSet):
    """测试任务执行视图集"""
    queryset = TestTaskExecution.objects.all()
    serializer_class = TestTaskExecutionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['task_suite', 'status', 'environment', 'executed_by']
    search_fields = ['task_suite__name']
    ordering_fields = ['created_time', 'start_time', 'end_time']
    ordering = ['-created_time']
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        # 根据任务集ID过滤
        task_suite_id = self.request.query_params.get('task_suite_id')
        if task_suite_id:
            queryset = queryset.filter(task_suite_id=task_suite_id)
        return queryset
    
    def list(self, request, *args, **kwargs):
        """获取测试任务执行记录列表"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            # 使用简化版序列化器
            serializer = TestTaskExecutionListSerializer(page, many=True)
            paginated_data = self.paginator.get_paginated_response(serializer.data).data
            return api_response(
                message="获取测试任务执行记录列表成功",
                data=paginated_data
            )
        
        # 使用简化版序列化器
        serializer = TestTaskExecutionListSerializer(queryset, many=True)
        return api_response(
            message="获取测试任务执行记录列表成功",
            data={
                "count": len(serializer.data),
                "next": None,
                "previous": None,
                "results": serializer.data
            }
        )
    
    @swagger_auto_schema(
        request_body=TestTaskExecutionCreateSerializer,
        responses={
            201: openapi.Response(
                description="测试任务已创建并开始执行",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, default=201),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, default='测试任务已创建并开始执行'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'task_suite': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'task_suite_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'status': openapi.Schema(type=openapi.TYPE_STRING),
                                'environment': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'environment_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                'duration': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'total_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'success_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'fail_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'error_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'success_rate': openapi.Schema(type=openapi.TYPE_NUMBER, format='float'),
                                'executed_by': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'executed_by_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'created_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(description="请求参数错误", schema=error_response_schema),
            404: openapi.Response(description="任务集不存在", schema=error_response_schema)
        }
    )
    def create(self, request, *args, **kwargs):
        """创建并执行测试任务"""
        # 验证请求数据
        serializer = TestTaskExecutionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 获取任务集和环境
        task_suite_id = serializer.validated_data['task_suite_id']
        environment_id = serializer.validated_data.get('environment_id')
        
        # 获取任务集
        task_suite = get_object_or_404(TestTaskSuite, id=task_suite_id)
        
        # 创建执行记录
        execution = TestTaskExecutionService.create_execution(
            task_suite=task_suite,
            environment_id=environment_id,
            user=request.user
        )
        
        # 异步执行任务
        execute_task_async.delay(execution.id)
        
        # 序列化结果
        result_serializer = self.get_serializer(execution)
        
        return api_response(
            code=status.HTTP_201_CREATED,
            message="测试任务已创建并开始执行",
            data=result_serializer.data
        )
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="获取用例结果成功",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, default='success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, default=200),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, default='获取用例结果成功'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'testcase': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'testcase_name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'start_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                    'end_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                    'duration': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'error_message': openapi.Schema(type=openapi.TYPE_STRING),
                                    'report': openapi.Schema(type=openapi.TYPE_OBJECT)
                                }
                            )
                        )
                    }
                )
            ),
            404: openapi.Response(description="执行记录不存在", schema=error_response_schema)
        }
    )
    @action(detail=True, methods=['get'], url_path='case-results')
    def case_results(self, request, pk=None):
        """获取任务执行的用例结果"""
        execution = self.get_object()
        
        # 获取用例结果
        case_results = execution.case_results.all().order_by('id')
        
        # 序列化结果
        serializer = TestTaskCaseResultSerializer(case_results, many=True)
        
        return api_response(
            message="获取用例结果成功",
            data=serializer.data
        )
    
    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="任务已取消", schema=success_response_schema),
            400: openapi.Response(description="只有等待执行或执行中的任务才能取消", schema=error_response_schema),
            404: openapi.Response(description="执行记录不存在", schema=error_response_schema)
        }
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """取消任务执行"""
        execution = self.get_object()
        
        # 只有等待执行或执行中的任务才能取消
        if execution.status not in ['pending', 'running']:
            return api_response(
                status_type="error",
                code=status.HTTP_400_BAD_REQUEST,
                message="只有等待执行或执行中的任务才能取消",
                data={},
                errors={"status": ["只有等待执行或执行中的任务才能取消"]}
            )
        
        # 取消执行
        execution.cancel()
        
        return api_response(
            message="任务已取消",
            data={}
        )

    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="获取测试任务执行记录详情成功", schema=success_response_schema),
            404: openapi.Response(description="测试任务执行记录不存在", schema=error_response_schema)
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取测试任务执行记录详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return api_response(
            message="获取测试任务执行记录详情成功",
            data=serializer.data
        )
