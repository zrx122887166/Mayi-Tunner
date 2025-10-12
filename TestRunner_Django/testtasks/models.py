from django.db import models
from django.conf import settings
from django.utils import timezone


class TestTaskSuite(models.Model):
    """测试任务集模型"""
    name = models.CharField("任务集名称", max_length=100)
    description = models.TextField("任务集描述", blank=True)
    
    # 执行配置
    priority = models.CharField(
        "优先级",
        max_length=2,
        choices=[
            ('P0', 'P0 - 最高'),
            ('P1', 'P1 - 较高'),
            ('P2', 'P2 - 普通'),
            ('P3', 'P3 - 较低')
        ],
        default='P2',
        help_text="P0: 核心功能，P1: 重要功能，P2: 一般功能，P3: 边缘功能"
    )
    
    # 执行策略
    fail_fast = models.BooleanField(
        "快速失败",
        default=False,
        help_text="当一个用例执行失败时，是否停止执行后续用例"
    )
    
    # 组织信息
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='test_task_suites',
        verbose_name="所属项目"
    )
    
    # 创建信息
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_task_suites',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)
    
    class Meta:
        verbose_name = "测试任务集"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        unique_together = ['name', 'project']

    def __str__(self):
        return self.name


class TestTaskCase(models.Model):
    """测试任务用例关联模型"""
    task_suite = models.ForeignKey(
        TestTaskSuite,
        on_delete=models.CASCADE,
        related_name='task_cases',
        verbose_name="所属任务集"
    )
    testcase = models.ForeignKey(
        'testcases.TestCase',
        on_delete=models.CASCADE,
        related_name='task_cases',
        verbose_name="测试用例"
    )
    order = models.IntegerField("执行顺序", default=0)
    
    class Meta:
        verbose_name = "任务用例关联"
        verbose_name_plural = verbose_name
        ordering = ['order']
        unique_together = ['task_suite', 'testcase']

    def __str__(self):
        return f"{self.task_suite.name}-{self.testcase.name}"


class TestTaskExecution(models.Model):
    """测试任务执行记录模型"""
    STATUS_CHOICES = [
        ('pending', '等待执行'),
        ('running', '执行中'),
        ('completed', '已完成'),
        ('failed', '执行失败'),
        ('canceled', '已取消')
    ]
    
    task_suite = models.ForeignKey(
        TestTaskSuite,
        on_delete=models.CASCADE,
        related_name='executions',
        verbose_name="任务集"
    )
    
    # 执行状态
    status = models.CharField(
        "执行状态",
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # 执行环境
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_executions',
        verbose_name="执行环境"
    )
    
    # 执行信息
    start_time = models.DateTimeField("开始时间", null=True, blank=True)
    end_time = models.DateTimeField("结束时间", null=True, blank=True)
    
    # 统计信息
    total_count = models.IntegerField("总用例数", default=0)
    success_count = models.IntegerField("成功用例数", default=0)
    fail_count = models.IntegerField("失败用例数", default=0)
    error_count = models.IntegerField("错误用例数", default=0)
    
    # 执行人
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_executions',
        verbose_name="执行人"
    )
    
    # 任务ID，用于异步任务
    task_id = models.CharField("任务ID", max_length=100, blank=True)
    
    # 创建信息
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "任务执行记录"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']

    def __str__(self):
        return f"{self.task_suite.name}-{self.created_time.strftime('%Y%m%d%H%M%S')}"
    
    @property
    def duration(self):
        """计算执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0
    
    @property
    def success_rate(self):
        """计算成功率（浮点数，范围0-1，保留两位小数）"""
        if self.total_count > 0:
            return round(self.success_count / self.total_count, 2)
        return 0.00
    
    def start(self):
        """开始执行"""
        self.status = 'running'
        self.start_time = timezone.now()
        self.save()
    
    def complete(self, success_count, fail_count, error_count):
        """完成执行"""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.success_count = success_count
        self.fail_count = fail_count
        self.error_count = error_count
        self.save()
    
    def fail(self):
        """执行失败"""
        self.status = 'failed'
        self.end_time = timezone.now()
        self.save()
    
    def cancel(self):
        """取消执行"""
        self.status = 'canceled'
        self.end_time = timezone.now()
        self.save()


class TestTaskCaseResult(models.Model):
    """测试任务用例执行结果模型"""
    execution = models.ForeignKey(
        TestTaskExecution,
        on_delete=models.CASCADE,
        related_name='case_results',
        verbose_name="执行记录"
    )
    testcase = models.ForeignKey(
        'testcases.TestCase',
        on_delete=models.CASCADE,
        related_name='task_results',
        verbose_name="测试用例"
    )
    report = models.ForeignKey(
        'testcases.TestReport',
        on_delete=models.SET_NULL,
        null=True,
        related_name='task_results',
        verbose_name="测试报告"
    )
    
    # 执行状态
    status = models.CharField(
        "执行状态",
        max_length=20,
        choices=[
            ('pending', '等待执行'),
            ('running', '执行中'),
            ('success', '成功'),
            ('failure', '失败'),
            ('error', '错误'),
            ('skipped', '已跳过')
        ],
        default='pending'
    )
    
    # 执行信息
    start_time = models.DateTimeField("开始时间", null=True, blank=True)
    end_time = models.DateTimeField("结束时间", null=True, blank=True)
    duration = models.FloatField("执行时长(s)", default=0)
    
    # 错误信息
    error_message = models.TextField("错误信息", blank=True)
    
    class Meta:
        verbose_name = "用例执行结果"
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        return f"{self.execution}-{self.testcase.name}"
