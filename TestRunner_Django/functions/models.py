from django.db import models
from django.contrib.auth import get_user_model
from projects.models import Project

User = get_user_model()

class CustomFunction(models.Model):
    """自定义函数模型"""
    name = models.CharField("函数名称", max_length=100)
    code = models.TextField("函数代码")
    description = models.TextField("函数描述", blank=True)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='custom_functions',
        verbose_name="所属项目"
    )
    is_active = models.BooleanField("是否启用", default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_functions',
        verbose_name="创建人"
    )
    created_time = models.DateTimeField("创建时间", auto_now_add=True)
    updated_time = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        verbose_name = "自定义函数"
        verbose_name_plural = verbose_name
        ordering = ['-created_time']
        unique_together = ['name', 'project']  # 同一项目下函数名唯一

    def __str__(self):
        return f"{self.project.name}-{self.name}"
