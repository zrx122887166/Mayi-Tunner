import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
django.setup()

# 导入Celery应用
from TestRunner.celery import app

# 导入测试任务
from testtasks.tasks import execute_task_async

if __name__ == '__main__':
    print("Celery配置信息:")
    print(f"消息代理URL: {app.conf.broker_url}")
    print(f"结果后端: {app.conf.result_backend}")
    print(f"接受的内容类型: {app.conf.accept_content}")
    print(f"任务序列化器: {app.conf.task_serializer}")
    print(f"结果序列化器: {app.conf.result_serializer}")
    print(f"时区: {app.conf.timezone}")
    print("\n已注册的任务:")
    for task_name in app.tasks:
        if not task_name.startswith('celery.'):
            print(f" - {task_name}") 