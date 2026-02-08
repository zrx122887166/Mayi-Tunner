from django.db import models
from django.conf import settings


class Project(models.Model):
    """项目模型"""
    name = models.CharField('项目名称', max_length=100)
    description = models.TextField('项目描述', blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_projects',
        verbose_name='创建者'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='joined_projects',
        verbose_name='项目成员'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '项目'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def has_permission(self, user):
        """检查用户是否有权限操作该项目"""
        # 同时检查 is_superuser 和 is_staff，确保权限判断一致
        if user.is_superuser and user.is_staff:
            return True
            
        # 检查用户是否是项目成员
        return self.members.filter(id=user.id).exists()
