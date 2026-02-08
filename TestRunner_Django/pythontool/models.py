from django.db import models
from django.conf import settings
import json

class Tool(models.Model):
    """Python工具模型"""
    name = models.CharField(max_length=100, verbose_name="工具名称")
    group_name = models.CharField(max_length=100, verbose_name="工具分组名称", default="未分组")
    remark = models.TextField(blank=True, null=True, verbose_name="工具备注")
    pythonScript = models.TextField(blank=True, null=True, verbose_name="Python脚本")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tools',
        verbose_name="创建人"
    )
    params = models.JSONField(default=dict, blank=True, null=True, verbose_name="参数配置")  # 存储参数列表的JSON字段
    connect_pools = models.JSONField(default=list, blank=True, null=True, verbose_name="连接池配置")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        verbose_name = "Python工具"
        verbose_name_plural = "Python工具"
        ordering = ["-create_time"]

        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['group_name']),
            models.Index(fields=['create_time']),
        ]

    def __str__(self):
        return self.name

class Tools(models.Model):
    """脚本依赖模型"""
    name = models.CharField(max_length=255, verbose_name='工具名称')
    remark = models.TextField(verbose_name='工具备注', blank=True, null=True)
    pythonScript = models.TextField(verbose_name='Python脚本', blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = "脚本依赖工具"
        verbose_name_plural = "脚本依赖工具"
        ordering = ["-create_time"]

    def __str__(self):
        return self.name