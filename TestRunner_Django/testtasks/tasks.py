import logging
from celery import shared_task
from .services import TestTaskExecutionService

logger = logging.getLogger('testrunner')


@shared_task
def execute_task_async(execution_id):
    """
    异步执行测试任务
    
    Args:
        execution_id: 执行记录ID
    """
    logger.info(f"开始异步执行任务[ID={execution_id}]")
    try:
        TestTaskExecutionService.execute_task_async(execution_id)
        logger.info(f"异步执行任务[ID={execution_id}]完成")
        return True
    except Exception as e:
        logger.error(f"异步执行任务[ID={execution_id}]异常: {str(e)}")
        return False 