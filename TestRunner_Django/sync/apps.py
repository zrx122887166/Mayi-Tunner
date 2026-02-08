from django.apps import AppConfig


class SyncConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sync"
    verbose_name = "同步管理"

    def ready(self):
        """应用就绪时的初始化操作"""
        try:
            import sync.signals  # 导入信号处理器
        except ImportError:
            pass
