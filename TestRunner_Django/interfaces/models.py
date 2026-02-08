from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project
from modules.models import Module

User = get_user_model()

class Interface(models.Model):
    """接口模型"""
    # 常量定义
    TYPE_HTTP = 'http'
    TYPE_SQL = 'sql'
    
    INTERFACE_TYPE_CHOICES = [
        (TYPE_HTTP, 'HTTP接口'),
        (TYPE_SQL, 'SQL接口')
    ]
    
    HTTP_METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH')
    ]
    
    SQL_METHOD_CHOICES = [
        ('fetchone', '查询单条'),
        ('fetchmany', '查询多条'),
        ('fetchall', '查询所有'),
        ('insert', '插入'),
        ('update', '更新'),
        ('delete', '删除')
    ]
    
    # 基本信息
    name = models.CharField("接口名称", max_length=100)
    type = models.CharField(
        "接口类型",
        max_length=20,
        choices=INTERFACE_TYPE_CHOICES,
        default=TYPE_HTTP
    )
    
    # HTTP接口特有字段
    method = models.CharField(
        "请求方法",
        max_length=20,
        choices=HTTP_METHOD_CHOICES,
        blank=True,
        null=True
    )
    url = models.TextField("接口地址", blank=True, null=True)
    headers = models.JSONField("请求头", default=dict, blank=True)
    params = models.JSONField("查询参数", default=dict, blank=True)
    body = models.JSONField("请求体", default=dict, blank=True)
    
    # SQL接口特有字段
    sql_method = models.CharField(
        "SQL方法",
        max_length=20,
        choices=SQL_METHOD_CHOICES,
        blank=True,
        null=True
    )
    sql = models.TextField("SQL语句", blank=True, null=True)
    sql_params = models.JSONField("SQL参数", default=dict, blank=True)
    sql_size = models.IntegerField("查询条数", default=10, blank=True, help_text="仅用于fetchmany方法")
    
    # httprunner 相关字段
    setup_hooks = models.JSONField(
        "前置钩子",
        default=list,
        blank=True,
        help_text='["${setup_hook_prepare_kwargs($request)}"]'
    )
    teardown_hooks = models.JSONField(
        "后置钩子",
        default=list,
        blank=True,
        help_text='["${teardown_hook_sleep_N_secs($response, 2)}"]'
    )
    variables = models.JSONField(
        "变量",
        default=dict,
        blank=True,
        help_text='{"username": "testuser", "password": "123456"}'
    )
    validators = models.JSONField(
        "断言规则",
        default=list,
        blank=True,
        help_text='[{"eq": ["status_code", 200]}]'
    )
    extract = models.JSONField(
        "提取变量",
        default=dict,
        blank=True,
        help_text='{"token": "body.data.token"}'
    )
    
    # 关联关系
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='interfaces',
        verbose_name="所属项目"
    )
    module = models.ForeignKey(
        Module,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='interfaces',
        verbose_name="所属模块"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_interfaces',
        verbose_name="创建人"
    )
    
    # 时间字段
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "接口"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        unique_together = ['name', 'project']

    def __str__(self):
        return f"{self.project.name}-{self.name}"

    def save(self, *args, **kwargs):
        """重写保存方法，确保模块属于同一个项目"""
        if self.module and self.module.project != self.project:
            raise ValueError("模块必须属于同一个项目")
            
        # 根据接口类型清理不必要的字段
        if self.type == self.TYPE_HTTP:
            self.sql_method = None
            self.sql = None
            self.sql_params = {}
            self.sql_size = 10
        elif self.type == self.TYPE_SQL:
            self.method = None
            self.url = None
            self.headers = {}
            self.params = {}
            self.body = {}
            
        super().save(*args, **kwargs)
        
    def get_interface_data(self):
        """获取接口数据，用于执行接口请求"""
        data = {
            'name': self.name,
            'type': self.type,
            'setup_hooks': self.setup_hooks,
            'teardown_hooks': self.teardown_hooks,
            'variables': self.variables,
            'validators': self.validators,
            'extract': self.extract,
        }
        
        if self.type == self.TYPE_HTTP:
            data.update({
                'method': self.method,
                'url': self.url,
                'headers': self.headers,
                'params': self.params,
                'body': self.body
            })
        elif self.type == self.TYPE_SQL:
            data.update({
                'method': self.sql_method,
                'sql': self.sql,
                'params': self.sql_params,
                'size': self.sql_size
            })
            
        return data

class InterfaceResult(models.Model):
    """接口执行结果"""
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name="关联接口"
    )
    environment = models.ForeignKey(
        'environments.Environment',
        on_delete=models.SET_NULL,
        null=True,
        related_name='interface_results',
        verbose_name="执行环境"
    )
    
    # 执行结果
    status = models.BooleanField("执行状态")
    elapsed = models.FloatField("响应时间(ms)")
    request = models.JSONField("请求信息")
    response = models.JSONField("响应信息")
    validation_results = models.JSONField("断言结果", default=list)
    extracted_variables = models.JSONField("提取的变量", default=dict)
    
    # 执行信息
    executed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='executed_results',
        verbose_name="执行人"
    )
    executed_time = models.DateTimeField("执行时间", auto_now_add=True)

    class Meta:
        verbose_name = "接口执行结果"
        verbose_name_plural = verbose_name
        ordering = ['-executed_time']

    def __str__(self):
        return f"{self.interface.name}-{self.executed_time}"
