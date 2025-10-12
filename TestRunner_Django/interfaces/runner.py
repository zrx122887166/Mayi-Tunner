from typing import Dict, Optional, List, Text
import logging
import json
from httprunner import HttpRunner, Config, Step, RunRequest, RunSqlRequest
from httprunner.models import TestCaseSummary
from httprunner.parser import Parser

logger = logging.getLogger('testrunner')

# 导入load_custom_functions函数
from functions.models import CustomFunction
import types

def load_custom_functions(project_id):
    """加载项目的自定义函数"""
    functions = {}
    loaded_count = 0
    error_count = 0
    
    try:
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

class InterfaceRunner(HttpRunner):
    """接口执行器"""
    
    def __init__(self, interface_data: Dict):
        super().__init__()
        self.interface_data = interface_data
        self.db_engine = None  # 用于SQL类型接口执行
        self.functions = {}  # 用于存储自定义函数
        
        try:
            self.config = Config(self.interface_data.get('name', 'Interface Request'))
            self.base_url = self.interface_data.get('base_url', '')
            self.verify = self.interface_data.get('verify', None)
            self.variables = self.interface_data.get('variables', {})
            
            # 设置配置
            if self.base_url:
                self.config.base_url(self.base_url)
            if self.verify is not None:
                self.config.verify(self.verify)
            if self.variables:
                self.config.variables(**self.variables)
            
            # 加载项目自定义函数
            project_id = self.interface_data.get('project_id')
            if project_id:
                try:
                    # 加载项目的自定义函数
                    custom_functions = load_custom_functions(project_id)
                    
                    if custom_functions:
                        # 注册到HttpRunner的函数映射中
                        self.functions.update(custom_functions)
                        # 使用实例化的Parser对象
                        self.parser = Parser(functions_mapping=custom_functions)
                        logger.info(f"接口[{self.interface_data.get('name')}]已加载项目自定义函数: {list(custom_functions.keys())}")
                except Exception as e:
                    logger.error(f"加载项目自定义函数失败: {str(e)}")
                
            logger.info(f"接口配置解析结果: base_url={self.base_url}, "
                       f"verify={self.verify}, variables={self.variables}")
        except Exception as e:
            logger.error(f"接口配置初始化失败: {str(e)}")
            raise
        
        # 确定接口类型，HTTP 或 SQL
        interface_type = self.interface_data.get('type', 'http')
        
        if interface_type == 'sql':
            # SQL类型接口
            self._init_sql_step()
        else:
            # HTTP类型接口
            self._init_http_step()
    
    def _init_http_step(self):
        """初始化HTTP步骤"""
        step_obj = RunRequest(self.interface_data.get('name', 'Interface Request'))
        
        # 设置请求方法和URL
        method = self.interface_data.get('method', 'GET').lower()
        url = self.interface_data.get('url', '')
        
        if not url.startswith(('http://', 'https://')):
            url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"
            
        logger.debug(f"请求URL: {url}")
        
        # 添加setup hooks
        if self.interface_data.get('setup_hooks'):
            for hook in self.interface_data['setup_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，需要序列化为JSON字符串
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.setup_hook(hook_json)
                    logger.debug(f"[诊断] 添加SQL类型的前置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型hook，需要序列化整个字典
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.setup_hook(hook_json)
                        logger.debug(f"[诊断] 添加带变量名的SQL类型前置钩子(已序列化): {hook_json}")
                    else:
                        # 普通变量定义hook，序列化为JSON
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.setup_hook(hook_json)
                        logger.debug(f"[诊断] 添加普通变量定义前置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict):
                    # 其他字典类型hook，序列化为JSON
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.setup_hook(hook_json)
                    logger.debug(f"[诊断] 添加字典类型前置钩子(已序列化): {hook_json}")
                else:
                    # 字符串类型hook，直接添加
                    step_obj = step_obj.setup_hook(hook)
                    logger.debug(f"[诊断] 添加字符串类型前置钩子: {hook}")
                
        # 执行HTTP方法
        step_obj = getattr(step_obj, method)(url)
        
        # 添加teardown hooks
        if self.interface_data.get('teardown_hooks'):
            for hook in self.interface_data['teardown_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，需要序列化为JSON字符串
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.teardown_hook(hook_json)
                    logger.debug(f"[诊断] 添加SQL类型的后置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型hook，需要序列化整个字典
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.teardown_hook(hook_json)
                        logger.debug(f"[诊断] 添加带变量名的SQL类型后置钩子(已序列化): {hook_json}")
                    else:
                        # 普通变量定义hook，序列化为JSON
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.teardown_hook(hook_json)
                        logger.debug(f"[诊断] 添加普通变量定义后置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict):
                    # 其他字典类型hook，序列化为JSON
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.teardown_hook(hook_json)
                    logger.debug(f"[诊断] 添加字典类型后置钩子(已序列化): {hook_json}")
                else:
                    # 字符串类型hook，直接添加
                    step_obj = step_obj.teardown_hook(hook)
                    logger.debug(f"[诊断] 添加字符串类型后置钩子: {hook}")
        
        # 添加请求参数
        if self.interface_data.get('params'):
            params = {}
            for k, v in self.interface_data['params'].items():
                if isinstance(v, str) and v.startswith('$'):
                    var_name = v[1:]
                    if var_name in self.variables:
                        params[k] = self.variables[var_name]
                    else:
                        params[k] = v
                else:
                    params[k] = v
            step_obj = step_obj.with_params(**params)
            logger.debug(f"请求参数: {params}")
        
        # 添加请求头
        # 首先获取全局请求头
        logger.info(f"[诊断] 开始处理请求头，project_id: {self.interface_data.get('project_id')}")
        global_headers = self._get_global_headers()
        logger.info(f"[诊断] 获取到的全局请求头: {global_headers}")
        
        headers_dict = {}
        # 先添加全局请求头
        if global_headers:
            headers_dict.update(global_headers)
            logger.info(f"[诊断] 已添加全局请求头到headers_dict: {headers_dict}")
        
        # 然后添加接口特定的请求头（会覆盖同名的全局请求头）
        if self.interface_data.get('headers'):
            # 处理headers，支持字典和列表两种格式
            interface_headers = {}
            headers = self.interface_data['headers']
            logger.info(f"[诊断] 接口自身的headers: {headers}")
            if isinstance(headers, dict):
                # 字典格式，直接使用
                interface_headers = headers
            elif isinstance(headers, list):
                # 列表格式，转换为字典
                for header in headers:
                    if isinstance(header, dict) and header.get('enabled', True):
                        interface_headers[header['key']] = header['value']
            
            # 合并接口特定的请求头
            if interface_headers:
                headers_dict.update(interface_headers)
                logger.info(f"[诊断] 合并接口请求头后的headers_dict: {headers_dict}")
        
        # 添加合并后的headers
        if headers_dict:
            step_obj = step_obj.with_headers(**headers_dict)
        logger.info(f"[诊断] 最终应用的请求头: {headers_dict}")
        
        # 添加请求体
        if self.interface_data.get('body'):
            body = self.interface_data['body']
            # 处理请求体中的变量引用
            if isinstance(body, str) and body.startswith('$'):
                var_name = body[1:]
                if var_name in self.variables:
                    body = self.variables[var_name]
            # 处理RAW格式的请求体
            if isinstance(body, dict) and 'type' in body and 'content' in body:
                if body['type'] == 'raw':
                    content = body['content']
                    # 尝试解析JSON字符串
                    if isinstance(content, str):
                        try:
                            body = json.loads(content)
                        except json.JSONDecodeError:
                            logger.error(f"解析请求体失败: {content}")
                            body = content
                    else:
                        body = content
            step_obj = step_obj.with_json(body)
            logger.debug(f"请求体: {body}")
        
        # 添加提取器
        if self.interface_data.get('extract'):
            extract_obj = step_obj.extract()
            for var_name, expr in self.interface_data['extract'].items():
                extract_obj = extract_obj.with_jmespath(expr, var_name)
                logger.debug(f"添加提取器: {var_name} <- {expr}")
            step_obj = extract_obj
        
        # 添加验证器
        if self.interface_data.get('validators'):
            validate_obj = step_obj.validate()
            for validator in self.interface_data['validators']:
                if isinstance(validator, dict):
                    if "check" in validator and "expect" in validator:
                        # 格式1: {"check": "status_code", "expect": 200}
                        validate_obj = validate_obj.assert_equal(validator["check"], validator["expect"])
                        logger.debug(f"添加验证器: {validator['check']} == {validator['expect']}")
                    elif "eq" in validator:
                        # 格式2: {"eq": ["status_code", 200]}
                        check_value = validator["eq"][0]
                        expect_value = validator["eq"][1]
                        validate_obj = validate_obj.assert_equal(check_value, expect_value)
                        logger.debug(f"添加验证器: {check_value} == {expect_value}")
                    elif len(validator) == 1:
                        # 格式3: {"comparator_name": [check_item, expected_value]}
                        comparator = list(validator.keys())[0]
                        check_item, expected_value = validator[comparator]
                        
                        if comparator == "eq":
                            validate_obj = validate_obj.assert_equal(check_item, expected_value)
                        elif comparator == "lt":
                            validate_obj = validate_obj.assert_less_than(check_item, expected_value)
                        elif comparator == "le":
                            validate_obj = validate_obj.assert_less_or_equals(check_item, expected_value)
                        elif comparator == "gt":
                            validate_obj = validate_obj.assert_greater_than(check_item, expected_value)
                        elif comparator == "ge":
                            validate_obj = validate_obj.assert_greater_or_equals(check_item, expected_value)
                        elif comparator == "ne":
                            validate_obj = validate_obj.assert_not_equal(check_item, expected_value)
                        elif comparator == "str_eq":
                            validate_obj = validate_obj.assert_string_equals(check_item, expected_value)
                        elif comparator == "contains":
                            validate_obj = validate_obj.assert_contains(check_item, expected_value)
                        elif comparator == "contained_by":
                            validate_obj = validate_obj.assert_contained_by(check_item, expected_value)
                        elif comparator == "type_match":
                            validate_obj = validate_obj.assert_type_match(check_item, expected_value)
                        elif comparator == "regex_match":
                            validate_obj = validate_obj.assert_regex_match(check_item, expected_value)
                        else:
                            logger.warning(f"不支持的比较器: {comparator}")
                        logger.debug(f"添加验证器: {comparator}({check_item}, {expected_value})")
                else:
                    logger.warning(f"不支持的验证器格式: {validator}")
            step_obj = validate_obj
                    
        # 创建Step对象
        step = Step(step_obj)
        self.teststeps.append(step)
    
    def _init_sql_step(self):
        """初始化SQL步骤"""
        step_obj = RunSqlRequest(self.interface_data.get('name', 'SQL Request'))
        
        # 设置SQL方法和语句
        sql_method = self.interface_data.get('method', 'fetchone').lower()
        sql = self.interface_data.get('sql', '')
        
        logger.debug(f"SQL语句: {sql}")
        
        # 添加setup hooks（SQL步骤）
        if self.interface_data.get('setup_hooks'):
            for hook in self.interface_data['setup_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，需要序列化为JSON字符串
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.setup_hook(hook_json)
                    logger.debug(f"[诊断] SQL步骤添加SQL类型的前置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型hook，需要序列化整个字典
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.setup_hook(hook_json)
                        logger.debug(f"[诊断] SQL步骤添加带变量名的SQL类型前置钩子(已序列化): {hook_json}")
                    else:
                        # 普通变量定义hook，序列化为JSON
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.setup_hook(hook_json)
                        logger.debug(f"[诊断] SQL步骤添加普通变量定义前置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict):
                    # 其他字典类型hook，序列化为JSON
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.setup_hook(hook_json)
                    logger.debug(f"[诊断] SQL步骤添加字典类型前置钩子(已序列化): {hook_json}")
                else:
                    # 字符串类型hook，直接添加
                    step_obj = step_obj.setup_hook(hook)
                    logger.debug(f"[诊断] SQL步骤添加字符串类型前置钩子: {hook}")
                
        # 执行SQL方法
        if sql_method == 'fetchone':
            step_obj = step_obj.fetchone(sql)
        elif sql_method == 'fetchmany':
            size = self.interface_data.get('size', 10)
            step_obj = step_obj.fetchmany(sql, size)
        elif sql_method == 'fetchall':
            step_obj = step_obj.fetchall(sql)
        elif sql_method == 'insert':
            step_obj = step_obj.insert(sql)
        elif sql_method == 'update':
            step_obj = step_obj.update(sql)
        elif sql_method == 'delete':
            step_obj = step_obj.delete(sql)
        else:
            logger.warning(f"不支持的SQL方法: {sql_method}，将使用fetchone")
            step_obj = step_obj.fetchone(sql)
        
        # 添加teardown hooks（SQL步骤）
        if self.interface_data.get('teardown_hooks'):
            for hook in self.interface_data['teardown_hooks']:
                # 检查是否是SQL类型的hook
                if isinstance(hook, dict) and hook.get('type') == 'sql':
                    # 这是SQL类型的hook，需要序列化为JSON字符串
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.teardown_hook(hook_json)
                    logger.debug(f"[诊断] SQL步骤添加SQL类型的后置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict) and len(hook) == 1:
                    # 检查值是否是SQL类型的hook
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get('type') == 'sql':
                        # 这是带变量名的SQL类型hook，需要序列化整个字典
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.teardown_hook(hook_json)
                        logger.debug(f"[诊断] SQL步骤添加带变量名的SQL类型后置钩子(已序列化): {hook_json}")
                    else:
                        # 普通变量定义hook，序列化为JSON
                        hook_json = json.dumps(hook, ensure_ascii=False)
                        step_obj = step_obj.teardown_hook(hook_json)
                        logger.debug(f"[诊断] SQL步骤添加普通变量定义后置钩子(已序列化): {hook_json}")
                elif isinstance(hook, dict):
                    # 其他字典类型hook，序列化为JSON
                    hook_json = json.dumps(hook, ensure_ascii=False)
                    step_obj = step_obj.teardown_hook(hook_json)
                    logger.debug(f"[诊断] SQL步骤添加字典类型后置钩子(已序列化): {hook_json}")
                else:
                    # 字符串类型hook，直接添加
                    step_obj = step_obj.teardown_hook(hook)
                    logger.debug(f"[诊断] SQL步骤添加字符串类型后置钩子: {hook}")
        
        # 添加提取变量
        if self.interface_data.get('extract'):
            for var_name, expr in self.interface_data['extract'].items():
                step_obj = step_obj.with_jmespath(expr, var_name)
                logger.debug(f"添加变量提取: {var_name} = {expr}")
        
        # 添加验证器
        if self.interface_data.get('validators'):
            validate_obj = step_obj.validate()
            for validator in self.interface_data['validators']:
                if isinstance(validator, dict):
                    for comparator, (check_item, expected_value) in validator.items():
                        try:
                            # StepSqlRequestValidation 没有 assert_that 方法，使用具体的断言方法
                            if comparator == "eq":
                                validate_obj = validate_obj.assert_equal(check_item, expected_value)
                            elif comparator == "ne":
                                validate_obj = validate_obj.assert_not_equal(check_item, expected_value)
                            elif comparator == "gt":
                                validate_obj = validate_obj.assert_greater_than(check_item, expected_value)
                            elif comparator == "ge":
                                validate_obj = validate_obj.assert_greater_or_equals(check_item, expected_value)
                            elif comparator == "lt":
                                validate_obj = validate_obj.assert_less_than(check_item, expected_value)
                            elif comparator == "le":
                                validate_obj = validate_obj.assert_less_or_equals(check_item, expected_value)
                            elif comparator == "contains":
                                validate_obj = validate_obj.assert_contains(check_item, expected_value)
                            else:
                                # 对于不支持的比较器，使用 type: ignore 来忽略类型检查
                                validate_obj = validate_obj.assert_that(check_item, comparator, expected_value)  # type: ignore
                            logger.debug(f"添加验证器: {comparator}({check_item}, {expected_value})")
                        except AttributeError as e:
                            logger.warning(f"SQL验证器方法不存在: {str(e)}")
                        except Exception as e:
                            logger.warning(f"添加验证器失败: {str(e)}")
                else:
                    logger.warning(f"不支持的验证器格式: {validator}")
            step_obj = validate_obj
                    
        # 创建Step对象
        step = Step(step_obj)
        self.teststeps.append(step)
    
    def run_interface(self, environment: Optional[Dict] = None) -> "InterfaceRunner":
        """运行接口请求"""
        logger.info(f"开始执行接口请求[{self.interface_data.get('name', 'Interface Request')}]")
        logger.info(f"当前配置: base_url={self.base_url}, verify={self.verify}, "
                   f"variables={self.variables}, environment={environment}")
        
        # 确定接口类型
        interface_type = self.interface_data.get('type', 'http')
        logger.info(f"接口类型: {interface_type}")
        
        # 1. 处理环境变量
        try:
            if environment and isinstance(environment, dict) and environment.get('variables'):
                logger.debug(f"更新环境变量: {environment['variables']}")
                self.variables.update(environment['variables'])
                self.config.variables = self.variables
                logger.debug(f"更新后的变量: {self.variables}")
            elif environment and not isinstance(environment, dict):
                logger.warning(f"环境参数类型错误，期望字典类型，实际是: {type(environment)}")
        except Exception as e:
            logger.error(f"更新环境变量失败: {str(e)}")
            
        # 2. 处理数据库配置（SQL接口）
        try:
            if interface_type == 'sql' and environment and isinstance(environment, dict) and environment.get('db_config'):
                db_config = environment['db_config']
                # 更新接口数据中的数据库配置
                if 'db_config' not in self.interface_data:
                    self.interface_data['db_config'] = {}
                    
                # 环境中的数据库配置优先级高于接口自身配置
                for key in ['user', 'password', 'ip', 'port', 'database']:
                    if key in db_config and db_config[key]:
                        self.interface_data['db_config'][key] = db_config[key]
                        
                logger.debug(f"更新后的数据库配置: {self.interface_data['db_config']}")
        except Exception as e:
            logger.error(f"更新数据库配置失败: {str(e)}")

        # 3. 更新测试步骤配置
        try:
            for step in self.teststeps:
                # Step对象在运行时动态添加属性，使用 type: ignore 忽略类型检查
                if interface_type == 'http':
                    # 检查是否有request属性并且是RunRequest类型
                    if hasattr(step, 'request') and isinstance(getattr(step, 'request', None), RunRequest):
                        # 设置变量 - 使用 type: ignore 避免类型检查错误
                        step.variables = self.variables  # type: ignore
                        
                        # 获取request对象
                        request_obj = step.request  # type: ignore
                        
                        # 设置base_url - 使用 type: ignore 处理动态属性
                        if hasattr(request_obj, 'url'):
                            url = request_obj.url  # type: ignore
                            if url and not url.startswith(('http://', 'https://')):
                                request_obj.url = f"{self.base_url.rstrip('/')}/{url.lstrip('/')}"  # type: ignore
                                logger.debug(f"接口请求URL: {request_obj.url}")  # type: ignore
                        
                        # 调试记录请求信息
                        if hasattr(request_obj, 'headers'):
                            logger.debug(f"接口请求头: {request_obj.headers}")  # type: ignore
                        if hasattr(request_obj, 'params'):
                            logger.debug(f"接口请求参数: {request_obj.params}")  # type: ignore
                        if hasattr(request_obj, 'json'):
                            logger.debug(f"接口请求体: {request_obj.json}")  # type: ignore
                        elif hasattr(request_obj, 'data'):
                            logger.debug(f"接口请求体: {request_obj.data}")  # type: ignore
                elif interface_type == 'sql':
                    # SQL类型测试步骤 - 使用 type: ignore 避免类型检查错误
                    step.variables = self.variables  # type: ignore
                    # SQL测试步骤的更新在运行时由httprunner内部处理
                    # 这里只需确保变量已更新
        except Exception as e:
            logger.error(f"更新接口步骤配置失败: {str(e)}")
            raise

        # 4. 开始执行接口请求
        try:
            self.test_start()
        except Exception as e:
            logger.error(f"执行接口请求失败: {str(e)}")
            raise

        return self
    
    def get_summary(self) -> TestCaseSummary:
        """获取执行结果摘要"""
        return super().get_summary()
        
    def get_response(self) -> Dict:
        """获取接口响应结果"""
        summary = self.get_summary()
        if not summary.step_results:
            return {
                "success": False,
                "error": "没有执行结果"
            }
        
        step_result = summary.step_results[0]
        
        # 安全地获取属性，使用 type: ignore 忽略类型检查
        data = step_result.data  # type: ignore
        req_resp = None
        stat = None
        validators = {}
        
        # 检查data是否有req_resp属性（HTTP请求）
        if hasattr(data, 'req_resp'):
            req_resp = data.req_resp  # type: ignore
        # 检查data是否有req_resps列表（兼容不同版本）
        elif hasattr(data, 'req_resps') and isinstance(data.req_resps, list):  # type: ignore
            req_resps = data.req_resps  # type: ignore
            if req_resps:
                req_resp = req_resps[0]
        
        # 获取统计信息
        if hasattr(data, 'stat'):
            stat = data.stat  # type: ignore
        
        # 获取验证器结果
        if hasattr(data, 'validators'):
            validators = data.validators  # type: ignore
        
        # 构建响应
        result = {
            "success": step_result.success,
            "name": step_result.name,
            "validators": validators,
            "extracted_variables": step_result.export_vars  # type: ignore
        }
        
        # 添加HTTP请求相关信息（如果存在）
        if req_resp:
            result.update({
                "status_code": req_resp.response.status_code if hasattr(req_resp, 'response') else None,  # type: ignore
                "response_time_ms": stat.response_time_ms if stat else 0,  # type: ignore
                "request": {
                    "method": req_resp.request.method if hasattr(req_resp, 'request') else None,  # type: ignore
                    "url": req_resp.request.url if hasattr(req_resp, 'request') else None,  # type: ignore
                    "headers": req_resp.request.headers if hasattr(req_resp, 'request') else {},  # type: ignore
                    "body": req_resp.request.body if hasattr(req_resp, 'request') else None  # type: ignore
                },
                "response": {
                    "headers": req_resp.response.headers if hasattr(req_resp, 'response') else {},  # type: ignore
                    "body": req_resp.response.body if hasattr(req_resp, 'response') else None,  # type: ignore
                    "content_size": stat.content_size if stat else 0  # type: ignore
                }
            })
        else:
            # 没有HTTP请求信息，可能是SQL或其他类型
            result.update({
                "status_code": None,
                "response_time_ms": 0,
                "request": {"method": None, "url": None, "headers": {}, "body": None},
                "response": {"headers": {}, "body": None, "content_size": 0}
            })
        
        return result
    
    def _get_global_headers(self):
        """获取全局请求头"""
        global_headers = {}
        try:
            # 如果项目关联了全局请求头，则获取它们
            project_id = self.interface_data.get('project_id')
            logger.info(f"[全局请求头诊断] ========== 开始获取全局请求头 ==========")
            logger.info(f"[全局请求头诊断] interface_data 内容: {self.interface_data.keys()}")
            logger.info(f"[全局请求头诊断] project_id: {project_id}, 类型: {type(project_id)}")
            
            if project_id:
                logger.info(f"[全局请求头诊断] 开始查询数据库...")
                from environments.models import GlobalRequestHeader
                
                # 先查询所有相关的全局请求头（不过滤启用状态）
                all_headers = GlobalRequestHeader.objects.filter(project_id=project_id)
                all_count = all_headers.count()
                logger.info(f"[全局请求头诊断] 项目 {project_id} 的所有全局请求头数量: {all_count}")
                
                if all_count > 0:
                    for h in all_headers:
                        logger.info(f"[全局请求头诊断] - {h.name}: is_enabled={h.is_enabled}, value={h.value[:50] if len(h.value) > 50 else h.value}")
                
                # 过滤启用的请求头
                headers = all_headers.filter(is_enabled=True)
                enabled_count = headers.count()
                logger.info(f"[全局请求头诊断] 启用的全局请求头数量: {enabled_count}")
                
                if enabled_count == 0 and all_count > 0:
                    logger.warning(f"[全局请求头诊断] 警告：项目存在 {all_count} 个全局请求头，但都未启用！")
                
                for header in headers:
                    logger.info(f"[全局请求头诊断] 处理请求头: {header.name}")
                    # 检查变量引用
                    header_value = header.value
                    original_value = header_value
                    
                    if isinstance(header_value, str):
                        # 记录当前可用的变量
                        if hasattr(self, 'variables'):
                            logger.info(f"[全局请求头诊断] 当前可用变量: {list(self.variables.keys())}")
                        else:
                            logger.info(f"[全局请求头诊断] 警告：runner 没有 variables 属性")
                        
                        if header_value.startswith('${') and header_value.endswith('}'):
                            # ${var} 格式
                            var_name = header_value[2:-1]
                            logger.info(f"[全局请求头诊断] 检测到变量引用（${{}}格式）: {var_name}")
                            if hasattr(self, 'variables') and var_name in self.variables:
                                header_value = self.variables[var_name]
                                logger.info(f"[全局请求头诊断] 变量替换成功: {original_value} -> {header_value}")
                            else:
                                logger.warning(f"[全局请求头诊断] 变量 {var_name} 不存在，保留原始值")
                        elif header_value.startswith('$') and len(header_value) > 1:
                            # $var 格式
                            var_name = header_value[1:]
                            logger.info(f"[全局请求头诊断] 检测到变量引用（$格式）: {var_name}")
                            if hasattr(self, 'variables') and var_name in self.variables:
                                header_value = self.variables[var_name]
                                logger.info(f"[全局请求头诊断] 变量替换成功: {original_value} -> {header_value}")
                            else:
                                logger.warning(f"[全局请求头诊断] 变量 {var_name} 不存在，保留原始值")
                    
                    global_headers[header.name] = header_value
                    logger.info(f"[全局请求头诊断] 添加请求头: {header.name} = {header_value}")
            else:
                logger.warning("[全局请求头诊断] project_id 为空或None，无法获取全局请求头")
                logger.warning(f"[全局请求头诊断] interface_data 完整内容: {self.interface_data}")
            
            logger.info(f"[全局请求头诊断] ========== 结束，返回 {len(global_headers)} 个请求头 ==========")
            if global_headers:
                logger.info(f"[全局请求头诊断] 最终请求头列表: {list(global_headers.keys())}")
            return global_headers
        except Exception as e:
            logger.error(f"[全局请求头诊断] ！！！发生错误: {str(e)}")
            import traceback
            logger.error(f"[全局请求头诊断] 错误堆栈:\n{traceback.format_exc()}")
            return {}