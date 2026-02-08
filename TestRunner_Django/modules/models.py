from django.db import models
from django.utils import timezone
from projects.models import Project

class Module(models.Model):
    """模块管理模型"""
    name = models.CharField(max_length=100, verbose_name='模块名称')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='modules', verbose_name='所属项目')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='父模块')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    create_time = models.DateTimeField(default=timezone.now, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'tb_modules'
        verbose_name = '模块'
        verbose_name_plural = verbose_name
        ordering = ['create_time']

    def __str__(self):
        return self.name

    def get_ancestors(self):
        """获取所有祖先模块"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """获取所有子孙模块"""
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
