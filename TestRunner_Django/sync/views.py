from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.utils import timezone

from .models import SyncConfig, SyncHistory, GlobalSyncConfig
from .serializers import (
    SyncConfigSerializer, SyncHistorySerializer,
    GlobalSyncConfigSerializer
)
from interfaces.models import Interface
from testcases.models import TestCase, TestCaseStep
from .tasks import sync_interface_data, batch_sync_interface_data

class SyncConfigViewSet(viewsets.ModelViewSet):
    """同步配置视图集"""
    queryset = SyncConfig.objects.all()
    serializer_class = SyncConfigSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        # 支持按接口、用例、步骤、项目过滤
        interface_id = self.request.query_params.get('interface_id')
        testcase_id = self.request.query_params.get('testcase_id')
        step_id = self.request.query_params.get('step_id')
        project_id = self.request.query_params.get('project_id')

        if interface_id:
            queryset = queryset.filter(interface_id=interface_id)
        if testcase_id:
            queryset = queryset.filter(testcase_id=testcase_id)
        if step_id:
            queryset = queryset.filter(step_id=step_id)
        if project_id:
            queryset = queryset.filter(interface__project_id=project_id)

        return queryset

    def list(self, request, *args, **kwargs):
        """获取同步配置列表"""
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
                'status': 'success',
                'code': 200,
                'message': '获取同步配置列表成功',
                'data': data
            })
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取同步配置列表成功',
            'data': {
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data
            }
        })

    def retrieve(self, request, *args, **kwargs):
        """获取同步配置详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取同步配置详情成功',
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """创建同步配置"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({
            'status': 'success',
            'code': 201,
            'message': '创建同步配置成功',
            'data': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """更新同步配置"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'status': 'success',
            'code': 200,
            'message': '更新同步配置成功',
            'data': serializer.data
        })

    def destroy(self, request, *args, **kwargs):
        """删除同步配置"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'status': 'success',
            'code': 204,
            'message': '删除同步配置成功',
            'data': {}
        })

    @action(detail=True, methods=['POST'])
    def sync_now(self, request, pk=None):
        """立即执行同步"""
        sync_config = self.get_object()
        
        # 检查特定配置是否启用
        if sync_config.sync_enabled:
            # 使用特定配置
            task = sync_interface_data.delay(sync_config.id, request.user.id)
            return Response({
                'status': 'success',
                'code': 200,
                'message': '同步任务已启动',
                'data': {
                    'task_id': task.id,
                    'config_id': sync_config.id,
                    'used_global_config': False
                }
            })
        else:
            # 检查是否有可用的全局配置
            global_config = GlobalSyncConfig.objects.filter(is_active=True, sync_enabled=True).first()
            if global_config:
                # 使用全局配置，但传递接口ID和步骤ID
                task = sync_interface_data.delay(
                    None, 
                    request.user.id,
                    interface_id=sync_config.interface_id,
                    step_id=sync_config.step_id
                )
                return Response({
                    'status': 'success',
                    'code': 200,
                    'message': '使用全局配置启动同步任务',
                    'data': {
                        'task_id': task.id,
                        'global_config_id': global_config.id,
                        'used_global_config': True
                    }
                })
            else:
                return Response({
                    'status': 'error',
                    'code': 400,
                    'message': '同步配置未启用且无可用的全局配置',
                    'errors': {
                        'sync_enabled': ['同步配置当前处于禁用状态'],
                        'global_config': ['未找到可用的全局配置']
                    }
                })

    @action(detail=False, methods=['POST'])
    def batch_sync(self, request):
        """批量同步"""
        config_ids = request.data.get('config_ids', [])
        interface_step_pairs = request.data.get('interface_step_pairs', [])
        
        # 如果既没有配置ID也没有接口-步骤对
        if not config_ids and not interface_step_pairs:
            # 检查是否有可用的全局配置
            global_config = GlobalSyncConfig.objects.filter(is_active=True, sync_enabled=True).first()
            if global_config:
                return Response({
                    'status': 'error',
                    'code': 400,
                    'message': '使用全局配置时需要提供接口和步骤信息',
                    'errors': {
                        'interface_step_pairs': ['请提供至少一组接口ID和步骤ID']
                    }
                })
            else:
                return Response({
                    'status': 'error',
                    'code': 400,
                    'message': '请选择要同步的配置或提供接口-步骤对',
                    'errors': {
                        'config_ids': ['请选择要同步的配置'],
                        'interface_step_pairs': ['或提供接口-步骤对'],
                        'global_config': ['未找到可用的全局配置']
                    }
                })

        # 启动批量异步任务
        task = batch_sync_interface_data.delay(config_ids, request.user.id, interface_step_pairs)
        
        return Response({
            'status': 'success',
            'code': 200,
            'message': '批量同步任务已启动',
            'data': {
                'task_id': task.id,
                'config_count': len(config_ids),
                'interface_step_pair_count': len(interface_step_pairs),
                'used_global_config': len(interface_step_pairs) > 0
            }
        })

class SyncHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """同步历史视图集"""
    queryset = SyncHistory.objects.all()
    serializer_class = SyncHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """获取同步历史列表，支持按配置、类型、状态、时间范围、项目和接口过滤"""
        queryset = super().get_queryset()
        
        # 支持按配置、类型、状态、时间范围过滤
        config_id = self.request.query_params.get('config_id')
        sync_type = self.request.query_params.get('sync_type')
        sync_status = self.request.query_params.get('sync_status')
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        project_id = self.request.query_params.get('project_id')
        interface_id = self.request.query_params.get('interface_id')

        if config_id:
            queryset = queryset.filter(sync_config_id=config_id)
        if sync_type:
            queryset = queryset.filter(sync_type=sync_type)
        if sync_status:
            queryset = queryset.filter(sync_status=sync_status)
        if start_time:
            queryset = queryset.filter(sync_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(sync_time__lte=end_time)
        if project_id:
            queryset = queryset.filter(sync_config__interface__project_id=project_id)
        if interface_id:
            queryset = queryset.filter(sync_config__interface_id=interface_id)

        return queryset

    def list(self, request, *args, **kwargs):
        """获取同步历史列表"""
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
                'status': 'success',
                'code': 200,
                'message': '获取同步历史列表成功',
                'data': data
            })
            
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取同步历史列表成功',
            'data': {
                'count': len(serializer.data),
                'next': None,
                'previous': None,
                'results': serializer.data
            }
        })

    def retrieve(self, request, *args, **kwargs):
        """获取同步历史详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取同步历史详情成功',
            'data': serializer.data
        })

    @action(detail=True, methods=['POST'])
    def rollback(self, request, pk=None):
        """回滚到指定的历史记录"""
        history = self.get_object()
        try:
            with transaction.atomic():
                # 获取步骤
                step = history.sync_config.step
                
                # 保存当前数据作为新的历史记录
                current_data = {
                    field: step.interface_data.get(field)
                    for field in history.sync_fields
                }
                
                # 回滚数据
                step.interface_data.update(history.old_data)
                step.last_sync_time = timezone.now()
                step.save()
                
                # 创建回滚的历史记录
                new_history = SyncHistory.objects.create(
                    sync_config=history.sync_config,
                    sync_type='rollback',
                    sync_status='success',
                    sync_fields=history.sync_fields,
                    old_data=current_data,
                    new_data=history.old_data,
                    operator=request.user
                )
                
                return Response({
                    'status': 'success',
                    'code': 200,
                    'message': '回滚成功',
                    'data': SyncHistorySerializer(new_history).data
                })
                
        except Exception as e:
            return Response({
                'status': 'error',
                'code': 500,
                'message': f'回滚失败: {str(e)}',
                'errors': {'detail': str(e)}
            })

class GlobalSyncConfigViewSet(viewsets.ModelViewSet):
    """全局同步配置视图集"""
    queryset = GlobalSyncConfig.objects.all()
    serializer_class = GlobalSyncConfigSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['sync_enabled', 'sync_mode', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['-updated_time']

    def get_queryset(self):
        """获取当前用户有权限的全局配置"""
        queryset = super().get_queryset()
        
        # 处理swagger文档生成的情况
        if getattr(self, 'swagger_fake_view', False):
            return queryset.none()
            
        # 按项目过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        # 如果不是超级用户，只能看到自己有权限的项目的配置
        user = self.request.user
        if not user.is_superuser:
            project_ids = user.joined_projects.values_list('id', flat=True)
            queryset = queryset.filter(project_id__in=project_ids)
            
        return queryset

    def list(self, request, *args, **kwargs):
        """获取配置列表，并标记当前生效的配置"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        # 按项目分组获取当前生效的配置ID
        active_configs = {}
        project_id = request.query_params.get('project_id')
        if project_id:
            # 如果指定了项目，只获取该项目的激活配置
            config = queryset.filter(
                project_id=project_id,
                is_active=True
            ).first()
            if config:
                active_configs[project_id] = config.id
        else:
            # 否则获取所有项目的激活配置
            for config in queryset.filter(is_active=True):
                active_configs[str(config.project_id)] = config.id
        
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取全局配置列表成功',
            'data': {
                'configs': serializer.data,
                'active_configs': active_configs
            }
        })

    @action(detail=True, methods=['POST'])
    def set_active(self, request, pk=None):
        """设置为当前生效的配置"""
        config = self.get_object()
        
        # 如果当前配置已经是激活状态，无需操作
        if config.is_active:
            return Response({
                'status': 'success',
                'code': 200,
                'message': '该配置已经是当前生效的配置',
                'data': self.get_serializer(config).data
            })
        
        with transaction.atomic():
            # 将同一项目下的其他配置设置为非激活
            GlobalSyncConfig.objects.filter(
                project=config.project
            ).exclude(id=config.id).update(is_active=False)
            # 设置当前配置为激活
            config.is_active = True
            config.save()
        
        return Response({
            'status': 'success',
            'code': 200,
            'message': '已将该配置设置为当前生效的配置',
            'data': self.get_serializer(config).data
        })

    @action(detail=False)
    def current_config(self, request):
        """获取当前生效的配置"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({
                'status': 'error',
                'code': 400,
                'message': '缺少project_id参数',
                'errors': {'project_id': ['该字段是必需的']}
            })
            
        config = GlobalSyncConfig.objects.filter(
            project_id=project_id,
            is_active=True
        ).first()
        
        if not config:
            return Response({
                'status': 'error',
                'code': 404,
                'message': '当前项目没有生效的全局配置',
                'data': {}
            })
            
        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取当前生效的配置成功',
            'data': self.get_serializer(config).data
        })

    def destroy(self, request, *args, **kwargs):
        """删除全局配置"""
        instance = self.get_object()
        
        # 检查用户是否有权限删除该配置
        user = self.request.user
        if not user.is_superuser and not user.joined_projects.filter(id=instance.project_id).exists():
            return Response({
                'status': 'error',
                'code': 403,
                'message': '您没有权限删除此配置',
                'errors': {'detail': ['您不是此项目的成员']}
            }, status=403)
        
        try:
            instance.delete()
            return Response({
                'status': 'success',
                'code': 204,
                'message': '删除全局配置成功',
                'data': {}
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'code': 500,
                'message': f'删除配置失败: {str(e)}',
                'errors': {'detail': [str(e)]}
            }, status=500)
