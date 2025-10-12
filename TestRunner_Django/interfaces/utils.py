import json
import logging
import os
import types
from httprunner import HttpRunner, Config, Step, RunRequest, RunTestCase
from httprunner.models import TConfig, TStep, ProjectMeta, TestCase
from httprunner.runner import SessionRunner
from rest_framework.response import Response
from rest_framework import status
from functions.models import CustomFunction
from environments.models import GlobalRequestHeader
from httprunner.parser import Parser

logger = logging.getLogger('testrunner')

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

class ResponseHandler:
    """响应处理工具类"""
    @staticmethod
    def success(data=None, message="操作成功", code=status.HTTP_200_OK):
        """成功响应"""
        return Response({
            'status': 'success',
            'code': code,
            'message': message,
            'data': data or {}
        })

    @staticmethod
    def error(message="操作失败", errors=None, code=status.HTTP_400_BAD_REQUEST, data=None):
        """错误响应"""
        response_data = {
            'status': 'error',
            'code': code,
            'message': message,
            'data': data or {},
        }
        if errors:
            response_data['errors'] = errors
        return Response(response_data, status=code)

class InterfaceRunner(HttpRunner):
    """接口运行器"""
    def __init__(self, interface, environment):
        super().__init__()
        self.interface = interface
        self.environment = environment
        self.functions = {}
        
        try:
            # 加载项目的自定义函数
            custom_functions = load_custom_functions(interface.project_id)
            
            if custom_functions:
                # 注册到HttpRunner的函数映射中
                self.functions.update(custom_functions)
                logger.info(f"接口[{interface.name}]已加载项目自定义函数: {list(custom_functions.keys())}")
                # 同时注册到parser中
                self.parser = Parser(functions_mapping=custom_functions)
            else:
                logger.warning(f"项目[{interface.project.name}]没有可用的自定义函数")
                
        except Exception as e:
            logger.error(f"加载项目[{interface.project.name}]自定义函数失败: {str(e)}")
            # 不阻止接口执行,但没有自定义函数可用
            pass
        
        # 获取环境的base_url，如果环境没有主键则使用空字符串
        base_url = ""
        if self.environment and self.environment.pk:
            base_url = self.environment.base_url or ""

        # 记录前置和后置钩子信息
        if self.interface.setup_hooks:
            logger.info(f"接口[{interface.name}]定义了{len(self.interface.setup_hooks)}个前置钩子")
            for i, hook in enumerate(self.interface.setup_hooks):
                logger.debug(f"前置钩子 #{i+1}: {hook}")
        else:
            logger.debug(f"接口[{interface.name}]没有定义前置钩子")
            
        if self.interface.teardown_hooks:
            logger.info(f"接口[{interface.name}]定义了{len(self.interface.teardown_hooks)}个后置钩子")
            for i, hook in enumerate(self.interface.teardown_hooks):
                logger.debug(f"后置钩子 #{i+1}: {hook}")
        else:
            logger.debug(f"接口[{interface.name}]没有定义后置钩子")
        
        # 处理hooks中的变量
        variables = self._get_variables()
        if self.interface.setup_hooks:
            for hook in self.interface.setup_hooks:
                if isinstance(hook, dict):
                    # 检查是否是SQL类型的钩子
                    if "type" in hook and hook["type"] == "sql":
                        # 对于SQL类型的钩子，不要作为变量处理，在执行时会通过httprunner处理
                        logger.info(f"检测到SQL类型的前置钩子: {hook}")
                    elif len(hook) == 1:
                        # 检查值是否是SQL类型的钩子
                        var_name, hook_content = list(hook.items())[0]
                        if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                            # 这是带变量名的SQL类型钩子，不要作为变量处理
                            logger.info(f"检测到带变量名的SQL类型前置钩子: {var_name} = {hook_content}")
                        else:
                            # 普通变量赋值
                            variables[var_name] = hook_content
                            logger.info(f"前置钩子设置变量: {var_name} = {hook_content}")
                else:
                    # 字符串钩子，不是变量赋值
                    logger.info(f"前置钩子: {hook}")

        if self.interface.teardown_hooks:
            for hook in self.interface.teardown_hooks:
                if isinstance(hook, dict):
                    # 检查是否是SQL类型的钩子
                    if "type" in hook and hook["type"] == "sql":
                        # 对于SQL类型的钩子，不要作为变量处理，在执行时会通过httprunner处理
                        logger.info(f"检测到SQL类型的后置钩子: {hook}")
                    elif len(hook) == 1:
                        # 检查值是否是SQL类型的钩子
                        var_name, hook_content = list(hook.items())[0]
                        if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                            # 这是带变量名的SQL类型钩子，不要作为变量处理
                            logger.info(f"检测到带变量名的SQL类型后置钩子: {var_name} = {hook_content}")
                        else:
                            # 普通变量赋值
                            variables[var_name] = hook_content
                            logger.info(f"后置钩子设置变量: {var_name} = {hook_content}")
                else:
                    # 字符串钩子，不是变量赋值
                    logger.info(f"后置钩子: {hook}")

        # 更新配置中的变量
        self.config = (
            Config(self.interface.name)
            .base_url(base_url)
            .variables(**variables)
            .verify(False)
        )

        # 构建请求步骤
        request_obj = RunRequest(self.interface.name)
        
        # 检查URL是否已包含http/https前缀
        url = self.interface.url
        if url.startswith(('http://', 'https://')):
            # 完整URL，不使用base_url
            full_url = url
        else:
            # 相对URL，需要拼接base_url
            full_url = f"{base_url.rstrip('/')}/{url.lstrip('/')}" if base_url else url
        
        # 根据方法类型调用对应的方法
        method = self.interface.method.lower()
        if method == "get":
            request_obj = request_obj.get(full_url)
        elif method == "post":
            request_obj = request_obj.post(full_url)
        elif method == "put":
            request_obj = request_obj.put(full_url)
        elif method == "delete":
            request_obj = request_obj.delete(full_url)
        elif method == "patch":
            request_obj = request_obj.patch(full_url)
        
        # 添加请求参数
        if self.interface.headers:
            # 处理headers - 支持两种格式：字典或列表
            headers_dict = {}
            if isinstance(self.interface.headers, dict):
                # 如果headers是字典格式，直接使用
                headers_dict = self.interface.headers
                logger.debug(f"使用字典格式headers: {headers_dict}")
            else:
                # 如果headers是列表格式，转换为字典
                for header in self.interface.headers:
                    if isinstance(header, dict) and header.get('enabled', True):
                        headers_dict[header['key']] = header['value']
                logger.debug(f"将列表格式headers转换为字典: {headers_dict}")
            
            if headers_dict:
                request_obj = request_obj.with_headers(**headers_dict)
                logger.debug(f"已应用headers: {headers_dict}")
                
        if self.interface.params:
            # 处理params - 支持两种格式：字典或列表
            params_dict = {}
            if isinstance(self.interface.params, dict):
                # 如果params是字典格式，直接使用
                params_dict = self.interface.params
                logger.debug(f"使用字典格式params: {params_dict}")
            else:
                # 如果params是列表格式，转换为字典
                for param in self.interface.params:
                    if isinstance(param, dict) and param.get('enabled', True):
                        params_dict[param['key']] = param['value']
                logger.debug(f"将列表格式params转换为字典: {params_dict}")
            
            if params_dict:
                request_obj = request_obj.with_params(**params_dict)
                logger.debug(f"已应用params: {params_dict}")
                
        if self.interface.body:
            try:
                # 处理请求体
                if self.interface.body == "null" or self.interface.body is None:
                    # body是null或None，不添加任何请求体
                    logger.debug("请求体为null或None，不添加请求体")
                    pass
                elif isinstance(self.interface.body, dict):
                    if 'type' in self.interface.body and 'content' in self.interface.body:
                        body_type = self.interface.body['type']
                        body_content = self.interface.body['content']
                        
                        if body_type == 'raw':
                            # 如果content是字符串形式的JSON，尝试解析
                            if isinstance(body_content, str):
                                try:
                                    body_data = json.loads(body_content)
                                    request_obj = request_obj.with_json(body_data)
                                except json.JSONDecodeError:
                                    # 如果不是JSON字符串，直接使用原始内容
                                    request_obj = request_obj.with_data(body_content)
                            else:
                                # content不是字符串，直接使用
                                request_obj = request_obj.with_json(body_content)
                        elif body_type == 'form':
                            # 处理form类型的数据
                            request_obj = request_obj.with_data(body_content)
                        elif body_type == 'form-data':
                            # 处理multipart/form-data类型的数据
                            request_obj = request_obj.with_data(body_content)
                            request_obj.request.headers['Content-Type'] = 'multipart/form-data'
                        else:
                            # 未知类型，记录警告并尝试作为JSON处理
                            logger.warning(f"未知的请求体类型: {body_type}，将尝试作为JSON处理")
                            request_obj = request_obj.with_json(body_content)
                    else:
                        # body是普通的dict，直接作为JSON处理
                        request_obj = request_obj.with_json(self.interface.body)
                else:
                    # body不是dict类型，尝试直接发送
                    request_obj = request_obj.with_data(self.interface.body)
                    
            except Exception as e:
                logger.error(f"处理请求体时发生错误: {str(e)}")
                # 发生错误时，尝试直接发送原始数据
                if self.interface.body != "null" and self.interface.body is not None:
                    request_obj = request_obj.with_data(self.interface.body)
            
        # 添加变量提取器
        if self.interface.extract:
            request_obj = request_obj.extract()
            for var_name, expr in self.interface.extract.items():
                request_obj = request_obj.with_jmespath(expr, var_name)
        
        # 添加验证器
        if self.interface.validators:
            # 保存原始请求对象
            original_request_obj = request_obj
            
            # 获取验证对象并添加验证器
            validate_obj = request_obj.validate()
            
            for validator in self.interface.validators:
                if not isinstance(validator, dict):
                    logger.warning(f"无效的验证器格式: {validator}")
                    continue
                
                if "check" in validator and "expect" in validator:
                    # 格式1: {"check": "status_code", "expect": 200}
                    validate_obj = validate_obj.assert_equal(validator["check"], validator["expect"])
                    logger.debug(f"添加验证器: {validator['check']} == {validator['expect']}")
                elif len(validator) == 1:
                    # 格式2: {"eq": ["status_code", 200]}
                    comparator = list(validator.keys())[0]
                    check_item, expect_value = validator[comparator]
                    
                    if comparator == "eq":
                        validate_obj = validate_obj.assert_equal(check_item, expect_value)
                    elif comparator == "lt":
                        validate_obj = validate_obj.assert_less_than(check_item, expect_value)
                    elif comparator == "le" or comparator == "lte":
                        validate_obj = validate_obj.assert_less_or_equals(check_item, expect_value)
                    elif comparator == "gt":
                        validate_obj = validate_obj.assert_greater_than(check_item, expect_value)
                    elif comparator == "ge" or comparator == "gte":
                        validate_obj = validate_obj.assert_greater_or_equals(check_item, expect_value)
                    elif comparator == "ne":
                        validate_obj = validate_obj.assert_not_equal(check_item, expect_value)
                    elif comparator == "contains":
                        validate_obj = validate_obj.assert_contains(check_item, expect_value)
                    elif comparator == "contained_by":
                        validate_obj = validate_obj.assert_contained_by(check_item, expect_value)
                    elif comparator == "type_match":
                        validate_obj = validate_obj.assert_type_match(check_item, expect_value)
                    elif comparator == "regex_match":
                        validate_obj = validate_obj.assert_regex_match(check_item, expect_value)
                    elif comparator == "startswith":
                        validate_obj = validate_obj.assert_startswith(check_item, expect_value)
                    elif comparator == "endswith":
                        validate_obj = validate_obj.assert_endswith(check_item, expect_value)
                    elif comparator == "length_equal":
                        validate_obj = validate_obj.assert_length_equal(check_item, expect_value)
                    elif comparator == "length_greater_than":
                        validate_obj = validate_obj.assert_length_greater_than(check_item, expect_value)
                    elif comparator == "length_less_than":
                        validate_obj = validate_obj.assert_length_less_than(check_item, expect_value)
                    elif comparator == "length_greater_or_equals":
                        validate_obj = validate_obj.assert_length_greater_or_equals(check_item, expect_value)
                    elif comparator == "length_less_or_equals":
                        validate_obj = validate_obj.assert_length_less_or_equals(check_item, expect_value)
                    else:
                        logger.warning(f"不支持的比较器: {comparator}")
                        continue
                        
                    logger.debug(f"添加验证器: {comparator}({check_item}, {expect_value})")
            
            # 使用更新后的验证对象，它是一个StepRequestValidation对象
            request_obj = validate_obj
            
            # 添加后置钩子 (StepRequestValidation没有teardown_hook方法，所以使用原始对象)
            if self.interface.teardown_hooks:
                logger.info("========== 准备执行后置钩子 ==========")
                for i, hook in enumerate(self.interface.teardown_hooks):
                    if isinstance(hook, dict) and hook.get("type") == "sql":
                        # SQL钩子将在请求执行后手动处理
                        logger.info(f"SQL后置钩子 #{i+1}: {hook}")
                    elif isinstance(hook, dict) and len(hook) == 1:
                        var_name, hook_content = list(hook.items())[0]
                        if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                            # SQL钩子将在请求执行后手动处理
                            logger.info(f"带变量名的SQL后置钩子 #{i+1}: {var_name} = {hook_content}")
                        else:
                            # 普通的钩子添加到原始对象
                            original_request_obj = original_request_obj.teardown_hook(hook)
                            logger.info(f"后置钩子 #{i+1}: {hook}")
                    else:
                        # 字符串钩子添加到原始对象
                        original_request_obj = original_request_obj.teardown_hook(hook)
                        logger.info(f"后置钩子 #{i+1}: {hook}")
                
                # 后置钩子都已添加到original_request_obj，现在需要将验证器合并到此对象
                if hasattr(request_obj, 'struct'):
                    validated_step_struct = request_obj.struct()
                    original_step_struct = original_request_obj.struct()
                    
                    # 将验证器从validated_step复制到original_request_obj
                    original_step_struct.validators = validated_step_struct.validators
                    
                    # 使用带有验证器和后置钩子的原始对象执行请求
                    request_obj = original_request_obj
            
        # 如果没有验证器但有后置钩子，直接添加后置钩子
        elif self.interface.teardown_hooks:
            logger.info("========== 准备执行后置钩子 ==========")
            for i, hook in enumerate(self.interface.teardown_hooks):
                if isinstance(hook, dict) and hook.get("type") == "sql":
                    # 直接使用SQL钩子（不需要通过step_obj.teardown_hook，httprunner会处理）
                    logger.info(f"SQL后置钩子 #{i+1}: {hook}")
                    # 我们会在请求执行后手动执行这个钩子
                elif isinstance(hook, dict) and len(hook) == 1:
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                        # 带变量名的SQL钩子
                        logger.info(f"带变量名的SQL后置钩子 #{i+1}: {var_name} = {hook_content}")
                        # 我们会在请求执行后手动执行这个钩子
                    else:
                        # 普通的钩子
                        request_obj = request_obj.teardown_hook(hook)
                        logger.info(f"后置钩子 #{i+1}: {hook}")
                else:
                    # 字符串钩子
                    request_obj = request_obj.teardown_hook(hook)
                    logger.info(f"后置钩子 #{i+1}: {hook}")

        # 确保函数映射正确注册到parser
        from httprunner.parser import Parser
        self.parser = Parser(functions_mapping=self.functions)
        from httprunner.response import ResponseObjectBase
        ResponseObjectBase.functions_mapping = self.functions

        # 执行请求
        step = Step(request_obj)
        result = self.run_step(step)
        
        # 执行后检查变量变化，推断钩子执行结果
        post_variables = {}
        if hasattr(self, 'context') and hasattr(self.context, 'variables'):
            post_variables = dict(self.context.variables)
            # 查找新增或变化的变量
            for var_name, var_value in post_variables.items():
                if var_name not in pre_variables or pre_variables[var_name] != var_value:
                    logger.info(f"变量变化: '{var_name}' = '{var_value}'")
        
        # 手动执行SQL类型的后置钩子
        if self.interface.teardown_hooks:
            logger.info("========== 开始执行SQL类型后置钩子 ==========")
            from httprunner.step_request import execute_sql_hook
            
            for i, hook in enumerate(self.interface.teardown_hooks):
                if isinstance(hook, dict) and hook.get("type") == "sql":
                    # 执行SQL钩子
                    logger.info(f"执行SQL后置钩子 #{i+1}: {hook}")
                    execute_sql_hook(self, hook, post_variables)
                elif isinstance(hook, dict) and len(hook) == 1:
                    var_name, hook_content = list(hook.items())[0]
                    if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                        # 设置变量名
                        sql_hook = hook_content.copy()
                        sql_hook["var_name"] = var_name
                        # 执行SQL钩子
                        logger.info(f"执行带变量名的SQL后置钩子 #{i+1}: {var_name} = {hook_content}")
                        execute_sql_hook(self, sql_hook, post_variables)
            logger.info("========== SQL类型后置钩子执行完成 ==========")
        
        # 尝试从summary获取钩子执行结果
        if hasattr(self, "summary"):
            # 从summary中尝试获取钩子执行结果
            if "details" in self.summary and len(self.summary["details"]) > 0:
                case_detail = self.summary["details"][0]
                # 记录前置钩子执行结果
                setup_hooks_results = case_detail.get("setup_hooks", [])
                if setup_hooks_results:
                    logger.info("从summary获取的前置钩子执行结果:")
                    for i, result in enumerate(setup_hooks_results):
                        logger.info(f"  前置钩子 #{i+1} 结果: {result}")
                
                # 记录后置钩子执行结果
                teardown_hooks_results = case_detail.get("teardown_hooks", [])
                if teardown_hooks_results:
                    logger.info("从summary获取的后置钩子执行结果:")
                    for i, result in enumerate(teardown_hooks_results):
                        logger.info(f"  后置钩子 #{i+1} 结果: {result}")
        
        # 检查是否有step_results
        if hasattr(self, "summary") and hasattr(self.summary, "step_results") and self.summary.step_results:
            step_result = self.summary.step_results[0]
            if hasattr(step_result, "hooks_results"):
                logger.info("从step_results获取的钩子执行结果:")
                hooks_results = step_result.hooks_results
                if "setup_hooks" in hooks_results:
                    for i, result in enumerate(hooks_results["setup_hooks"]):
                        logger.info(f"  前置钩子 #{i+1} 结果: {result}")
                if "teardown_hooks" in hooks_results:
                    for i, result in enumerate(hooks_results["teardown_hooks"]):
                        logger.info(f"  后置钩子 #{i+1} 结果: {result}")
        
        # 记录响应信息
        step = self.teststeps[0]
        if hasattr(step, 'response') and step.response:
            logger.info(f"请求完成: 状态码={step.response.status_code}")
        
        # 直接记录后置钩子内容
        if self.interface.teardown_hooks:
            logger.info("========== 开始执行后置钩子 ==========")
            for i, hook in enumerate(self.interface.teardown_hooks):
                logger.info(f"后置钩子 #{i+1}: {hook}")
        
        # 导出变量信息（从多个可能的位置）
        if hasattr(self, "summary"):
            # 尝试方式1：从details中获取
            if "details" in self.summary and len(self.summary["details"]) > 0:
                case_detail = self.summary["details"][0]
                export_vars = case_detail.get("export_vars", {})
                if export_vars:
                    logger.info("从summary.details获取的导出变量:")
                    for var_name, var_value in export_vars.items():
                        logger.info(f"  - {var_name} = {var_value}")
        
            # 尝试方式2：从step_results中获取
            if hasattr(self.summary, "step_results") and self.summary.step_results:
                step_result = self.summary.step_results[0]
                if hasattr(step_result, "export_vars") and step_result.export_vars:
                    logger.info("从step_results获取的导出变量:")
                    for var_name, var_value in step_result.export_vars.items():
                        logger.info(f"  - {var_name} = {var_value}")
        
        # 比较最终变量与执行前变量的差异，找出钩子可能产生的变量
        if post_variables:
            new_vars = {}
            for var_name, var_value in post_variables.items():
                if var_name not in pre_variables:
                    new_vars[var_name] = var_value
            
            if new_vars:
                logger.info("钩子执行后的新增变量:")
                for var_name, var_value in new_vars.items():
                    logger.info(f"  - {var_name} = {var_value}")
        
        logger.info("========== 接口测试执行完成 ==========")
        return self
        
    def get_logs(self):
        """获取测试日志"""
        log_path = self.summary.get("log_path")
        if log_path and os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _get_variables(self):
        """获取环境变量"""
        variables = {}
        
        # 检查环境对象是否有主键
        if not self.environment or not self.environment.pk:
            logger.info("使用临时环境对象或环境对象没有主键，跳过加载环境变量")
            # 只返回接口变量
            return self.interface.variables or {}
        
        # 获取父环境的变量
        if self.environment.parent:
            parent_vars = self.environment.parent.variables.all()
            for var in parent_vars:
                try:
                    if var.type == "json":
                        variables[var.name] = json.loads(var.value)
                    elif var.type == "int":
                        variables[var.name] = int(var.value)
                    elif var.type == "float":
                        variables[var.name] = float(var.value)
                    elif var.type == "bool":
                        variables[var.name] = var.value.lower() == "true"
                    else:
                        variables[var.name] = var.value
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"变量 {var.name} 解析失败: {str(e)}")
                    variables[var.name] = var.value
        
        # 获取当前环境的变量,会覆盖父环境的同名变量
        current_vars = self.environment.variables.all()
        for var in current_vars:
            try:
                if var.type == "json":
                    variables[var.name] = json.loads(var.value)
                elif var.type == "int":
                    variables[var.name] = int(var.value)
                elif var.type == "float":
                    variables[var.name] = float(var.value)
                elif var.type == "bool":
                    variables[var.name] = var.value.lower() == "true"
                else:
                    variables[var.name] = var.value
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"变量 {var.name} 解析失败: {str(e)}")
                variables[var.name] = var.value
                
        # 合并接口变量,接口变量优先级更高
        variables.update(self.interface.variables or {})
                
        return variables

    def _prepare_request_data(self):
        """准备请求数据，包括请求头、参数和请求体"""
        data = {}
        
        # 处理请求头
        if hasattr(self.interface, 'headers') and self.interface.headers:
            headers = {}
            if isinstance(self.interface.headers, dict):
                # 如果是字典格式，直接使用
                headers = self.interface.headers
            elif isinstance(self.interface.headers, list):
                # 如果是列表格式，转换为字典
                for header in self.interface.headers:
                    if isinstance(header, dict) and header.get('enabled', True):
                        headers[header['key']] = header['value']
            
            if headers:
                data['headers'] = headers
        
        # 处理请求参数
        if hasattr(self.interface, 'params') and self.interface.params:
            params = {}
            if isinstance(self.interface.params, dict):
                # 如果是字典格式，直接使用
                params = self.interface.params
            elif isinstance(self.interface.params, list):
                # 如果是列表格式，转换为字典
                for param in self.interface.params:
                    if isinstance(param, dict) and param.get('enabled', True):
                        params[param['key']] = param['value']
            
            if params:
                data['params'] = params
        
        # 处理请求体
        if hasattr(self.interface, 'body') and self.interface.body is not None:
            body = self.interface.body
            
            if body == "null":
                body = None
            elif isinstance(body, dict) and 'type' in body and 'content' in body:
                # 处理带类型的请求体
                body_type = body['type']
                content = body['content']
                
                if body_type == 'raw' and isinstance(content, str):
                    try:
                        # 尝试解析JSON字符串
                        body = json.loads(content)
                    except:
                        # 解析失败，保持原始内容
                        body = content
                else:
                    # 使用内容部分
                    body = content
            
            data['body'] = body
        
        return data