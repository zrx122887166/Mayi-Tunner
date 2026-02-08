from django.db import models
from django.conf import settings


class TestCaseTag(models.Model):
    """测试用例标签"""
    name = models.CharField("标签名称", max_length=50)
    color = models.CharField(
        "标签颜色",
        max_length=20,
        default="#1890ff",
        help_text="标签显示的颜色，例如：#1890ff"
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='testcase_tags',
        verbose_name="所属项目"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tags',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "用例标签"
        verbose_name_plural = verbose_name
        ordering = ['name']
        unique_together = ['name', 'project']

    def __str__(self):
        return self.name


class TestCaseGroup(models.Model):
    """测试用例分组"""
    name = models.CharField("分组名称", max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="父分组"
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='testcase_groups',
        verbose_name="所属项目"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "用例分组"
        verbose_name_plural = verbose_name
        ordering = ['name']
        unique_together = ['name', 'parent', 'project']

    def __str__(self):
        return self.name

    def get_full_path(self):
        """获取完整路径"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.append(parent.name)
            parent = parent.parent
        return ' / '.join(reversed(path))


class TestCase(models.Model):
    """测试用例模型"""
    name = models.CharField("用例名称", max_length=100)
    description = models.TextField("用例描述", blank=True)
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
    
    # 配置信息
    config = models.JSONField(
        "用例配置",
        default=dict,
        help_text={
            "base_url": "基础URL",
            "variables": "变量配置",
            "parameters": "参数化数据",
            "export": "导出变量列表",
            "verify": "SSL验证"
        }
    )
    
    # 组织信息
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.CASCADE,
        related_name='testcases',
        verbose_name="所属项目"
    )
    group = models.ForeignKey(
        TestCaseGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testcases',
        verbose_name="所属分组"
    )
    tags = models.ManyToManyField(
        TestCaseTag,
        blank=True,
        related_name='testcases',
        verbose_name="标签"
    )
    
    # 创建信息
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_testcases',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)
    
    class Meta:
        verbose_name = "测试用例"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        unique_together = ['name', 'project']

    def __str__(self):
        return self.name


class TestCaseStep(models.Model):
    """测试步骤模型"""
    name = models.CharField("步骤名称", max_length=100)
    order = models.IntegerField("执行顺序")
    
    # 接口数据副本
    interface_data = models.JSONField(
        "接口数据",
        help_text={
            "method": "请求方法",
            "url": "接口地址",
            "headers": "请求头",
            "params": "查询参数",
            "body": "请求体",
            "validators": "断言规则",
            "extract": "变量提取",
            "setup_hooks": "前置钩子",
            "teardown_hooks": "后置钩子",
            "variables": "变量"
        }
    )
    
    # 关联关系
    testcase = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name="所属用例"
    )
    origin_interface = models.ForeignKey(
        'interfaces.Interface',
        on_delete=models.SET_NULL,
        null=True,
        related_name='related_steps',
        verbose_name="关联接口"
    )
    
    # 同步配置
    sync_fields = models.JSONField(
        "同步字段配置",
        default=list,
        help_text=[
            "method",      # 请求方法
            "url",         # 接口地址
            "headers",     # 请求头
            "params",      # 查询参数
            "body",        # 请求体
            "setup_hooks", # 前置钩子
            "teardown_hooks", # 后置钩子
            "variables",   # 变量
            "validators",  # 断言规则
            "extract"      # 提取变量
        ]
    )
    last_sync_time = models.DateTimeField(
        "最后同步时间",
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = "测试步骤"
        verbose_name_plural = verbose_name
        ordering = ['order']
        unique_together = ['testcase', 'order']

    def __str__(self):
        return f"{self.testcase.name}-{self.name}"


class TestReport(models.Model):
    """测试报告"""
    name = models.CharField("报告名称", max_length=200)
    status = models.CharField(
        "执行状态",
        max_length=20,
        choices=[
            ('success', '成功'),
            ('failure', '失败'),
            ('error', '错误')
        ]
    )
    
    # 统计信息
    success_count = models.IntegerField("成功步骤数", default=0)
    fail_count = models.IntegerField("失败步骤数", default=0)
    error_count = models.IntegerField("错误步骤数", default=0)
    duration = models.FloatField("执行时长(s)")
    
    # 执行信息
    start_time = models.DateTimeField("开始时间", auto_now_add=True)
    summary = models.JSONField(
        "执行汇总",
        help_text={
            "name": "用例名称",
            "success": "是否成功",
            "time": {
                "start_at": "开始时间",
                "duration": "执行时长"
            },
            "in_out": {
                "config_vars": "配置变量",
                "export_vars": "导出变量"
            },
            "log": "执行日志"
        }
    )
    
    # 关联关系
    testcase = models.ForeignKey(
        TestCase,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name="关联用例"
    )
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
        verbose_name="执行环境"
    )
    executed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='executed_reports',
        verbose_name="执行人"
    )
    
    class Meta:
        verbose_name = "测试报告"
        verbose_name_plural = verbose_name
        ordering = ['-start_time']

    def __str__(self):
        return self.name


class TestReportDetail(models.Model):
    """测试报告详情"""
    report = models.ForeignKey(
        TestReport,
        on_delete=models.CASCADE,
        related_name='details',
        verbose_name="测试报告"
    )
    step = models.ForeignKey(
        TestCaseStep,
        on_delete=models.SET_NULL,
        null=True,
        related_name='results',
        verbose_name="测试步骤"
    )
    
    # 执行结果
    success = models.BooleanField("是否成功")
    elapsed = models.FloatField("执行时长(ms)")
    
    # 请求信息
    request = models.JSONField(
        "请求信息",
        help_text={
            "method": "请求方法",
            "url": "请求地址",
            "headers": "请求头",
            "body": "请求体"
        }
    )
    
    # 响应信息
    response = models.JSONField(
        "响应信息",
        help_text={
            "status_code": "状态码",
            "headers": "响应头",
            "body": "响应体",
            "content_size": "响应大小",
            "response_time": "响应时间"
        }
    )
    
    # 其他信息
    validators = models.JSONField("断言结果", default=list)
    extracted_variables = models.JSONField("提取的变量", default=dict)
    attachment = models.TextField("附加信息", blank=True)
    
    class Meta:
        verbose_name = "报告详情"
        verbose_name_plural = verbose_name
        ordering = ['id']

    def __str__(self):
        report_name = self.report.name if self.report else "未知报告"
        step_name = self.step.name if self.step else "未知步骤"
        return f"{report_name}-{step_name}"
