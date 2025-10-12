from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SyncConfig(models.Model):
    """同步配置"""
    name = models.CharField(
        verbose_name='配置名称',
        max_length=100
    )
    description = models.TextField(
        verbose_name='配置描述',
        blank=True
    )
    interface = models.ForeignKey(
        'interfaces.Interface',
        verbose_name='关联接口',
        on_delete=models.CASCADE,
        related_name='sync_configs'
    )
    testcase = models.ForeignKey(
        'testcases.TestCase',
        verbose_name='关联用例',
        on_delete=models.CASCADE,
        related_name='sync_configs'
    )
    step = models.ForeignKey(
        'testcases.TestCaseStep',
        verbose_name='关联步骤',
        on_delete=models.CASCADE,
        related_name='sync_configs'
    )
    sync_fields = models.JSONField(
        verbose_name='同步字段',
        default=list,
        help_text='配置需要同步的字段列表'
    )
    sync_enabled = models.BooleanField(
        verbose_name='是否启用',
        default=True
    )
    sync_mode = models.CharField(
        verbose_name='同步模式',
        max_length=20,
        choices=[
            ('manual', '手动同步'),
            ('auto', '自动同步')
        ],
        default='manual'
    )
    sync_trigger = models.JSONField(
        verbose_name='触发条件',
        default=dict,
        help_text='自动同步的触发条件配置'
    )
    created_by = models.ForeignKey(
        User,
        verbose_name='创建人',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_sync_configs'
    )
    created_time = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间',
        auto_now=True
    )

    class Meta:
        verbose_name = '同步配置'
        verbose_name_plural = verbose_name
        unique_together = ['interface', 'testcase', 'step']
        ordering = ['-updated_time']

    def __str__(self):
        return f"{self.name} ({self.interface} -> {self.testcase})"

class SyncHistory(models.Model):
    """同步历史"""
    sync_config = models.ForeignKey(
        'SyncConfig',
        verbose_name='同步配置',
        on_delete=models.CASCADE,
        related_name='sync_histories'
    )
    sync_type = models.CharField(
        verbose_name='同步类型',
        max_length=20,
        choices=[
            ('manual', '手动同步'),
            ('auto', '自动同步'),
            ('batch', '批量同步')
        ]
    )
    sync_status = models.CharField(
        verbose_name='同步状态',
        max_length=20,
        choices=[
            ('success', '成功'),
            ('failed', '失败'),
            ('partial', '部分成功')
        ]
    )
    sync_fields = models.JSONField(
        verbose_name='同步字段',
        help_text='本次同步的字段列表'
    )
    old_data = models.JSONField(
        verbose_name='同步前数据'
    )
    new_data = models.JSONField(
        verbose_name='同步后数据'
    )
    error_message = models.TextField(
        verbose_name='错误信息',
        blank=True
    )
    operator = models.ForeignKey(
        User,
        verbose_name='操作人',
        on_delete=models.SET_NULL,
        null=True
    )
    sync_time = models.DateTimeField(
        verbose_name='同步时间',
        auto_now_add=True
    )

    class Meta:
        verbose_name = '同步历史'
        verbose_name_plural = verbose_name
        ordering = ['-sync_time']

    def __str__(self):
        return f"{self.sync_config.name} - {self.sync_time}"

class GlobalSyncConfig(models.Model):
    """全局同步配置"""
    name = models.CharField(
        verbose_name='配置名称',
        max_length=100
    )
    description = models.TextField(
        verbose_name='配置描述',
        blank=True
    )
    project = models.ForeignKey(
        'projects.Project',
        verbose_name='所属项目',
        on_delete=models.CASCADE,
        related_name='global_sync_configs'
    )
    sync_fields = models.JSONField(
        verbose_name='同步字段',
        default=list,
        help_text='配置需要同步的字段列表'
    )
    sync_enabled = models.BooleanField(
        verbose_name='是否启用',
        default=True
    )
    sync_mode = models.CharField(
        verbose_name='同步模式',
        max_length=20,
        choices=[
            ('manual', '手动同步'),
            ('auto', '自动同步')
        ],
        default='manual'
    )
    is_active = models.BooleanField(
        verbose_name='是否激活',
        default=False,
        help_text='只能有一个配置处于激活状态'
    )
    created_by = models.ForeignKey(
        User,
        verbose_name='创建人',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_global_configs'
    )
    created_time = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )
    updated_time = models.DateTimeField(
        verbose_name='更新时间',
        auto_now=True
    )

    class Meta:
        verbose_name = '全局同步配置'
        verbose_name_plural = verbose_name
        ordering = ['-updated_time']
        unique_together = ['project', 'name']  # 同一项目下配置名称唯一

    def __str__(self):
        return f"{self.name} ({'激活' if self.is_active else '未激活'})"

    def save(self, *args, **kwargs):
        # 如果当前配置被设置为激活，则将同一项目下的其他配置设置为非激活
        if self.is_active:
            GlobalSyncConfig.objects.filter(
                project=self.project
            ).exclude(id=self.id).update(is_active=False)
        super().save(*args, **kwargs)
