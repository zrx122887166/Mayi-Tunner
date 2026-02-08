from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class DatabaseConfig(models.Model):
    """数据库配置模型"""
    
    # 数据库类型选项
    DB_TYPE_CHOICES = (
        ('mysql', _('MySQL')),
        ('postgresql', _('PostgreSQL')),
        ('sqlite', _('SQLite')),
        ('oracle', _('Oracle')),
        ('sqlserver', _('SQL Server')),
    )
    
    name = models.CharField(_("配置名称"), max_length=100)
    project = models.ForeignKey(
        'projects.Project', 
        on_delete=models.CASCADE, 
        related_name='database_configs',
        verbose_name=_("所属项目")
    )
    
    # 数据库类型，前端使用type字段
    db_type = models.CharField(_("数据库类型"), max_length=20, choices=DB_TYPE_CHOICES, default='mysql')
    
    # 数据库连接信息
    host = models.CharField(_("主机地址"), max_length=255)
    port = models.IntegerField(_("端口号"), default=3306)
    username = models.CharField(_("用户名"), max_length=100)
    password = models.CharField(_("密码"), max_length=255)
    database = models.CharField(_("数据库名"), max_length=100)
    
    # 额外配置
    charset = models.CharField(_("字符集"), max_length=50, default="utf8mb4")
    is_active = models.BooleanField(_("是否启用"), default=True)
    
    # 前端需要的额外字段
    description = models.TextField(_("描述"), blank=True, null=True)
    psm = models.CharField(_("PSM"), max_length=255, blank=True, null=True)
    verify_ssl = models.BooleanField(_("验证SSL"), default=False)
    connection_params = models.JSONField(_("连接参数"), default=dict, blank=True)
    
    # 创建和更新信息
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_database_configs',
        verbose_name=_("创建人")
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _("数据库配置")
        verbose_name_plural = _("数据库配置")
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.project.name})"
    
    @property
    def connection_string(self):
        """获取数据库连接字符串"""
        if self.db_type == 'mysql':
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
        elif self.db_type == 'postgresql':
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == 'sqlite':
            return f"sqlite:///{self.database}"
        elif self.db_type == 'oracle':
            return f"oracle://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == 'sqlserver':
            return f"mssql+pymssql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
            
    @classmethod
    def get_by_key(cls, db_key):
        """根据db_key获取数据库配置"""
        if not db_key:
            return None
        
        try:
            return cls.objects.filter(name=db_key, is_active=True).first()
        except Exception as e:
            import logging
            logger = logging.getLogger('testrunner')
            logger.error(f"获取数据库配置失败: {str(e)}")
            return None