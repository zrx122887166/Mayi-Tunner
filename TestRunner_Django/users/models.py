from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    自定义用户模型
    """
    phone = models.CharField(
        _('手机号'), 
        max_length=11, 
        null=True, 
        blank=True,
        help_text=_('手机号（可选）'),
        db_index=True
    )
    avatar = models.URLField(_('头像'), max_length=200, null=True, blank=True)
    is_deleted = models.BooleanField(_('是否删除'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = verbose_name
        ordering = ['-id']
        db_table = 'auth_user'

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # 确保空字符串被保存为 NULL
        if not self.phone:
            self.phone = None
        super().save(*args, **kwargs) 