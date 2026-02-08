import os
import django
import pytest
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TestRunner.settings')
django.setup()

from django.contrib.auth import get_user_model
from projects.models import Project
from testcases.models import TestCase, TestCaseStep
from testcases.runner import TestCaseRunner

User = get_user_model()

@pytest.fixture
def setup_data():
    """创建测试数据"""
    # 创建用户
    user, _ = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com', 'is_staff': True}
    )

    # 使用现有项目
    project = Project.objects.first()
    if not project:
        raise ValueError('没有可用的项目，请先创建一个项目')

    # 确保用户是项目成员
    project.members.add(user)

    # 创建测试用例
    try:
        testcase = TestCase.objects.get(name='Test Case with SQL Hooks', project=project)
    except TestCase.DoesNotExist:
        testcase = TestCase.objects.create(
            name='Test Case with SQL Hooks',
            project=project,
            description='测试SQL钩子功能',
            priority='P2',
            created_by=user,
            config={
                'base_url': 'https://postman-echo.com',
                'verify': False,
                'variables': {
                    'var1': 'value1'
                }
            }
        )

    # 删除现有步骤
    TestCaseStep.objects.filter(testcase=testcase).delete()

    # 创建带SQL钩子的HTTP步骤
    http_step = TestCaseStep.objects.create(
        testcase=testcase,
        name='HTTP Step with SQL Hooks',
        order=1,
        interface_data={
            'type': 'http',
            'method': 'GET',
            'url': '/get',
            'headers': {'Content-Type': 'application/json'},
            'params': {'foo': 'bar'},
            'setup_hooks': [
                {
                    'type': 'sql',
                    'sql': 'SELECT * FROM users LIMIT 1',
                    'db_id': 1,
                    'var_name': 'user_data'
                }
            ],
            'teardown_hooks': [
                {
                    'type': 'sql',
                    'sql': 'UPDATE users SET last_login = NOW() WHERE id = 1',
                    'db_id': 1
                }
            ],
            'validators': [
                {'eq': ['status_code', 200]}
            ]
        }
    )

    # 创建SQL步骤
    sql_step = TestCaseStep.objects.create(
        testcase=testcase,
        name='SQL Step',
        order=2,
        interface_data={
            'type': 'sql',
            'sql_method': 'FETCHONE',
            'sql': 'SELECT * FROM users WHERE id = 1',
            'db_config': {
                'user': 'testuser',
                'password': 'testpass',
                'database': 'testdb',
                'ip': 'localhost',
                'port': 3306
            },
            'setup_hooks': [
                {'result_var': '${get_timestamp()}'}
            ],
            'validators': [
                {'ne': ['result', None]}
            ]
        }
    )

    return {
        'user': user,
        'project': project,
        'testcase': testcase,
        'http_step': http_step,
        'sql_step': sql_step
    }

def test_sql_hooks(setup_data):
    """测试SQL钩子功能"""
    testcase = setup_data['testcase']

    # 创建测试用例执行器
    runner = TestCaseRunner(testcase)

    # 检查步骤是否正确加载
    assert len(runner.teststeps) == 2, "应该有2个测试步骤"

    # 检查HTTP步骤的SQL钩子
    http_step = runner.teststeps[0]
    http_step_struct = http_step.struct()

    # 检查前置钩子
    assert len(http_step_struct.setup_hooks) == 1, "HTTP步骤应该有1个前置钩子"
    setup_hook = http_step_struct.setup_hooks[0]
    assert isinstance(setup_hook, dict), "前置钩子应该是字典类型"
    assert setup_hook.get('type') == 'sql', "前置钩子应该是SQL类型"
    assert 'sql' in setup_hook, "前置钩子应该包含SQL语句"

    # 检查后置钩子
    assert len(http_step_struct.teardown_hooks) == 1, "HTTP步骤应该有1个后置钩子"
    teardown_hook = http_step_struct.teardown_hooks[0]
    assert isinstance(teardown_hook, dict), "后置钩子应该是字典类型"
    assert teardown_hook.get('type') == 'sql', "后置钩子应该是SQL类型"
    assert 'sql' in teardown_hook, "后置钩子应该包含SQL语句"

    # 检查SQL步骤
    sql_step = runner.teststeps[1]
    sql_step_struct = sql_step.struct()

    # 检查SQL步骤类型
    assert sql_step.name() == "SQL Step", "SQL步骤名称应该正确"
    assert "sql" in sql_step.type(), "SQL步骤类型应该包含'sql'"

    # 检查SQL请求
    assert sql_step_struct.sql_request is not None, "SQL步骤应该有SQL请求"
    assert sql_step_struct.sql_request.method == "FETCHONE", "SQL方法应该是FETCHONE"
    assert "users" in sql_step_struct.sql_request.sql, "SQL语句应该包含表名"

    print("SQL钩子测试通过!")
