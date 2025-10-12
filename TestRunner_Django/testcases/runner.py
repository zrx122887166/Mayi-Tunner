from typing import Dict, List, Optional, Text
import json
import logging
import types
from httprunner import HttpRunner, Config, Step, RunRequest, RunSqlRequest
from httprunner.models import TestCaseSummary
from httprunner.step_sql_request import SqlMethodEnum
from .models import TestCase, TestCaseStep

logger = logging.getLogger('testrunner')

def load_custom_functions(project_id):
    """加载项目的自定义函数"""
    functions = {}
    loaded_count = 0
    error_count = 0

    try:
        from functions.models import CustomFunction
        custom_functions = CustomFunction.objects.filter(
            project_id=project_id,
            is_active=True
        ).select_related('project')

        project_name = custom_functions[0].project.name if custom_functions else "Unknown"
        logger.info(f"开始加载项目[{project_name}]的自定义函数")

        for func in custom_functions:
            try:
                # 创建模块对象
                module = types.ModuleType(func.name)

                # 编译函数代码
                code = compile(func.code, func.name, 'exec')

                # 执行代码,将函数加载到模块中
                exec(code, module.__dict__)

                # 获取模块中定义的所有函数
                module_functions = {
                    name: obj for name, obj in module.__dict__.items()
                    if isinstance(obj, types.FunctionType)
                }

                if not module_functions:
                    logger.warning(f"函数[{func.name}]没有定义任何可调用的函数")
                    error_count += 1
                    continue

                # 检查函数名冲突
                for name in module_functions:
                    if name in functions:
                        logger.warning(f"函数名冲突: {name}, 将使用最新定义的函数")

                functions.update(module_functions)
                loaded_count += 1
                logger.debug(f"成功加载函数: {func.name}, 包含方法: {list(module_functions.keys())}")

            except SyntaxError as e:
                logger.error(f"函数[{func.name}]语法错误: {str(e)}")
                error_count += 1
            except Exception as e:
                logger.error(f"加载函数[{func.name}]失败: {str(e)}")
                error_count += 1

        logger.info(f"项目[{project_name}]函数加载完成: 成功{loaded_count}个, 失败{error_count}个")

    except Exception as e:
        logger.error(f"加载项目[{project_id}]的自定义函数时发生错误: {str(e)}")

    return functions

class TestCaseRunner(HttpRunner):
    """测试用例执行器"""

    def _create_http_step(self, step_name: str, interface_data: Dict) -> RunRequest:
        """创建HTTP请求步骤

        Args:
            step_name: 步骤名称
            interface_data: 接口数据

        Returns:
            RunRequest: HTTP请求步骤对象
        """
        step_obj = RunRequest(step_name)

        # 设置请求方法和URL
        method = interface_data['method'].lower()
        url = interface_data['url']
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"

        # 添加setup hooks
        if interface_data.get('setup_hooks'):
            for hook in interface_data['setup_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，直接添加
                    step_obj = step_obj.setup_hook(hook)
                    logger.debug(f"添加SQL类型的前置钩子: {hook}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型hook
                        step_obj = step_obj.setup_hook(hook)
                        logger.debug(f"添加带变量名的SQL类型前置钩子: {hook}")
                    else:
                        # 普通hook
                        step_obj = step_obj.setup_hook(hook)
                else:
                    # 字符串类型hook或其他格式
                    step_obj = step_obj.setup_hook(hook)

        # 执行HTTP方法
        step_obj = getattr(step_obj, method)(url)

        # 添加teardown hooks
        if interface_data.get('teardown_hooks'):
            for hook in interface_data['teardown_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，直接添加
                    step_obj = step_obj.teardown_hook(hook)
                    logger.debug(f"添加SQL类型的后置钩子: {hook}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型钩子
                        step_obj = step_obj.teardown_hook(hook)
                        logger.debug(f"添加带变量名的SQL类型后置钩子: {hook}")
                    else:
                        # 普通hook
                        step_obj = step_obj.teardown_hook(hook)
                else:
                    # 字符串类型hook或其他格式
                    step_obj = step_obj.teardown_hook(hook)

        return step_obj

    def _create_sql_step(self, step_name: str, interface_data: Dict) -> RunSqlRequest:
        """创建SQL请求步骤

        Args:
            step_name: 步骤名称
            interface_data: 接口数据

        Returns:
            RunSqlRequest: SQL请求步骤对象
        """
        step_obj = RunSqlRequest(step_name)

        # 设置数据库配置
        if interface_data.get('db_config'):
            db_config = interface_data['db_config']
            step_obj = step_obj.with_db_config(
                user=db_config.get('user'),
                password=db_config.get('password'),
                ip=db_config.get('ip'),
                port=db_config.get('port'),
                database=db_config.get('database'),
                psm=db_config.get('psm')
            )

        # 添加setup hooks
        if interface_data.get('setup_hooks'):
            for hook in interface_data['setup_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，直接添加
                    step_obj = step_obj.setup_hook(hook)
                    logger.debug(f"添加SQL类型的前置钩子: {hook}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型hook
                        step_obj = step_obj.setup_hook(hook)
                        logger.debug(f"添加带变量名的SQL类型前置钩子: {hook}")
                    else:
                        # 普通hook
                        step_obj = step_obj.setup_hook(hook)
                else:
                    # 字符串类型hook或其他格式
                    step_obj = step_obj.setup_hook(hook)

        # 执行SQL方法
        sql_method = interface_data.get('sql_method', 'fetchone').upper()
        sql = interface_data.get('sql', '')

        if sql_method == 'FETCHONE':
            step_obj = step_obj.fetchone(sql)
        elif sql_method == 'FETCHMANY':
            size = interface_data.get('sql_size', 10)
            step_obj = step_obj.fetchmany(sql, size)
        elif sql_method == 'FETCHALL':
            step_obj = step_obj.fetchall(sql)
        elif sql_method == 'INSERT':
            step_obj = step_obj.insert(sql)
        elif sql_method == 'UPDATE':
            step_obj = step_obj.update(sql)
        elif sql_method == 'DELETE':
            step_obj = step_obj.delete(sql)
        else:
            logger.warning(f"不支持的SQL方法: {sql_method}，将使用fetchone")
            step_obj = step_obj.fetchone(sql)

        # 添加teardown hooks
        if interface_data.get('teardown_hooks'):
            for hook in interface_data['teardown_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，直接添加
                    step_obj = step_obj.teardown_hook(hook)
                    logger.debug(f"添加SQL类型的后置钩子: {hook}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型钩子
                        step_obj = step_obj.teardown_hook(hook)
                        logger.debug(f"添加带变量名的SQL类型后置钩子: {hook}")
                    else:
                        # 普通hook
                        step_obj = step_obj.teardown_hook(hook)
                else:
                    # 字符串类型hook或其他格式
                    step_obj = step_obj.teardown_hook(hook)

        return step_obj

    def __init__(self, testcase: TestCase):
        # 先初始化父类
        super().__init__()
        self.testcase = testcase
        # 初始化测试步骤列表
        self.teststeps = []

        # 加载并注册自定义函数
        try:
            custom_functions = load_custom_functions(testcase.project_id)
            if custom_functions:
                # 注册到HttpRunner的functions中
                self.functions = custom_functions
                # 同时注册到parser中
                from httprunner.parser import Parser
                self.parser = Parser(functions_mapping=custom_functions)
                logger.info(f"用例[{testcase.name}]已加载项目自定义函数: {list(custom_functions.keys())}")
            else:
                logger.warning(f"项目[{testcase.project.name}]没有可用的自定义函数")
        except Exception as e:
            logger.error(f"加载项目[{testcase.project.name}]自定义函数失败: {str(e)}")

        # 构建配置
        logger.info(f"用例[{testcase.name}]配置信息: {testcase.config}, 类型: {type(testcase.config)}")

        try:
            self.config = Config(self.testcase.name)
            logger.debug(f"用例[{testcase.name}]创建Config对象成功")

            # 处理 config 字段，确保它是字典类型
            if isinstance(testcase.config, str):
                # 如果 config 是字符串，尝试解析为 JSON
                try:
                    import json
                    testcase.config = json.loads(testcase.config)
                    logger.info(f"用例[{testcase.name}]的config从字符串解析为字典: {testcase.config}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"用例[{testcase.name}]的config字符串无法解析为JSON: {e}")
                    testcase.config = {}
            elif not isinstance(testcase.config, dict):
                logger.error(f"用例[{testcase.name}]的config不是字典类型: {type(testcase.config)}")
                testcase.config = {}

            self.base_url = self.testcase.config.get('base_url', '')
            self.verify = self.testcase.config.get('verify', None)
            # 确保 variables 是字典类型
            variables = self.testcase.config.get('variables', {})
            if isinstance(variables, str):
                # 如果 variables 是字符串，尝试解析为 JSON
                try:
                    import json
                    variables = json.loads(variables)
                    logger.info(f"用例[{testcase.name}]的variables从字符串解析为字典: {variables}")
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"用例[{testcase.name}]的variables字符串无法解析为JSON: {e}")
                    variables = {}
            elif not isinstance(variables, dict):
                logger.warning(f"用例[{testcase.name}]的variables不是字典类型: {type(variables)}, 使用空字典")
                variables = {}
            self.variables = variables

            # 设置配置
            if self.base_url:
                self.config.base_url(self.base_url)
            if self.verify is not None:  # 只有在明确设置时才配置verify
                self.config.verify(self.verify)
            # 只有当 variables 是非空字典时才配置
            if self.variables and isinstance(self.variables, dict):
                self.config.variables(**self.variables)

            logger.info(f"用例[{testcase.name}]配置解析结果: base_url={self.base_url}, "
                       f"verify={self.verify}, variables={self.variables}")
        except Exception as e:
            logger.error(f"用例[{testcase.name}]配置初始化失败: {str(e)}")
            raise

        # 构建测试步骤
        steps = []
        for step in self.testcase.steps.all().order_by('order'):
            interface_data = step.interface_data

            # 确定步骤类型（HTTP或SQL）
            step_type = interface_data.get('type', 'http').lower()

            if step_type == 'sql':
                # 创建SQL请求步骤
                step_obj = self._create_sql_step(step.name, interface_data)
            else:
                # 创建HTTP请求步骤
                step_obj = self._create_http_step(step.name, interface_data)

            # 注意：后置钩子已经在_create_http_step和_create_sql_step方法中添加

            # 对于HTTP请求，添加请求参数
            if step_type != 'sql' and interface_data.get('params'):
                # 处理变量替换
                params = {}
                # 确保 self.variables 是字典类型
                if not isinstance(self.variables, dict):
                    logger.warning(f"步骤[{step.name}]的variables不是字典类型，无法进行变量替换")
                    self.variables = {}
                
                for k, v in interface_data['params'].items():
                    if isinstance(v, str) and v.startswith('$'):
                        var_name = v[1:]
                        if var_name in self.variables:
                            params[k] = self.variables[var_name]
                        else:
                            params[k] = v
                    else:
                        params[k] = v
                step_obj = step_obj.with_params(**params)

            # 对于HTTP请求，添加请求头 - 增强健壮性处理多种格式
            if step_type != 'sql':
                try:
                    headers = interface_data.get('headers')
                    if headers:
                        headers_dict = {}
                        # 1. 处理字典格式的headers
                        if isinstance(headers, dict):
                            logger.debug(f"步骤[{step.name}]使用字典格式headers: {headers}")
                            headers_dict = headers
                        # 2. 处理列表格式的headers
                        elif isinstance(headers, list):
                            logger.debug(f"步骤[{step.name}]使用列表格式headers: {headers}")
                            for header in headers:
                                if isinstance(header, dict) and header.get('enabled', True):
                                    headers_dict[header['key']] = header['value']
                                    logger.debug(f"添加header: {header['key']}={header['value']}")
                                elif isinstance(header, dict):
                                    logger.debug(f"跳过禁用的header: {header}")
                                else:
                                    logger.warning(f"未知的header格式: {header}, 类型: {type(header)}")
                        # 3. 其他未知格式尝试转换
                        elif headers:
                            logger.warning(f"步骤[{step.name}]的headers格式未知: {type(headers)}, 值: {headers}")
                            try:
                                # 尝试使用JSON解析
                                if isinstance(headers, str):
                                    logger.debug(f"尝试将字符串headers解析为JSON: {headers}")
                                    parsed_headers = json.loads(headers)
                                    if isinstance(parsed_headers, dict):
                                        logger.debug(f"成功将headers解析为字典: {parsed_headers}")
                                        headers_dict = parsed_headers
                                    elif isinstance(parsed_headers, list):
                                        logger.debug(f"成功将headers解析为列表: {parsed_headers}")
                                        for header in parsed_headers:
                                            if isinstance(header, dict) and header.get('enabled', True):
                                                headers_dict[header['key']] = header['value']
                                                logger.debug(f"添加header: {header['key']}={header['value']}")
                            except Exception as e:
                                logger.error(f"步骤[{step.name}]解析headers失败: {str(e)}")

                        # 应用headers
                        if headers_dict:
                            logger.debug(f"步骤[{step.name}]最终应用的headers: {headers_dict}")
                            step_obj = step_obj.with_headers(**headers_dict)
                        else:
                            logger.warning(f"步骤[{step.name}]的headers解析后为空，不会应用任何headers")
                    else:
                        logger.debug(f"步骤[{step.name}]没有定义headers")
                except Exception as e:
                    logger.error(f"处理步骤[{step.name}]的headers时发生错误: {str(e)}", exc_info=True)
                    # 即使处理header出错，也继续执行其他步骤

            # 对于HTTP请求，添加请求体
            if step_type != 'sql' and interface_data.get('body'):
                body = interface_data['body']
                # 确保 self.variables 是字典类型
                if isinstance(body, str) and body.startswith('$'):
                    var_name = body[1:]
                    if isinstance(self.variables, dict) and var_name in self.variables:
                        body = self.variables[var_name]

                # 如果body是字典且包含type和content字段，说明是RAW格式
                if isinstance(body, dict) and 'type' in body and 'content' in body:
                    if body['type'] == 'raw':
                        content = body['content']
                        if isinstance(content, str):
                            try:
                                # 如果content是字符串，尝试解析为JSON对象
                                body = json.loads(content)
                            except json.JSONDecodeError:
                                logger.error(f"解析请求体失败: {content}")
                                body = content
                        else:
                            # 如果content已经是字典类型，直接使用
                            body = content

                step_obj = step_obj.with_json(body)

            # 设置需要导出的变量
            if interface_data.get('export'):
                step_obj.struct().export = interface_data['export']

            # 添加变量提取器
            if interface_data.get('extract'):
                step_obj = step_obj.extract()
                for var_name, expr in interface_data['extract'].items():
                    step_obj = step_obj.with_jmespath(expr, var_name)

            # 创建Step对象
            step = Step(step_obj)

            # 添加验证器
            if interface_data.get('validators'):
                step_obj = step_obj.validate()
                for validator in interface_data['validators']:
                    if isinstance(validator, dict):
                        if "check" in validator and "expect" in validator:
                            # 格式1: {"check": "status_code", "expect": 200}
                            step_obj = step_obj.assert_equal(validator["check"], validator["expect"])
                        elif "eq" in validator:
                            # 格式2: {"eq": ["status_code", 200]}
                            check_value = validator["eq"][0]
                            expect_value = validator["eq"][1]
                            step_obj = step_obj.assert_equal(check_value, expect_value)
                        elif len(validator) == 1:
                            # 格式3: {"comparator_name": [check_item, expected_value]}
                            comparator = list(validator.keys())[0]
                            check_item, expected_value = validator[comparator]

                            if comparator == "eq":
                                step_obj = step_obj.assert_equal(check_item, expected_value)
                            elif comparator == "lt":
                                step_obj = step_obj.assert_less_than(check_item, expected_value)
                            elif comparator == "le":
                                step_obj = step_obj.assert_less_or_equals(check_item, expected_value)
                            elif comparator == "gt":
                                step_obj = step_obj.assert_greater_than(check_item, expected_value)
                            elif comparator == "ge":
                                step_obj = step_obj.assert_greater_or_equals(check_item, expected_value)
                            elif comparator == "ne":
                                step_obj = step_obj.assert_not_equal(check_item, expected_value)
                            elif comparator == "str_eq":
                                step_obj = step_obj.assert_string_equals(check_item, expected_value)
                            elif comparator == "contains":
                                step_obj = step_obj.assert_contains(check_item, expected_value)
                            elif comparator == "contained_by":
                                step_obj = step_obj.assert_contained_by(check_item, expected_value)
                            elif comparator == "type_match":
                                step_obj = step_obj.assert_type_match(check_item, expected_value)
                            elif comparator == "regex_match":
                                step_obj = step_obj.assert_regex_match(check_item, expected_value)
                            else:
                                logger.warning(f"不支持的比较器: {comparator}")
                    else:
                        logger.warning(f"不支持的验证器格式: {validator}")

            # 添加到步骤列表
            self.teststeps.append(step)

    def run_testcase(self, environment: Optional[Dict] = None) -> "TestCaseRunner":
        """执行测试用例

        Args:
            environment: 环境配置，包含base_url和variables

        Returns:
            TestCaseRunner: 返回自身，便于链式调用
        """
        logger.info(f"开始执行测试用例: {self.testcase.name}")

        if environment:
            # 使用环境的base_url
            if environment.get('base_url'):
                self.config.base_url(environment['base_url'])
                logger.info(f"使用环境base_url: {environment['base_url']}")

            # 使用环境的变量，与用例变量合并
            if environment.get('variables'):
                # 将环境变量更新到用例变量中
                env_variables = environment.get('variables', {})
                # 确保环境变量是字典类型
                if not isinstance(env_variables, dict):
                    logger.warning(f"环境变量不是字典类型: {type(env_variables)}, 使用空字典")
                    env_variables = {}
                # 确保用例变量是字典类型
                if not isinstance(self.variables, dict):
                    logger.warning(f"用例变量不是字典类型: {type(self.variables)}, 使用空字典")
                    self.variables = {}
                case_variables = self.variables.copy()
                # 环境变量优先级高于用例变量
                case_variables.update(env_variables)
                self.config.variables(**case_variables)
                logger.info(f"合并环境变量: {env_variables}")
                logger.debug(f"最终变量: {case_variables}")

        # 全局请求头处理
        try:
            from environments.models import GlobalRequestHeader
            if self.testcase.project_id:
                global_headers = GlobalRequestHeader.objects.filter(
                    project_id=self.testcase.project_id,
                    is_enabled=True
                )

                # 处理每个全局请求头
                for header in global_headers:
                    header_name = header.name
                    header_value = header.value

                    # 处理变量引用 - 支持两种格式：${var}和$var
                    try:
                        if header_value.startswith('${') and header_value.endswith('}'):
                            # ${var} 格式
                            var_name = header_value[2:-1]
                            if var_name in case_variables:
                                header_value = case_variables[var_name]
                            else:
                                logger.warning(f"全局请求头 '{header_name}' 引用的变量 '${var_name}' 在当前环境中不存在，将使用原始值")
                        elif header_value.startswith('$') and len(header_value) > 1:
                            # $var 格式
                            var_name = header_value[1:]
                            if var_name in case_variables:
                                header_value = case_variables[var_name]
                            else:
                                logger.warning(f"全局请求头 '{header_name}' 引用的变量 '${var_name}' 在当前环境中不存在，将使用原始值")
                    except Exception as ve:
                        logger.warning(f"处理全局请求头 '{header_name}' 的变量引用时出错: {str(ve)}")

                    # 应用全局请求头到测试步骤
                    for step in self.testcase.steps.all().order_by('order'):
                        interface_data = step.interface_data
                        # 确保headers字段存在
                        if 'headers' not in interface_data:
                            interface_data['headers'] = {}

                        # 只有当接口没有定义该请求头时才添加全局请求头（接口优先）
                        headers_dict = interface_data['headers']
                        if isinstance(headers_dict, dict) and header_name not in headers_dict:
                            headers_dict[header_name] = header_value
                            logger.info(f"为步骤 '{step.name}' 添加全局请求头: {header_name}={header_value}")
                        elif not isinstance(headers_dict, dict):
                            logger.warning(f"步骤 '{step.name}' 的headers不是字典类型，无法添加全局请求头")
        except Exception as e:
            logger.error(f"应用全局请求头时出错: {str(e)}")
            # 继续执行，不中断测试

        # 执行测试
        try:
            self.test_start()
            logger.info(f"测试用例执行完成: {self.testcase.name}")
        except Exception as e:
            logger.error(f"测试用例执行异常: {str(e)}")
            raise

        return self

    def get_step_results(self) -> List[Dict]:
        """获取步骤执行结果"""
        summary = super().get_summary()
        results = []

        for step_result in summary.step_results:
            # 检查步骤类型
            step_type = step_result.step_type

            # 检查验证器结果和响应状态码
            success = step_result.success

            # 检查验证器结果，如果有任何断言失败，则将步骤标记为失败
            if hasattr(step_result.data, 'validators') and step_result.data.validators:
                # 检查验证器的整体成功状态
                if 'success' in step_result.data.validators and step_result.data.validators['success'] is False:
                    success = False
                # 检查每个验证器的结果
                if 'validate_extractor' in step_result.data.validators:
                    for validator in step_result.data.validators['validate_extractor']:
                        if validator.get('check_result') == 'fail':
                            success = False
                            break

            # 初始化结果字典
            result = {
                'name': step_result.name,
                'success': success,
                'elapsed': step_result.elapsed,
                'step_type': step_type,
                'data': {
                    'extracted_variables': step_result.export_vars,
                    'validators': getattr(step_result.data, 'validators', {})
                },
                'attachment': step_result.attachment
            }

            # 根据步骤类型处理不同的数据
            if step_type == 'request':
                # HTTP请求类型
                req_resp = step_result.data.req_resps[-1] if step_result.data.req_resps else None

                # 检查响应状态码
                if req_resp and req_resp.response.status_code >= 400:
                    result['success'] = False

                # 添加HTTP特有的数据
                result['data'].update({
                    'request': {
                        'method': req_resp.request.method if req_resp else None,
                        'url': req_resp.request.url if req_resp else None,
                        'headers': req_resp.request.headers if req_resp else {},
                        'body': req_resp.request.body if req_resp else None
                    },
                    'response': {
                        'status_code': req_resp.response.status_code if req_resp else None,
                        'headers': req_resp.response.headers if req_resp else {},
                        'body': req_resp.response.body if req_resp else None,
                        'content_size': step_result.data.stat.content_size,
                        'response_time_ms': step_result.data.stat.response_time_ms,
                    }
                })
            elif step_type == 'sql':
                # SQL请求类型
                # 尝试获取SQL结果
                sql_result = None
                if hasattr(step_result.data, 'sql_response'):
                    sql_result = step_result.data.sql_response

                # 添加SQL特有的数据
                result['data'].update({
                    'sql_request': {
                        'sql': getattr(step_result.data, 'sql', None),
                        'method': getattr(step_result.data, 'method', None),
                        'db_config': getattr(step_result.data, 'db_config', {})
                    },
                    'sql_response': sql_result
                })

            results.append(result)

        return results

    def get_summary(self) -> Dict:
        """获取执行结果汇总"""
        summary = super().get_summary()
        step_results = self.get_step_results()

        # 检查所有步骤的验证结果和响应状态
        success = True
        export_vars = {}
        for step in step_results:
            # 检查步骤成功状态
            if not step['success']:
                success = False
                break

            # 对于HTTP请求，检查响应状态码
            if step['step_type'] == 'request' and step['data'].get('response', {}).get('status_code', 0) >= 400:
                success = False
                break

            # 收集导出的变量
            if step['data'].get('extracted_variables'):
                export_vars.update(step['data']['extracted_variables'])

        return {
            'success': success,
            'name': summary.name,
            'time': {
                'start_at': summary.time.start_at,
                'duration': summary.time.duration
            },
            'in_out': {
                'config_vars': summary.in_out.config_vars,
                'export_vars': export_vars
            },
            'log': summary.log,
            'step_results': step_results
        }

class BatchRunner:
    """批量执行器"""

    def __init__(self, testcases: List[TestCase]):
        self.testcases = testcases
        self.results = []

    def run(self, environment: Optional[Dict] = None) -> List[Dict]:
        """
        批量执行测试用例

        Args:
            environment: 环境变量配置

        Returns:
            List[Dict]: 执行结果列表
        """
        for testcase in self.testcases:
            # 执行测试用例
            runner = TestCaseRunner(testcase)
            runner.run_testcase(environment)

            # 收集结果
            self.results.append({
                'testcase_id': testcase.id,
                'testcase_name': testcase.name,
                'summary': runner.get_summary()
            })

        return self.results

    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.results:
            return {}

        total = len(self.results)
        success = len([r for r in self.results if r['summary']['success']])

        return {
            'total': total,
            'success': success,
            'fail': total - success,
            'success_rate': f"{(success / total * 100):.2f}%"
        }