from typing import Dict, List, Optional, Tuple
import logging
from django.utils import timezone
from django.db import transaction
from interfaces.models import Interface
from .models import TestCase, TestCaseStep, TestReport, TestReportDetail
from .runner import TestCaseRunner

logger = logging.getLogger('testrunner')


class TestCaseService:
    """测试用例服务类"""
    
    @staticmethod
    def create_testcase(data: Dict, user) -> TestCase:
        """
        创建测试用例
        
        Args:
            data: 用例数据
            user: 创建用户
            
        Returns:
            TestCase: 创建的测试用例
        """
        # 1. 提取步骤数据
        steps_data = data.pop('steps_info', [])
        
        # 2. 创建用例
        with transaction.atomic():
            # 2.1 创建用例基本信息
            testcase = TestCase.objects.create(
                created_by=user,
                **data
            )
            
            # 2.2 创建测试步骤
            for index, step_data in enumerate(steps_data, 1):
                # 获取接口信息
                interface_id = step_data.pop('interface_id')
                interface = Interface.objects.get(id=interface_id)
                
                # 复制接口数据
                interface_data = {
                    'method': interface.method,
                    'url': interface.url,
                    'headers': interface.headers,
                    'params': interface.params,
                    'body': interface.body,
                    'validators': interface.validators,
                    'extract': interface.extract,
                    'setup_hooks': interface.setup_hooks,
                    'teardown_hooks': interface.teardown_hooks,
                    'variables': interface.variables
                }
                
                # 创建测试步骤
                TestCaseStep.objects.create(
                    testcase=testcase,
                    order=index,
                    interface_data=interface_data,
                    origin_interface=interface,
                    **step_data
                )
        
        return testcase

    @staticmethod
    def validate_testcase_data(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证测试用例数据
        
        Args:
            data: 用例数据
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误信息)
        """
        # 1. 验证基本信息
        required_fields = ['name', 'project']
        for field in required_fields:
            if field not in data:
                return False, f'缺少必填字段: {field}'
        
        # 2. 验证步骤数据
        steps = data.get('steps_info', [])
        if not steps:
            return False, '至少需要一个测试步骤'
            
        # 3. 验证每个步骤
        for index, step in enumerate(steps):
            # 验证步骤基本信息
            if 'name' not in step:
                return False, f'第 {index + 1} 个步骤缺少名称'
            if 'interface_id' not in step:
                return False, f'第 {index + 1} 个步骤缺少接口ID'
        
        return True, None


class TestExecutionService:
    """测试执行服务类"""
    
    @staticmethod
    def _prepare_config(config: Dict, environment: Optional[Dict] = None) -> Dict:
        """
        准备配置数据，合并环境配置和用例配置
        
        Args:
            config: 用例配置数据
            environment: 环境配置数据
            
        Returns:
            Dict: 合并后的配置数据
        """
        logger.info(f"准备处理配置数据: config={config}, environment={environment}")
        
        # 1. 确保config是字典
        if not isinstance(config, dict):
            logger.warning(f"配置不是字典类型: {type(config)}, 值: {config}")
            config = {}
            
        # 2. 确保environment是字典
        if not isinstance(environment, dict):
            logger.warning(f"环境配置不是字典类型: {type(environment)}, 值: {environment}")
            environment = {}
            
        # 3. 确保环境变量是字典类型
        env_variables = environment.get('variables', {})
        if not isinstance(env_variables, dict):
            logger.warning(f"环境变量不是字典类型: {type(env_variables)}, 值: {env_variables}")
            # 尝试将字符串解析为字典
            if isinstance(env_variables, str):
                # 如果是空字符串，直接使用空字典
                if env_variables.strip() == '':
                    env_variables = {}
                else:
                    try:
                        import json
                        env_variables = json.loads(env_variables)
                        if not isinstance(env_variables, dict):
                            logger.error(f"解析后的环境变量仍不是字典: {type(env_variables)}")
                            env_variables = {}
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"无法解析环境变量字符串: {e}")
                        env_variables = {}
            else:
                env_variables = {}
            
        # 4. 确保用例变量也是字典类型
        case_variables = config.get('variables', {})
        if not isinstance(case_variables, dict):
            logger.warning(f"用例变量不是字典类型: {type(case_variables)}, 值: {case_variables}")
            # 尝试将字符串解析为字典
            if isinstance(case_variables, str):
                # 如果是空字符串，直接使用空字典
                if case_variables.strip() == '':
                    case_variables = {}
                else:
                    try:
                        import json
                        case_variables = json.loads(case_variables)
                        if not isinstance(case_variables, dict):
                            logger.error(f"解析后的用例变量仍不是字典: {type(case_variables)}")
                            case_variables = {}
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"无法解析用例变量字符串: {e}")
                        case_variables = {}
            else:
                case_variables = {}
        
        # 5. 确保 parameters 也是字典类型
        case_parameters = config.get('parameters', {})
        if not isinstance(case_parameters, dict):
            logger.warning(f"用例参数不是字典类型: {type(case_parameters)}, 值: {case_parameters}")
            # 尝试将字符串解析为字典
            if isinstance(case_parameters, str):
                # 如果是空字符串，直接使用空字典
                if case_parameters.strip() == '':
                    case_parameters = {}
                else:
                    try:
                        import json
                        case_parameters = json.loads(case_parameters)
                        if not isinstance(case_parameters, dict):
                            logger.error(f"解析后的用例参数仍不是字典: {type(case_parameters)}")
                            case_parameters = {}
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"无法解析用例参数字符串: {e}")
                        case_parameters = {}
            else:
                case_parameters = {}
        
        # 6. 合并配置
        final_config = {
            # base_url: 优先使用用例的，如果用例没设置则使用环境的
            "base_url": config.get('base_url') or environment.get('base_url', ''),
            
            # verify: 优先使用用例的，如果用例没设置则使用环境的
            "verify": config.get('verify', environment.get('verify_ssl', True)),
            
            # variables: 环境变量和用例变量合并，用例变量优先级更高
            "variables": {
                **env_variables,
                **case_variables
            },
            
            # export: 只使用用例的配置，确保是列表
            "export": config.get('export', []),
            
            # parameters: 只使用用例的配置，使用处理后的值
            "parameters": case_parameters
        }
        
        logger.info(f"配置合并结果: {final_config}")
        return final_config
    
    @staticmethod
    def run_testcase(testcase: TestCase, environment: Optional[Dict] = None, user = None) -> TestReport:
        """
        执行测试用例
        
        Args:
            testcase: 测试用例
            environment: 环境变量
            user: 执行用户
            
        Returns:
            TestReport: 测试报告
        """
        # 1. 处理配置数据
        logger.info(f"处理用例[{testcase.name}]配置前: {testcase.config}")
        config = TestExecutionService._prepare_config(testcase.config, environment)
        testcase.config = config
        logger.info(f"处理用例[{testcase.name}]配置后: {config}")
        
        # 2. 创建执行器并运行测试
        runner = TestCaseRunner(testcase)
        runner.run_testcase(environment)
        
        # 3. 获取结果
        summary = runner.get_summary()
        step_results = runner.get_step_results()
        
        # 4. 创建测试报告
        with transaction.atomic():
            # 4.1 创建报告
            report = TestReport.objects.create(
                name=f"{testcase.name}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                status='success' if summary['success'] else 'failure',
                success_count=len([r for r in step_results if r['success']]),
                fail_count=len([r for r in step_results if not r['success']]),
                error_count=0,
                duration=summary['time']['duration'],
                summary=summary,
                testcase=testcase,
                executed_by=user,
                environment_id=environment.get('id') if environment else None  # 保存环境ID
            )
            
            # 4.2 创建详细结果
            # 获取所有步骤，创建ID到步骤的映射和顺序到步骤的映射
            steps_by_id = {step.id: step for step in testcase.steps.all()}
            steps_by_order = {step.order: step for step in testcase.steps.all()}
            
            for i, step_result in enumerate(step_results):
                step_name = step_result['name']
                
                try:
                    # 首先尝试通过顺序位置获取步骤（最可靠的方式）
                    step = steps_by_order.get(i+1)  # 步骤顺序通常从1开始
                    
                    # 如果找不到步骤，则尝试通过名称查找对应的步骤ID
                    if step is None:
                        logger.warning(f"找不到顺序为 {i+1} 的步骤，尝试通过名称 '{step_name}' 匹配")
                        # 获取按顺序排列的所有步骤
                        ordered_steps = list(testcase.steps.all().order_by('order'))
                        # 确保索引在范围内
                        if i < len(ordered_steps):
                            step = ordered_steps[i]
                        else:
                            logger.error(f"步骤索引 {i} 超出范围，总步骤数: {len(ordered_steps)}")
                            continue
                    
                    # 检查验证器结果，确保断言失败时步骤被标记为失败
                    step_success = step_result['success']
                    validators = step_result['data']['validators']
                    
                    # 如果验证器中有任何断言失败，则将步骤标记为失败
                    if validators:
                        # 检查验证器的整体成功状态
                        if 'success' in validators and validators['success'] is False:
                            step_success = False
                        # 检查每个验证器的结果
                        if 'validate_extractor' in validators:
                            for validator in validators['validate_extractor']:
                                if validator.get('check_result') == 'fail':
                                    step_success = False
                                    logger.warning(f"步骤 '{step_name}' 的断言失败: {validator.get('check')} {validator.get('comparator')} {validator.get('expect_value')}")
                                    break
                    
                    TestReportDetail.objects.create(
                        report=report,
                        step=step,
                        success=step_success,
                        elapsed=step_result['elapsed'],
                        request=step_result['data']['request'],
                        response=step_result['data']['response'],
                        validators=step_result['data']['validators'],
                        extracted_variables=step_result['data']['extracted_variables'],
                        attachment=step_result['attachment']
                    )
                except Exception as e:
                    logger.error(f"创建测试报告详情失败: {str(e)}")
                    # 继续处理下一个步骤，不中断整个流程
                    continue
        
        return report

    @staticmethod
    def run_batch(testcases: List[TestCase], environment: Optional[Dict] = None, user = None) -> List[TestReport]:
        """
        批量执行测试用例
        
        Args:
            testcases: 测试用例列表
            environment: 环境变量
            user: 执行用户
            
        Returns:
            List[TestReport]: 测试报告列表
        """
        reports = []
        for testcase in testcases:
            report = TestExecutionService.run_testcase(testcase, environment, user)
            reports.append(report)
        return reports

    @staticmethod
    def get_statistics(reports: List[TestReport]) -> Dict:
        """
        获取统计信息
        
        Args:
            reports: 测试报告列表
            
        Returns:
            Dict: 统计信息
        """
        total = len(reports)
        if not total:
            return {
                'total': 0,
                'success': 0,
                'failure': 0,
                'error': 0,
                'success_rate': '0%'
            }
            
        success = len([r for r in reports if r.status == 'success'])
        failure = len([r for r in reports if r.status == 'failure'])
        error = len([r for r in reports if r.status == 'error'])
        
        return {
            'total': total,
            'success': success,
            'failure': failure,
            'error': error,
            'success_rate': f"{(success / total * 100):.2f}%"
        }
