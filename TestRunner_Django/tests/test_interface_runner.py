import os
import django
import pytest

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project
from environments.models import Environment
from interfaces.models import Interface
from interfaces.utils import InterfaceRunner
from httprunner.models import TRequest

User = get_user_model()

@pytest.fixture
def setup_data():
    """准备测试数据"""
    # 清理可能存在的测试用户
    User.objects.filter(username='tester').delete()
    
    # 创建测试用户
    user = User.objects.create_user(
        username='tester',
        password='123456'
    )
    
    # 创建测试项目
    project = Project.objects.create(
        name='测试项目',
        description='用于测试接口功能',
        creator=user
    )
    project.members.add(user)
    
    # 创建测试环境
    environment = Environment.objects.create(
        name='测试环境',
        base_url='https://postman-echo.com',
        project=project,
        created_by=user
    )
    
    # 创建测试接口
    interface = Interface.objects.create(
        name='Echo GET',
        method='GET',
        url='/get',
        project=project,
        created_by=user,
        params={
            'foo': 'bar'
        },
        validators=[
            {
                'eq': ['status_code', 200]
            },
            {
                'eq': ['body.args.foo', 'bar']
            }
        ]
    )
    
    yield {
        'user': user,
        'project': project,
        'environment': environment,
        'interface': interface
    }
    
    # 清理测试数据
    interface.delete()
    environment.delete()
    project.delete()
    user.delete()

def test_interface_runner(setup_data):
    """测试接口运行器"""
    # 获取测试数据
    interface = setup_data['interface']
    environment = setup_data['environment']
    
    # 创建运行器
    runner = InterfaceRunner(interface, environment)
    
    # 运行测试
    runner = runner.run_interface()
    
    # 1. 验证测试步骤配置
    step = runner.teststeps[0]
    assert isinstance(step.request, TRequest), "请求对象类型正确"
    assert step.request.method == "GET", "请求方法正确"
    assert step.request.url == "/get", "请求URL正确"
    assert step.request.params == {"foo": "bar"}, "请求参数正确"
    
    # 2. 验证接口调用结果
    assert len(runner.teststeps) == 1, "测试步骤数量正确"
    
    # 3. 验证响应结果
    step = runner.teststeps[0]
    assert step.request.method == "GET", "请求方法正确"
    assert step.request.url == "/get", "请求URL正确"
    assert step.request.params == {"foo": "bar"}, "请求参数正确"