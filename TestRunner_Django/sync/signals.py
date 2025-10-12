from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from interfaces.models import Interface
from .models import SyncConfig, SyncHistory
from .tasks import sync_interface_data

@receiver(post_save, sender=Interface)
def handle_interface_update(sender, instance, created, **kwargs):
    """处理接口更新时的自动同步"""
    if created:  # 新创建的接口不需要同步
        return
    
    # 获取所有关联到这个接口且启用了自动同步的配置
    sync_configs = SyncConfig.objects.filter(
        interface=instance,
        sync_enabled=True,
        sync_mode='auto'
    ).select_related('step')
    
    # 使用异步任务执行同步
    for config in sync_configs:
        try:
            # 检查触发条件
            trigger = config.sync_trigger or {}
            fields_to_watch = trigger.get('fields_to_watch', [])
            
            # 如果没有指定要监视的字段，则认为所有字段都需要监视
            if not fields_to_watch:
                fields_to_watch = config.sync_fields
            
            # 获取步骤当前数据
            step = config.step
            old_data = {
                field: step.interface_data.get(field)
                for field in config.sync_fields
            }
            
            # 获取接口数据
            interface_data = {
                'method': instance.method,
                'url': instance.url,
                'headers': instance.headers,
                'params': instance.params,
                'body': instance.body,
                'setup_hooks': instance.setup_hooks,
                'teardown_hooks': instance.teardown_hooks,
                'variables': instance.variables,
                'validators': instance.validators,
                'extract': instance.extract
            }
            
            # 检查是否有变化
            has_changes = any(
                old_data.get(field) != interface_data.get(field)
                for field in fields_to_watch
            )
            
            if has_changes:
                # 使用异步任务执行同步
                sync_interface_data.delay(config.id)
        
        except Exception as e:
            # 记录同步失败
            SyncHistory.objects.create(
                sync_config=config,
                sync_type='auto',
                sync_status='failed',
                sync_fields=config.sync_fields,
                old_data={},
                new_data={},
                error_message=str(e),
                operator=None
            ) 