import os
import django
import time
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
django.setup()

# 导入模型和任务
from django.contrib.auth import get_user_model
from projects.models import Project
from testcases.models import TestCase
from testtasks.models import TestTaskSuite, TestTaskExecution
from testtasks.services import TestTaskService, TestTaskExecutionService
from testtasks.tasks import execute_task_async

User = get_user_model()

def test_async_execution():
    """测试异步任务执行"""
    print(f"[{datetime.now()}] 开始测试异步任务执行...")
    
    # 获取用户（假设已有用户）
    try:
        user = User.objects.first()
        if not user:
            print("错误: 没有可用的用户，请先创建用户")
            return
    except Exception as e:
        print(f"获取用户时出错: {str(e)}")
        return
    
    # 获取项目（假设已有项目）
    try:
        project = Project.objects.first()
        if not project:
            print("错误: 没有可用的项目，请先创建项目")
            return
    except Exception as e:
        print(f"获取项目时出错: {str(e)}")
        return
    
    # 获取测试用例（假设已有测试用例）
    try:
        testcases = TestCase.objects.filter(project=project)[:2]
        if not testcases:
            print("错误: 没有可用的测试用例，请先创建测试用例")
            return
        testcase_ids = [tc.id for tc in testcases]
    except Exception as e:
        print(f"获取测试用例时出错: {str(e)}")
        return
    
    # 创建测试任务集
    try:
        task_suite_data = {
            'name': f'测试任务集-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'description': '用于测试异步任务执行',
            'priority': 'P2',
            'fail_fast': False,
            'project': project
        }
        task_suite = TestTaskService.create_task_suite(task_suite_data, user)
        print(f"[{datetime.now()}] 创建测试任务集成功: {task_suite.name} (ID={task_suite.id})")
    except Exception as e:
        print(f"创建测试任务集时出错: {str(e)}")
        return
    
    # 添加测试用例到任务集
    try:
        task_cases = TestTaskService.add_testcases(task_suite, testcase_ids)
        print(f"[{datetime.now()}] 添加测试用例到任务集成功: {len(task_cases)}个用例")
    except Exception as e:
        print(f"添加测试用例到任务集时出错: {str(e)}")
        return
    
    # 创建执行记录
    try:
        execution = TestTaskExecutionService.create_execution(task_suite, None, user)
        print(f"[{datetime.now()}] 创建执行记录成功: ID={execution.id}")
    except Exception as e:
        print(f"创建执行记录时出错: {str(e)}")
        return
    
    # 异步执行任务
    try:
        print(f"[{datetime.now()}] 开始异步执行任务...")
        task = execute_task_async.delay(execution.id)
        print(f"[{datetime.now()}] 任务已提交: task_id={task.id}")
        
        # 等待任务完成
        print(f"[{datetime.now()}] 等待任务完成...")
        while not task.ready():
            time.sleep(1)
            # 刷新执行记录
            execution.refresh_from_db()
            print(f"[{datetime.now()}] 任务状态: {execution.status}, 进度: {execution.success_count}/{execution.total_count}")
        
        # 获取任务结果
        result = task.get()
        print(f"[{datetime.now()}] 任务执行完成: result={result}")
        
        # 刷新执行记录
        execution.refresh_from_db()
        print(f"[{datetime.now()}] 最终状态: {execution.status}")
        print(f"[{datetime.now()}] 执行统计: 总数={execution.total_count}, 成功={execution.success_count}, 失败={execution.fail_count}, 错误={execution.error_count}")
        
    except Exception as e:
        print(f"执行任务时出错: {str(e)}")
        return

if __name__ == '__main__':
    test_async_execution() 