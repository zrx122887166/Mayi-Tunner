import os
from celery import Celery
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量
project_root = Path(__file__).parent.parent
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file)

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')

# 创建Celery应用
app = Celery('TestRunner')

# 使用Django的settings.py配置Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动从所有已注册的Django应用中加载任务
app.autodiscover_tasks()

# Celery 配置优化
app.conf.update(
    # 任务结果后端 - 使用 Django DB
    result_backend='django-db',
    
    # 任务路由配置 - 暂时注释掉，让所有任务使用默认队列
    # task_routes={
    #     'performance.tasks.*': {'queue': 'performance'},
    # },
    
    # 任务序列化
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    
    # 任务时区
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务超时设置
    task_soft_time_limit=1800,  # 30分钟软超时
    task_time_limit=3600,       # 60分钟硬超时
    
    # 任务重试设置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # 结果过期时间
    result_expires=86400,  # 24小时
    
    # Worker 设置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    
    # 监控设置
    worker_send_task_events=True,
    task_send_sent_event=True,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """测试任务"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

# 启动时的调试信息
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """设置定期任务"""
    # 每小时清理过期结果
    from django.conf import settings
    if hasattr(settings, 'PERFORMANCE_CLEANUP_ENABLED') and settings.PERFORMANCE_CLEANUP_ENABLED:
        sender.add_periodic_task(
            3600.0,  # 60分钟
            cleanup_expired_results.s(),
            name='清理过期的性能测试结果'
        )

@app.task
def cleanup_expired_results():
    """清理过期的性能测试结果"""
    try:
        from performance.tasks import cleanup_old_results
        return cleanup_old_results.delay()
    except Exception as e:
        print(f"清理任务执行失败: {e}")
        return None 