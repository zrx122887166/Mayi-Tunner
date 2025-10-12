import os
import django
import pytest

# 定义全局变量用于记录hook执行顺序
hook_execution = []

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project
from environments.models import Environment
from testcases.models import TestCase, TestCaseStep
from testcases.runner import TestCaseRunner
from functions.models import CustomFunction
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
        description='用于测试用例功能',
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
    
    # 创建测试用例
    testcase = TestCase.objects.create(
        name='Hooks测试',
        project=project,
        created_by=user,
        config={
            'base_url': 'https://postman-echo.com',
            'verify': False,
            'variables': {
                'post_data': {
                    'name': 'test_name',
                    'value': 'test_value'
                }
            }
        }
    )
    
    # 创建带hooks的测试步骤
    TestCaseStep.objects.create(
        name='带Hooks的POST请求',
        testcase=testcase,
        order=1,
        interface_data={
            'method': 'POST',
            'url': '/post',
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': '$post_data',
            'setup_hooks': [
                "${setup_hook_func($request)}"
            ],
            'teardown_hooks': [
                "${teardown_hook_func($response)}"
            ],
            'validators': [
                {
                    'eq': ['status_code', 200]
                },
                {
                    'eq': ['body.json.name', 'test_name']
                },
                {
                    'eq': ['body.json.value', 'test_value']
                }
            ],
            'extract': {
                'response_name': 'body.json.name',
                'response_value': 'body.json.value'
            },
            'export': ['response_name', 'response_value']
        }
    )
    
    # 创建自定义函数
    custom_function = CustomFunction.objects.create(
        name='test_hooks',
        code='''
def setup_hook_func(request):
    from tests.test_testcase_runner import hook_execution
    hook_execution.append("setup")
    request["headers"]["X-Test"] = "setup_hook_value"
    return request

def teardown_hook_func(response):
    from tests.test_testcase_runner import hook_execution
    hook_execution.append("teardown")
    return response
        ''',
        project=project,
        created_by=user,
        is_active=True
    )
    
    # 创建自定义函数
    custom_function = CustomFunction.objects.create(
        name='test_function',
        code='''
def get_test_value():
    return "test_value"
        ''',
        project=project,
        created_by=user,
        is_active=True
    )
    
    # 获取所有步骤
    steps = list(testcase.steps.all().order_by('order'))
    
    yield {
        'user': user,
        'project': project,
        'environment': environment,
        'testcase': testcase,
        'steps': steps,
        'custom_function': custom_function
    }
    
    # 清理测试数据
    custom_function.delete()
    TestCaseStep.objects.filter(testcase=testcase).delete()
    testcase.delete()
    environment.delete()
    project.delete()
    user.delete()
def test_basic_get_request(setup_data):
    """测试hooks功能"""
    # 清空hook执行记录
    global hook_execution
    hook_execution.clear()
    
    testcase = setup_data['testcase']
    runner = TestCaseRunner(testcase)
    runner = TestCaseRunner(testcase)
    
    # 验证配置加载
    assert runner.config.name == testcase.name, "用例名称正确"
    assert runner.base_url == "https://postman-echo.com", "base_url正确"
    assert runner.verify is False, "verify配置正确"
    
    # 执行测试
    runner = runner.run_testcase()
    
    # 验证结果
    summary = runner.get_summary()
    assert summary["success"] is True, "测试执行成功"
    
    # 验证POST请求结果
    step_result = summary["step_results"][0]
    assert step_result["success"] is True, "POST请求执行成功"
    assert step_result["data"]["response"]["status_code"] == 200, "响应状态码正确"
    
    # 验证setup_hook执行结果
    request_data = step_result["data"]["request"]
    assert request_data["method"] == "POST", "请求方法正确"
    assert request_data["headers"]["Content-Type"] == "application/json", "Content-Type正确"
    assert request_data["headers"]["X-Test"] == "setup_hook_value", "setup_hook正确执行"
    assert request_data["body"]["name"] == "test_name", "请求体name字段正确"
    assert request_data["body"]["value"] == "test_value", "请求体value字段正确"
    
    # 验证teardown_hook执行结果
    response_data = step_result["data"]["response"]
    # 验证hooks执行顺序
    assert hook_execution == ["setup", "teardown"], "hooks执行顺序正确"
    assert response_data["body"]["json"]["name"] == "test_name", "响应中的name字段正确"
    assert response_data["body"]["json"]["value"] == "test_value", "响应中的value字段正确"
    
    # 验证变量提取
    extracted_vars = step_result["data"]["extracted_variables"]
    assert "response_name" in extracted_vars, "成功提取response_name变量"
    assert extracted_vars["response_name"] == "test_name", "提取的response_name值正确"
    assert "response_value" in extracted_vars, "成功提取response_value变量"
    assert extracted_vars["response_value"] == "test_value", "提取的response_value值正确"
    
    # 验证统计信息
    assert step_result["elapsed"] > 0, "记录了执行时间"
    assert step_result["data"]["response"]["response_time_ms"] > 0, "记录了响应时间"
    assert len(str(step_result["data"]["response"]["body"])) > 0, "响应体不为空"
    
    # 验证导出变量
    export_vars = summary["in_out"]["export_vars"]
    assert "response_name" in export_vars, "response_name变量被导出"
    assert "response_value" in export_vars, "response_value变量被导出"