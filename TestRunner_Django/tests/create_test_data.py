import os
import django
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
django.setup()

# 导入模型
from django.contrib.auth import get_user_model
from projects.models import Project
from environments.models import Environment
from interfaces.models import Interface
from testcases.models import TestCase, TestCaseStep

User = get_user_model()

def create_test_data():
    """创建测试数据"""
    print(f"[{datetime.now()}] 开始创建测试数据...")
    
    # 创建用户
    try:
        username = 'testuser'
        email = 'testuser@example.com'
        password = 'password123'
        
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'is_staff': True
            }
        )
        
        if created:
            user.set_password(password)
            user.save()
            print(f"[{datetime.now()}] 创建用户成功: {username}")
        else:
            print(f"[{datetime.now()}] 用户已存在: {username}")
    except Exception as e:
        print(f"创建用户时出错: {str(e)}")
        return
    
    # 创建项目
    try:
        project_name = 'Test Project'
        project, created = Project.objects.get_or_create(
            name=project_name,
            defaults={
                'description': '用于测试的项目',
                'creator': user
            }
        )
        
        if created:
            print(f"[{datetime.now()}] 创建项目成功: {project_name}")
        else:
            print(f"[{datetime.now()}] 项目已存在: {project_name}")
    except Exception as e:
        print(f"创建项目时出错: {str(e)}")
        return
    
    # 创建环境
    try:
        env_name = 'Test Environment'
        environment, created = Environment.objects.get_or_create(
            name=env_name,
            project=project,
            defaults={
                'base_url': 'http://example.com',
                'description': '用于测试的环境',
                'created_by': user
            }
        )
        
        if created:
            print(f"[{datetime.now()}] 创建环境成功: {env_name}")
            
            # 创建环境变量
            from environments.models import EnvironmentVariable
            EnvironmentVariable.objects.create(
                environment=environment,
                name='var1',
                value='value1',
                type='string',
                description='测试变量1'
            )
            EnvironmentVariable.objects.create(
                environment=environment,
                name='var2',
                value='value2',
                type='string',
                description='测试变量2'
            )
            print(f"[{datetime.now()}] 创建环境变量成功")
        else:
            print(f"[{datetime.now()}] 环境已存在: {env_name}")
    except Exception as e:
        print(f"创建环境时出错: {str(e)}")
        return
    
    # 创建接口
    try:
        interface_name = 'Test Interface'
        interface, created = Interface.objects.get_or_create(
            name=interface_name,
            project=project,
            defaults={
                'url': '/api/test',
                'method': 'GET',
                'created_by': user
            }
        )
        
        if created:
            print(f"[{datetime.now()}] 创建接口成功: {interface_name}")
        else:
            print(f"[{datetime.now()}] 接口已存在: {interface_name}")
    except Exception as e:
        print(f"创建接口时出错: {str(e)}")
        return
    
    # 创建测试用例
    try:
        for i in range(1, 3):
            case_name = f'Test Case {i}'
            testcase, created = TestCase.objects.get_or_create(
                name=case_name,
                project=project,
                defaults={
                    'description': f'用于测试的用例 {i}',
                    'priority': 'P2',
                    'created_by': user
                }
            )
            
            if created:
                print(f"[{datetime.now()}] 创建测试用例成功: {case_name}")
                
                # 创建测试步骤
                step = TestCaseStep.objects.create(
                    testcase=testcase,
                    name=f'Step 1 for {case_name}',
                    origin_interface=interface,
                    interface_data={
                        'method': 'GET',
                        'url': '/api/test',
                        'headers': {"Content-Type": "application/json"},
                        'params': {"param1": "value1"},
                        'body': {},
                        'validators': [{"type": "status_code", "expected": 200}],
                        'extract': {},
                        'setup_hooks': [],
                        'teardown_hooks': [],
                        'variables': {}
                    },
                    order=1
                )
                print(f"[{datetime.now()}] 创建测试步骤成功: {step.name}")
            else:
                print(f"[{datetime.now()}] 测试用例已存在: {case_name}")
    except Exception as e:
        print(f"创建测试用例时出错: {str(e)}")
        return
    
    print(f"[{datetime.now()}] 测试数据创建完成!")

if __name__ == '__main__':
    create_test_data() 