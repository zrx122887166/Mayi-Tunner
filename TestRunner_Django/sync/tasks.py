from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import SyncConfig, SyncHistory, GlobalSyncConfig
from .serializers import SyncHistorySerializer

User = get_user_model()

@shared_task
def sync_interface_data(config_id, user_id=None, interface_id=None, step_id=None):
    """异步执行同步任务"""
    try:
        # 获取同步配置
        config = SyncConfig.objects.filter(id=config_id).first()
        
        # 如果没有找到特定配置，尝试使用全局配置
        if not config:
            global_config = GlobalSyncConfig.objects.filter(is_active=True).first()
            if not global_config or not global_config.sync_enabled:
                return {
                    'status': 'error',
                    'code': 400,
                    'message': '未找到有效的同步配置',
                    'errors': {'config': ['未找到有效的同步配置']}
                }
            
            # 使用全局配置
            sync_enabled = global_config.sync_enabled
            sync_fields = global_config.sync_fields
            sync_mode = global_config.sync_mode
        else:
            # 使用特定配置
            sync_enabled = config.sync_enabled
            sync_fields = config.sync_fields
            sync_mode = config.sync_mode
            # 从配置中获取接口和步骤ID
            interface_id = config.interface_id
            step_id = config.step_id

        if not sync_enabled:
            return {
                'status': 'error',
                'code': 400,
                'message': '同步配置未启用',
                'errors': {'sync_enabled': ['同步配置当前处于禁用状态']}
            }

        # 检查接口ID和步骤ID是否存在
        if not interface_id or not step_id:
            return {
                'status': 'error',
                'code': 400,
                'message': '缺少接口ID或步骤ID',
                'errors': {
                    'interface_id': ['缺少接口ID'] if not interface_id else [],
                    'step_id': ['缺少步骤ID'] if not step_id else []
                }
            }

        with transaction.atomic():
            # 获取接口最新数据
            from interfaces.models import Interface
            from testcases.models import TestCaseStep
            
            try:
                interface = Interface.objects.get(id=interface_id)
            except Interface.DoesNotExist:
                return {
                    'status': 'error',
                    'code': 400,
                    'message': '未找到关联的接口',
                    'errors': {'interface': [f'ID为{interface_id}的接口不存在']}
                }

            interface_data = {
                'method': interface.method,
                'url': interface.url,
                'headers': interface.headers,
                'params': interface.params,
                'body': interface.body,
                'setup_hooks': interface.setup_hooks,
                'teardown_hooks': interface.teardown_hooks,
                'variables': interface.variables,
                'validators': interface.validators,
                'extract': interface.extract
            }

            # 获取要同步的字段数据
            sync_data = {
                field: interface_data[field]
                for field in sync_fields
                if field in interface_data
            }

            # 获取步骤当前数据
            try:
                step = TestCaseStep.objects.get(id=step_id)
            except TestCaseStep.DoesNotExist:
                return {
                    'status': 'error',
                    'code': 400,
                    'message': '未找到关联的测试步骤',
                    'errors': {'step': [f'ID为{step_id}的测试步骤不存在']}
                }

            old_data = {
                field: step.interface_data.get(field)
                for field in sync_fields
            }

            # 更新步骤数据
            step.interface_data.update(sync_data)
            step.last_sync_time = timezone.now()
            step.save()

            # 记录同步历史
            operator = User.objects.get(id=user_id) if user_id else None
            
            # 如果使用全局配置，尝试查找或创建对应的同步配置
            if not config:
                config, created = SyncConfig.objects.get_or_create(
                    interface_id=interface_id,
                    step_id=step_id,
                    defaults={
                        'name': f'自动创建的配置 - {interface.name}',
                        'testcase': step.testcase,
                        'sync_fields': sync_fields,
                        'sync_enabled': True,
                        'sync_mode': sync_mode,
                        'created_by': operator
                    }
                )
            
            history = SyncHistory.objects.create(
                sync_config=config,
                sync_type='async',
                sync_status='success',
                sync_fields=sync_fields,
                old_data=old_data,
                new_data=sync_data,
                operator=operator
            )

            return {
                'status': 'success',
                'code': 200,
                'message': '同步成功',
                'data': {
                    'config_id': config.id if config else None,
                    'history_id': history.id,
                    'used_global_config': config_id is None
                }
            }

    except Exception as e:
        return {
            'status': 'error',
            'code': 500,
            'message': f'同步失败: {str(e)}',
            'errors': {'detail': str(e)}
        }

@shared_task
def batch_sync_interface_data(config_ids, user_id=None, interface_step_pairs=None):
    """批量异步执行同步任务"""
    success_count = 0
    failed_count = 0
    results = []

    # 处理特定配置ID的同步
    if config_ids:
        for config_id in config_ids:
            result = sync_interface_data(config_id, user_id)
            if result['status'] == 'success':
                success_count += 1
            else:
                failed_count += 1
            results.append({
                'config_id': config_id,
                'result': result
            })
    
    # 处理使用全局配置的接口-步骤对
    if interface_step_pairs:
        for pair in interface_step_pairs:
            interface_id = pair.get('interface_id')
            step_id = pair.get('step_id')
            if interface_id and step_id:
                result = sync_interface_data(None, user_id, interface_id, step_id)
                if result['status'] == 'success':
                    success_count += 1
                else:
                    failed_count += 1
                results.append({
                    'interface_id': interface_id,
                    'step_id': step_id,
                    'result': result
                })

    return {
        'status': 'success',
        'code': 200,
        'message': f'批量同步完成: 成功{success_count}个, 失败{failed_count}个',
        'data': {
            'success_count': success_count,
            'failed_count': failed_count,
            'results': results
        }
    } 