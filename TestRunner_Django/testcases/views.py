from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.db import transaction, models
from django.db.models import Count, Max
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import (
    TestCase, TestCaseStep, TestReport, TestReportDetail,
    TestCaseTag, TestCaseGroup
)
from .serializers import (
    TestCaseSerializer, TestCaseStepSerializer,
    TestReportSerializer, TestReportDetailSerializer,
    TestCaseTagSerializer, TestCaseGroupSerializer,
    InterfaceOptionSerializer, TestReportListSerializer
)
from .services import TestCaseService, TestExecutionService
from interfaces.models import Interface
from testtasks.views import BaseModelViewSet, api_response
from testtasks.pagination import StandardResultsSetPagination


class TestCaseFilter(django_filters.FilterSet):
    """测试用例过滤器"""
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags',
        queryset=TestCaseTag.objects.all(),
        conjoined=False  # 使用OR关系，任意一个标签匹配即可
    )
    
    class Meta:
        model = TestCase
        fields = {
            'project': ['exact'],
            'priority': ['exact'],
            'group': ['exact']
        }


class TestReportFilter(django_filters.FilterSet):
    """测试报告过滤器"""
    project = django_filters.NumberFilter(field_name='testcase__project')
    project_id = django_filters.NumberFilter(field_name='testcase__project')
    
    class Meta:
        model = TestReport
        fields = {
            'status': ['exact'],
            'testcase': ['exact'],
            'environment': ['exact'],
            'executed_by': ['exact'],
            'testcase__project': ['exact']
        }


@login_required
def admin_execute_testcase(request, pk):
    """Admin后台执行测试用例"""
    testcase = get_object_or_404(TestCase, pk=pk)
    try:
        report = TestExecutionService.run_testcase(
            testcase=testcase,
            user=request.user
        )
        messages.success(
            request,
            f'用例执行成功，报告ID: {report.id}'
        )
    except Exception as e:
        messages.error(
            request,
            f'用例执行失败: {str(e)}'
        )
    
    # 返回用例列表页
    return redirect('admin:testcases_testcase_changelist')


class TestCaseTagViewSet(viewsets.ModelViewSet):
    """测试用例标签视图集"""
    queryset = TestCaseTag.objects.all()
    serializer_class = TestCaseTagSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['project']
    search_fields = ['name']
    ordering = ['name']
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_queryset(self):
        """按项目过滤标签"""
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    @action(detail=False)
    def statistics(self, request):
        """获取标签使用统计"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            raise ValidationError('缺少project_id参数')
            
        tags = self.get_queryset().annotate(
            usage_count=Count('testcases')
        ).values('id', 'name', 'color', 'usage_count')
        
        return Response(tags)


class TestCaseGroupViewSet(viewsets.ModelViewSet):
    """测试用例分组视图集"""
    queryset = TestCaseGroup.objects.all()
    serializer_class = TestCaseGroupSerializer
    filterset_fields = ['project', 'parent']
    search_fields = ['name']
    ordering = ['name']

    def get_queryset(self):
        """按项目过滤分组"""
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    @action(detail=False)
    def tree(self, request):
        """获取分组树结构"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            raise ValidationError('缺少project_id参数')
            
        # 获取顶级分组
        root_groups = self.get_queryset().filter(parent=None)
        serializer = self.get_serializer(root_groups, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def testcases(self, request, pk=None):
        """获取分组下的用例"""
        group = self.get_object()
        testcases = group.testcases.all()
        serializer = TestCaseSerializer(testcases, many=True)
        return Response(serializer.data)


class TestCaseViewSet(BaseModelViewSet):
    """测试用例视图集
    
    支持的操作:
    1. 创建、更新、删除测试用例
    2. 获取用例列表和详情
    3. 执行测试用例
    4. 管理测试步骤
    
    更新用例步骤时可以通过 update_mode 参数控制处理方式:
    - 'auto': 自动模式，如果步骤内容相同则跳过，否则根据情况创建新步骤或调整顺序(默认)
    - 'update': 如果存在相同顺序的步骤，则更新该步骤而不是创建新步骤
    - 'create': 总是创建新步骤，并自动调整顺序
    
    示例请求:
    PATCH /api/testcases/123/
    {
        "name": "测试用例名称",
        "update_mode": "update",  // 可选，控制步骤处理方式
        "steps_info": [
            {
                "name": "步骤1",
                "order": 1,
                "interface_id": 456
            }
        ]
    }
    """
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TestCaseFilter
    ordering_fields = ['created_time', 'updated_time']
    ordering = ['-created_time']

    def get_queryset(self):
        """根据项目过滤用例"""
        queryset = super().get_queryset()
        project = self.request.query_params.get('project')
        if project:
            queryset = queryset.filter(project_id=project)
        return queryset

    @action(detail=False)
    def available_interfaces(self, request):
        """获取可用的接口列表"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            raise ValidationError('缺少project_id参数')
            
        interfaces = Interface.objects.filter(
            project_id=project_id
        ).select_related('project', 'module')
        
        serializer = InterfaceOptionSerializer(interfaces, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def referenced_interfaces(self, request, pk=None):
        """获取用例引用的接口列表"""
        testcase = self.get_object()
        
        # 获取所有引用了接口的测试步骤
        steps = testcase.steps.filter(
            origin_interface__isnull=False
        ).select_related('origin_interface', 'origin_interface__module')
        
        # 按接口分组，避免重复
        interfaces = {}
        for step in steps:
            interface = step.origin_interface
            if interface.id not in interfaces:
                interfaces[interface.id] = {
                    'interface': interface,
                    'steps': []
                }
            interfaces[interface.id]['steps'].append(step)
        
        # 构建响应数据
        data = []
        for interface_info in interfaces.values():
            interface = interface_info['interface']
            steps = interface_info['steps']
            data.append({
                'id': interface.id,
                'name': interface.name,
                'method': interface.method,
                'url': interface.url,
                'module': interface.module.name if interface.module else "未分类",
                'steps': [{
                    'id': step.id,
                    'name': step.name,
                    'order': step.order,
                    'sync_fields': step.sync_fields,
                    'last_sync_time': step.last_sync_time
                } for step in steps]
            })
        
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取用例引用的接口列表成功',
            'data': data
        })

    @action(detail=True, methods=['post'])
    def copy(self, request, pk=None):
        """复制测试用例"""
        testcase = self.get_object()
        
        with transaction.atomic():
            # 复制用例基本信息
            testcase.pk = None
            testcase.name = f"{testcase.name}_copy"
            testcase.created_by = request.user
            testcase.save()
            
            # 复制标签关联
            original = TestCase.objects.get(pk=pk)
            testcase.tags.set(original.tags.all())
            
            # 复制用例步骤
            steps = TestCaseStep.objects.filter(testcase_id=pk)
            for step in steps:
                step.pk = None
                step.testcase = testcase
                step.save()
        
        serializer = self.get_serializer(testcase)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """执行测试用例"""
        testcase = self.get_object()
        environment_id = request.data.get('environment')
        
        # 获取环境配置
        environment_config = None
        if environment_id is not None:
            try:
                from environments.models import Environment
                env = Environment.objects.get(id=environment_id)
                # 获取环境配置
                environment_config = {
                    'id': env.id,
                    'base_url': env.base_url,
                    'verify_ssl': env.verify_ssl,
                    'variables': env.get_all_variables()
                }
            except Environment.DoesNotExist:
                return Response({
                    'status': 'error',
                    'code': status.HTTP_404_NOT_FOUND,
                    'message': f'环境ID {environment_id} 不存在',
                    'data': {}
                })
        
        try:
            report = TestExecutionService.run_testcase(
                testcase=testcase,
                environment=environment_config,
                user=request.user
            )
            
            return Response({
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': '用例执行成功',
                'data': {
                    'report_id': report.id,
                    'status': report.status,
                    'success_count': report.success_count,
                    'fail_count': report.fail_count,
                    'error_count': report.error_count,
                    'duration': report.duration,
                    'config': environment_config  # 返回实际使用的配置
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': f'用例执行失败: {str(e)}',
                'data': {}
            })

    @action(detail=False, methods=['post'])
    def batch_run(self, request):
        """批量执行测试用例"""
        testcase_ids = request.data.get('testcase_ids', [])
        if not testcase_ids:
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '缺少testcase_ids参数',
                'data': {}
            })
            
        environment_id = request.data.get('environment')
        
        # 获取环境配置
        environment_config = None
        if environment_id is not None:
            try:
                from environments.models import Environment
                env = Environment.objects.get(id=environment_id)
                # 获取环境配置
                environment_config = {
                    'id': env.id,
                    'base_url': env.base_url,
                    'verify_ssl': env.verify_ssl,
                    'variables': env.get_all_variables()
                }
            except Environment.DoesNotExist:
                return Response({
                    'status': 'error',
                    'code': status.HTTP_404_NOT_FOUND,
                    'message': f'环境ID {environment_id} 不存在',
                    'data': {}
                })
        
        try:
            testcases = TestCase.objects.filter(id__in=testcase_ids)
            reports = TestExecutionService.run_batch(
                testcases=testcases,
                environment=environment_config,
                user=request.user
            )
            
            statistics = TestExecutionService.get_statistics(reports)
            
            return Response({
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': '批量执行完成',
                'data': {
                    'statistics': statistics,
                    'report_ids': [report.id for report in reports],
                    'config': environment_config  # 返回实际使用的配置
                }
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': f'批量执行失败: {str(e)}',
                'data': {}
            })

    @action(detail=True, methods=['delete'])
    def delete_step(self, request, pk=None):
        """删除测试步骤"""
        testcase = self.get_object()
        step_id = request.query_params.get('step_id')
        
        if not step_id:
            return Response({
                "status": "error",
                "code": 400,
                "message": "缺少step_id参数",
                "data": {},
                "errors": {"step_id": ["该字段是必需的"]}
            }, status=400)
        
        try:
            with transaction.atomic():
                # 删除指定步骤
                step = testcase.steps.get(id=step_id)
                step.delete()
                
                # 重新排序剩余步骤
                for index, step in enumerate(testcase.steps.all().order_by('order'), start=1):
                    if step.order != index:
                        step.order = index
                        step.save()
            
            return Response({
                "status": "success",
                "code": 200,
                "message": "测试步骤删除成功",
                "data": TestCaseSerializer(testcase).data
            })
            
        except TestCaseStep.DoesNotExist:
            return Response({
                "status": "error",
                "code": 404,
                "message": "测试步骤不存在",
                "data": {},
                "errors": {"step_id": ["指定的测试步骤不存在"]}
            }, status=404)
        except Exception as e:
            return Response({
                "status": "error",
                "code": 500,
                "message": f"删除测试步骤失败: {str(e)}",
                "data": {},
                "errors": {"detail": ["服务器内部错误"]}
            }, status=500)

    def update(self, request, *args, **kwargs):
        """
        更新测试用例
        
        可以通过提供update_mode参数来控制steps_info的处理方式：
        - 'auto': 自动模式，如果步骤内容相同则跳过，否则根据情况创建新步骤或调整顺序(默认)
        - 'update': 如果存在相同顺序的步骤，则更新该步骤而不是创建新步骤
        - 'create': 总是创建新步骤，并自动调整顺序
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 从请求数据中提取update_mode
        update_mode = request.data.get('update_mode', 'auto')
        data = request.data.copy()
        
        # 将update_mode添加到validated_data中
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # 添加update_mode到validated_data
        serializer.validated_data['update_mode'] = update_mode
        
        # 调用序列化器的update方法
        result = serializer.save()
        
        # 如果返回的是统一格式的响应数据，直接返回
        if isinstance(result, dict) and 'status' in result:
            return Response(result)
            
        # 否则返回默认的序列化数据
        return Response(serializer.data)

    @action(detail=True)
    def history_reports(self, request, pk=None):
        """获取用例的历史执行报告"""
        testcase = self.get_object()
        reports = testcase.reports.all().select_related(
            'environment',
            'executed_by'
        ).order_by('-start_time')

        # 使用分页器
        page = self.paginate_queryset(reports)
        if page is not None:
            serializer = TestReportListSerializer(page, many=True)
            data = {
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'results': serializer.data
            }
            return Response({
                "status": "success",
                "code": 200,
                "message": "获取用例历史报告成功",
                "data": data
            })

        serializer = TestReportListSerializer(reports, many=True)
        return Response({
            "status": "success",
            "code": 200,
            "message": "获取用例历史报告成功",
            "data": {
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data
            }
        })

    @action(detail=True, methods=['put'])
    def update_step(self, request, pk=None):
        """修改测试步骤
        
        请求示例:
        {
            "step_id": 123,
            "name": "修改后的步骤名称",
            "order": 1,
            "interface_id": 456,  // 可选，更换关联的接口
            "interface_data": {  // 可选，更新接口数据
                "method": "POST",
                "url": "/api/resource",
                "headers": {"Content-Type": "application/json"},
                "params": {},
                "body": {"type": "raw", "content": "{\"key\": \"value\"}"},
                "validators": [{"eq": ["status_code", 200]}],
                "extract": {"token": "body.data.token"},
                "variables": {"user_id": 1001},
                "setup_hooks": [],
                "teardown_hooks": []
            }
        }
        """
        testcase = self.get_object()
        step_id = request.data.get('step_id')
        
        if not step_id:
            return Response({
                "status": "error",
                "code": 400,
                "message": "缺少step_id参数",
                "data": {},
                "errors": {"step_id": ["该字段是必需的"]}
            }, status=400)
        
        try:
            # 获取要修改的步骤
            step = testcase.steps.get(id=step_id)
            
            # 保存旧的order值
            old_order = step.order
            new_order = request.data.get('order')
            
            # 复制请求数据，移除order字段避免序列化器处理
            data_without_order = request.data.copy()
            if 'order' in data_without_order:
                data_without_order.pop('order')
            
            # 准备序列化器（不包含order字段）
            serializer = TestCaseStepSerializer(
                instance=step,
                data=data_without_order,
                context={'request': request},
                partial=True
            )
            
            # 验证数据
            serializer.is_valid(raise_exception=True)
            
            # 使用事务保证操作的原子性
            with transaction.atomic():
                # 如果order发生变化，使用批量更新方式调整顺序
                if new_order is not None and int(new_order) != old_order:
                    # 将新order转换为整数
                    new_order = int(new_order)
                    
                    # 方案：使用大的临时值空间，避免任何冲突
                    # 1. 先将所有需要调整的步骤移到临时位置（+1000）
                    # 2. 然后将它们移到最终位置
                    
                    # 获取所有步骤并按顺序排列
                    all_steps = list(testcase.steps.all().order_by('order'))
                    
                    # 创建新的顺序映射
                    new_orders = {}
                    current_position = 1
                    
                    for s in all_steps:
                        if s.id == step.id:
                            # 跳过当前要移动的步骤
                            continue
                        
                        if current_position == new_order:
                            # 在这个位置插入要移动的步骤
                            new_orders[step.id] = new_order
                            current_position += 1
                        
                        # 分配新的顺序给其他步骤
                        new_orders[s.id] = current_position
                        current_position += 1
                    
                    # 如果步骤要移到最后
                    if step.id not in new_orders:
                        new_orders[step.id] = current_position
                    
                    # 第一步：将所有步骤移到临时位置（+1000）
                    for s in all_steps:
                        s.order = s.order + 1000
                        s.save(update_fields=['order'])
                    
                    # 第二步：将步骤移到最终位置
                    for step_id_to_update, final_order in new_orders.items():
                        TestCaseStep.objects.filter(
                            id=step_id_to_update,
                            testcase=testcase
                        ).update(order=final_order)
                    
                    # 刷新step对象以获取新的order值
                    step.refresh_from_db()
                
                # 保存其他字段的修改（order已经单独处理）
                if data_without_order:  # 如果还有其他字段需要更新
                    serializer.save()
            
            # 返回响应
            return Response({
                "status": "success",
                "code": 200,
                "message": "测试步骤修改成功",
                "data": serializer.data
            })
            
        except TestCaseStep.DoesNotExist:
            return Response({
                "status": "error",
                "code": 404,
                "message": "测试步骤不存在",
                "data": {},
                "errors": {"step_id": ["指定的测试步骤不存在"]}
            }, status=404)
        except Exception as e:
            return Response({
                "status": "error",
                "code": 500,
                "message": f"修改测试步骤失败: {str(e)}",
                "data": {},
                "errors": {"detail": [str(e)]}
            }, status=500)

    @action(detail=True, methods=['post'])
    def reorder_steps(self, request, pk=None):
        """批量调整测试步骤顺序
        
        专门用于拖拽排序等场景，支持批量调整多个步骤的顺序
        
        请求示例 - 批量调整:
        {
            "steps": [
                {"step_id": 61, "order": 1},
                {"step_id": 62, "order": 2},
                {"step_id": 63, "order": 3}
            ]
        }
        
        或者单个步骤调整:
        {
            "step_id": 61,
            "new_order": 3
        }
        """
        testcase = self.get_object()
        
        # 支持两种请求格式
        steps_data = request.data.get('steps')
        single_step_id = request.data.get('step_id')
        new_order = request.data.get('new_order')
        
        try:
            with transaction.atomic():
                if steps_data:
                    # 批量调整模式
                    # 验证步骤ID都属于该测试用例
                    step_ids = [step['step_id'] for step in steps_data]
                    existing_steps = testcase.steps.filter(id__in=step_ids)
                    
                    if existing_steps.count() != len(step_ids):
                        return Response({
                            "status": "error",
                            "code": 400,
                            "message": "部分步骤ID无效或不属于该测试用例",
                            "data": {},
                            "errors": {"steps": ["某些步骤ID不存在"]}
                        }, status=400)
                    
                    # 创建步骤ID到新顺序的映射
                    order_map = {step['step_id']: step['order'] for step in steps_data}
                    
                    # 批量更新顺序
                    for step in existing_steps:
                        if step.id in order_map:
                            step.order = order_map[step.id]
                            step.save(update_fields=['order'])
                    
                    # 确保所有步骤顺序连续
                    all_steps = testcase.steps.all().order_by('order')
                    for index, step in enumerate(all_steps, start=1):
                        if step.order != index:
                            step.order = index
                            step.save(update_fields=['order'])
                    
                    return Response({
                        "status": "success",
                        "code": 200,
                        "message": "步骤顺序批量调整成功",
                        "data": TestCaseSerializer(testcase).data
                    })
                    
                elif single_step_id and new_order is not None:
                    # 单个步骤调整模式
                    try:
                        step = testcase.steps.get(id=single_step_id)
                    except TestCaseStep.DoesNotExist:
                        return Response({
                            "status": "error",
                            "code": 404,
                            "message": "测试步骤不存在",
                            "data": {},
                            "errors": {"step_id": ["指定的测试步骤不存在"]}
                        }, status=404)
                    
                    old_order = step.order
                    new_order = int(new_order)
                    
                    if old_order == new_order:
                        # 顺序没有变化，直接返回
                        return Response({
                            "status": "success",
                            "code": 200,
                            "message": "步骤顺序未变化",
                            "data": TestCaseStepSerializer(step).data
                        })
                    
                    # 临时将当前步骤移到一个不会冲突的位置
                    step.order = 9999
                    step.save(update_fields=['order'])
                    
                    # 调整其他步骤的顺序
                    if new_order > old_order:
                        # 向下移动：中间的步骤向上移动
                        steps_to_update = testcase.steps.filter(
                            order__gt=old_order,
                            order__lte=new_order
                        ).exclude(id=step.id)
                        for s in steps_to_update:
                            s.order -= 1
                            s.save(update_fields=['order'])
                    else:
                        # 向上移动：中间的步骤向下移动
                        steps_to_update = testcase.steps.filter(
                            order__gte=new_order,
                            order__lt=old_order
                        ).exclude(id=step.id)
                        for s in steps_to_update:
                            s.order += 1
                            s.save(update_fields=['order'])
                    
                    # 设置新的顺序
                    step.order = new_order
                    step.save(update_fields=['order'])
                    
                    return Response({
                        "status": "success",
                        "code": 200,
                        "message": "步骤顺序调整成功",
                        "data": TestCaseStepSerializer(step).data
                    })
                    
                else:
                    return Response({
                        "status": "error",
                        "code": 400,
                        "message": "请提供steps数组或step_id与new_order参数",
                        "data": {},
                        "errors": {"request": ["缺少必要参数"]}
                    }, status=400)
                    
        except Exception as e:
            return Response({
                "status": "error",
                "code": 500,
                "message": f"调整步骤顺序失败: {str(e)}",
                "data": {},
                "errors": {"detail": [str(e)]}
            }, status=500)


class TestReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    测试报告视图集
    
    list:
    获取测试报告列表，支持通过 project 或 project_id 参数过滤特定项目的报告
    
    retrieve:
    获取测试报告详情
    """
    queryset = TestReport.objects.all()
    serializer_class = TestReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TestReportFilter
    search_fields = ['name', 'testcase__name']
    ordering_fields = ['start_time', 'duration', 'success_count', 'fail_count', 'error_count']
    ordering = ['-start_time']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """根据不同的操作返回不同的序列化器"""
        if self.action == 'list':
            return TestReportListSerializer
        return TestReportSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 获取当前用户
        user = self.request.user
        
        # 基于用户权限过滤
        if not user.is_superuser:
            # 普通用户只能看到自己有权限的项目的报告
            queryset = queryset.filter(testcase__project__members=user)
        
        # 基于项目ID过滤 - 同时支持 project_id 和 project 参数
        project_id = self.request.query_params.get('project_id')
        project = self.request.query_params.get('project')
        
        # 优先使用 project_id，如果没有则使用 project
        if project_id:
            queryset = queryset.filter(testcase__project_id=project_id)
        elif project:
            queryset = queryset.filter(testcase__project_id=project)
            
        # 根据不同视图加载不同的关联数据
        if self.action == 'list':
            # 列表视图只需要基本关联，不需要预加载详情
            return queryset.select_related(
                'testcase',
                'environment',
                'executed_by'
            )
        # 详情视图需要预加载所有关联数据
        return queryset.select_related(
            'testcase',
            'environment',
            'environment__project',
            'executed_by'
        ).prefetch_related('details', 'details__step')

    def list(self, request, *args, **kwargs):
        # 处理分页大小
        page_size = request.query_params.get('page_size')
        if page_size:
            self.pagination_class.page_size = int(page_size)
            
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = {
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'results': serializer.data
            }
            return Response({
                "status": "success",
                "code": 200,
                "message": "获取测试报告列表成功",
                "data": data
            })
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "code": 200,
            "message": "获取测试报告列表成功",
            "data": {
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data
            }
        })

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            "status": "success",
            "code": 200,
            "message": "获取测试报告详情成功",
            "data": response.data
        })
