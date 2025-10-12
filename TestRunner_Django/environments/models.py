from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project

User = get_user_model()

class Environment(models.Model):
    """环境配置模型"""
    name = models.CharField("环境名称", max_length=100)
    base_url = models.URLField("基础URL", max_length=200)
    verify_ssl = models.BooleanField("验证SSL证书", default=True)
    description = models.TextField("环境描述", blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='environments',
        verbose_name="所属项目"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="父环境"
    )
    database_config = models.ForeignKey(
        'database_configs.DatabaseConfig',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='environments',
        verbose_name="数据库配置"
    )
    is_active = models.BooleanField("是否激活", default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_environments',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "测试环境"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        unique_together = ['name', 'project']

    def __str__(self):
        return f"{self.project.name}-{self.name}"
        
    def clean(self):
        """验证环境数据"""
        from django.core.exceptions import ValidationError
        # 验证父环境必须属于同一个项目
        if self.parent and self.parent.project != self.project:
            raise ValidationError({'parent': '父环境必须属于同一个项目'})
            
        # 验证不能将自己设为父环境
        if self.parent and self.parent.id == self.id:
            raise ValidationError({'parent': '不能将自己设为父环境'})
            
        # 验证不能形成循环继承
        if self.parent:
            parent = self.parent
            while parent:
                if parent.parent and parent.parent.id == self.id:
                    raise ValidationError({'parent': '不能形成循环继承'})
                parent = parent.parent
                
        # 验证数据库配置必须属于同一个项目
        if self.database_config and self.database_config.project != self.project:
            raise ValidationError({'database_config': '数据库配置必须属于同一个项目'})
                
    def get_all_variables(self):
        """获取所有变量(包括继承的)"""
        variables = {}
        
        # 获取父环境的变量
        if self.parent:
            parent_vars = self.parent.get_all_variables()
            # 确保父环境返回的是字典
            if isinstance(parent_vars, dict):
                variables.update(parent_vars)
            
        # 获取当前环境的变量(会覆盖父环境的同名变量)
        for var in self.variables.all():
            try:
                variables[var.name] = var.get_typed_value()
            except Exception as e:
                # 如果变量值解析失败，使用原始字符串值
                variables[var.name] = var.value
            
        return variables
        
    def get_database_config(self):
        """获取数据库配置(包括继承的)"""
        # 当前环境有数据库配置则直接返回
        if self.database_config:
            return self.database_config
            
        # 否则从父环境中获取
        if self.parent:
            return self.parent.get_database_config()
            
        # 都没有则返回None
        return None

class EnvironmentVariable(models.Model):
    """环境变量模型"""
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name='variables',
        verbose_name="所属环境"
    )
    name = models.CharField("变量名", max_length=100)
    value = models.TextField("变量值")
    type = models.CharField(
        "变量类型",
        max_length=20,
        choices=[
            ('string', '字符串'),
            ('integer', '整数'),
            ('float', '浮点数'),
            ('boolean', '布尔值'),
            ('json', 'JSON对象'),
            ('list', '列表'),
            ('dict', '字典')
        ],
        default='string'
    )
    description = models.CharField("描述", max_length=200, blank=True)
    is_sensitive = models.BooleanField("是否敏感数据", default=False)
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "环境变量"
        verbose_name_plural = verbose_name
        ordering = ['name']
        unique_together = ['environment', 'name']

    def __str__(self):
        return f"{self.environment.name}-{self.name}"
        
    def clean(self):
        """验证变量值"""
        from django.core.exceptions import ValidationError
        import json
        
        try:
            if self.type == 'integer':
                int(self.value)
            elif self.type == 'float':
                float(self.value)
            elif self.type == 'boolean':
                if self.value.lower() not in ['true', 'false']:
                    raise ValueError
            elif self.type == 'json':
                json.loads(self.value)
        except (ValueError, json.JSONDecodeError):
            raise ValidationError({
                'value': f'变量值不符合{self.get_type_display()}类型'
            })
            
    def get_typed_value(self):
        """获取类型转换后的变量值"""
        import json
        
        try:
            if self.type == 'integer':
                return int(self.value)
            elif self.type == 'float':
                return float(self.value)
            elif self.type == 'boolean':
                return self.value.lower() == 'true'
            elif self.type == 'json':
                return json.loads(self.value)
            elif self.type == 'list':
                return json.loads(self.value)
            elif self.type == 'dict':
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, json.JSONDecodeError):
            # 如果转换失败则返回原始值
            return self.value

class GlobalRequestHeader(models.Model):
    """全局请求头参数模型，针对项目级别"""
    name = models.CharField("请求头名称", max_length=100)
    value = models.TextField("请求头值")
    description = models.CharField("描述", max_length=200, blank=True)
    is_enabled = models.BooleanField("是否启用", default=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='global_headers',
        verbose_name="所属项目"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_headers',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "全局请求头"
        verbose_name_plural = verbose_name
        ordering = ['name']
        unique_together = ['name', 'project']

    def __str__(self):
        return f"{self.project.name}-{self.name}"
