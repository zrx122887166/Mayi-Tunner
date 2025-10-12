from typing import Dict, List, Optional, Tuple
import logging
from django.utils import timezone
from django.db import transaction, models
from testcases.models import TestCase, TestReport
from testcases.services import TestExecutionService
from .models import TestTaskSuite, TestTaskCase, TestTaskExecution, TestTaskCaseResult

logger = logging.getLogger('testrunner')


class TestTaskService:
    """测试任务服务类"""
    
    @staticmethod
    def create_task_suite(data: Dict, user) -> TestTaskSuite:
        """
        创建测试任务集
        
        Args:
            data: 任务集数据
            user: 创建用户
            
        Returns:
            TestTaskSuite: 创建的任务集
        """
        with transaction.atomic():
            # 创建任务集
            task_suite = TestTaskSuite.objects.create(
                created_by=user,
                **data
            )
        
        return task_suite
    
    @staticmethod
    def add_testcases(task_suite: TestTaskSuite, testcase_ids: List[int]) -> List[TestTaskCase]:
        """
        添加测试用例到任务集
        
        Args:
            task_suite: 任务集
            testcase_ids: 测试用例ID列表
            
        Returns:
            List[TestTaskCase]: 创建的任务用例关联列表
        """
        # 获取已存在的用例ID
        existing_ids = set(task_suite.task_cases.values_list('testcase_id', flat=True))
        
        # 过滤出新增的用例ID
        new_ids = [id for id in testcase_ids if id not in existing_ids]
        
        # 获取最大顺序值
        max_order = task_suite.task_cases.aggregate(max_order=models.Max('order'))['max_order'] or 0
        
        # 创建新的任务用例关联
        task_cases = []
        with transaction.atomic():
            for i, testcase_id in enumerate(new_ids, 1):
                try:
                    testcase = TestCase.objects.get(id=testcase_id)
                    task_case = TestTaskCase.objects.create(
                        task_suite=task_suite,
                        testcase=testcase,
                        order=max_order + i
                    )
                    task_cases.append(task_case)
                except TestCase.DoesNotExist:
                    logger.warning(f"测试用例[ID={testcase_id}]不存在，跳过添加")
                    continue
        
        return task_cases
    
    @staticmethod
    def remove_testcase(task_suite: TestTaskSuite, testcase_id: int) -> bool:
        """
        从任务集中移除测试用例
        
        Args:
            task_suite: 任务集
            testcase_id: 测试用例ID
            
        Returns:
            bool: 是否成功移除
        """
        try:
            task_case = TestTaskCase.objects.get(task_suite=task_suite, testcase_id=testcase_id)
            task_case.delete()
            
            # 重新排序
            for i, task_case in enumerate(task_suite.task_cases.all().order_by('order'), 1):
                task_case.order = i
                task_case.save()
                
            return True
        except TestTaskCase.DoesNotExist:
            logger.warning(f"任务集[{task_suite.name}]中不存在测试用例[ID={testcase_id}]")
            return False
    
    @staticmethod
    def delete_task_suite(task_suite: TestTaskSuite) -> bool:
        """
        删除测试任务集
        
        Args:
            task_suite: 任务集
            
        Returns:
            bool: 是否成功删除
        """
        try:
            task_suite.delete()
            return True
        except Exception as e:
            logger.error(f"删除任务集[{task_suite.name}]失败: {str(e)}")
            return False


class TestTaskExecutionService:
    """测试任务执行服务类"""
    
    @staticmethod
    def create_execution(task_suite: TestTaskSuite, environment_id: Optional[int] = None, user = None) -> TestTaskExecution:
        """
        创建测试任务执行记录
        
        Args:
            task_suite: 任务集
            environment_id: 环境ID
            user: 执行用户
            
        Returns:
            TestTaskExecution: 创建的执行记录
        """
        with transaction.atomic():
            # 创建执行记录
            execution = TestTaskExecution.objects.create(
                task_suite=task_suite,
                environment_id=environment_id,
                executed_by=user,
                total_count=task_suite.task_cases.count()
            )
            
            # 创建用例执行结果
            for task_case in task_suite.task_cases.all().order_by('order'):
                TestTaskCaseResult.objects.create(
                    execution=execution,
                    testcase=task_case.testcase
                )
        
        return execution
    
    @staticmethod
    def execute_task(execution: TestTaskExecution) -> None:
        """
        执行测试任务
        
        Args:
            execution: 执行记录
        """
        # 标记开始执行
        execution.start()
        
        # 获取环境信息
        environment = None
        if execution.environment:
            try:
                # 获取所有环境变量，包括继承的变量
                env_variables = execution.environment.get_all_variables()
                # 确保 env_variables 是字典类型
                if isinstance(env_variables, str):
                    # 如果返回的是字符串，尝试解析为 JSON
                    try:
                        import json
                        env_variables = json.loads(env_variables)
                        logger.info(f"环境变量从字符串解析为字典: {env_variables}")
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"环境变量字符串无法解析为JSON: {e}")
                        env_variables = {}
                elif not isinstance(env_variables, dict):
                    logger.warning(f"环境变量返回非字典类型: {type(env_variables)}, 使用空字典")
                    env_variables = {}
                    
                environment = {
                    'id': execution.environment.id,
                    'name': execution.environment.name,
                    'base_url': execution.environment.base_url,
                    'variables': env_variables,  # 使用 get_all_variables() 获取的字典
                    'verify_ssl': execution.environment.verify_ssl
                }
                logger.info(f"环境[{execution.environment.name}]配置: base_url={execution.environment.base_url}, variables={env_variables}")
            except Exception as e:
                logger.error(f"获取环境信息时发生错误: {str(e)}", exc_info=True)
                # 使用默认环境配置
                environment = {
                    'id': execution.environment.id if execution.environment else None,
                    'name': execution.environment.name if execution.environment else 'Unknown',
                    'base_url': execution.environment.base_url if execution.environment else '',
                    'variables': {},
                    'verify_ssl': True
                }
                logger.warning(f"使用默认环境配置: {environment}")
        
        # 获取任务集
        task_suite = execution.task_suite
        
        # 获取所有用例结果
        case_results = execution.case_results.all().order_by('id')
        
        # 执行统计
        success_count = 0
        fail_count = 0
        error_count = 0
        
        # 执行每个用例
        for case_result in case_results:
            # 标记开始执行
            case_result.status = 'running'
            case_result.start_time = timezone.now()
            case_result.save()
            
            try:
                # 执行测试用例
                testcase = case_result.testcase
                report = TestExecutionService.run_testcase(testcase, environment, execution.executed_by)
                
                # 更新用例结果
                case_result.report = report
                case_result.end_time = timezone.now()
                case_result.duration = (case_result.end_time - case_result.start_time).total_seconds()
                
                # 根据报告状态更新结果状态
                if report.status == 'success':
                    case_result.status = 'success'
                    success_count += 1
                else:
                    case_result.status = 'failure'
                    fail_count += 1
                
                case_result.save()
                
                # 如果设置了快速失败且当前用例执行失败，则停止执行后续用例
                if task_suite.fail_fast and report.status != 'success':
                    logger.info(f"任务集[{task_suite.name}]设置了快速失败，当前用例[{testcase.name}]执行失败，停止执行后续用例")
                    # 将剩余用例标记为已跳过
                    for remaining in case_results.filter(status='pending'):
                        remaining.status = 'skipped'
                        remaining.save()
                    break
                
            except Exception as e:
                # 处理执行异常
                logger.error(f"执行用例[{case_result.testcase.name}]异常: {str(e)}")
                case_result.status = 'error'
                case_result.end_time = timezone.now()
                case_result.duration = (case_result.end_time - case_result.start_time).total_seconds()
                case_result.error_message = str(e)
                case_result.save()
                error_count += 1
                
                # 如果设置了快速失败，则停止执行后续用例
                if task_suite.fail_fast:
                    logger.info(f"任务集[{task_suite.name}]设置了快速失败，当前用例[{case_result.testcase.name}]执行异常，停止执行后续用例")
                    # 将剩余用例标记为已跳过
                    for remaining in case_results.filter(status='pending'):
                        remaining.status = 'skipped'
                        remaining.save()
                    break
        
        # 更新执行记录
        execution.complete(success_count, fail_count, error_count)
        
    @staticmethod
    def execute_task_async(execution_id: int) -> None:
        """
        异步执行测试任务
        
        Args:
            execution_id: 执行记录ID
        """
        try:
            # 获取执行记录
            execution = TestTaskExecution.objects.get(id=execution_id)
            
            # 执行任务
            TestTaskExecutionService.execute_task(execution)
            
        except TestTaskExecution.DoesNotExist:
            logger.error(f"执行记录[ID={execution_id}]不存在")
        except Exception as e:
            logger.error(f"异步执行任务异常: {str(e)}")
            
            # 尝试更新执行状态
            try:
                execution = TestTaskExecution.objects.get(id=execution_id)
                execution.fail()
            except:
                pass 