from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import DatabaseConfig

class DatabaseConfigResource(resources.ModelResource):
    class Meta:
        model = DatabaseConfig
        skip_unchanged = True
        report_skipped = True
        exclude = ('id', 'password')  # 排除敏感字段

@admin.register(DatabaseConfig)
class DatabaseConfigAdmin(ImportExportModelAdmin):
    """数据库配置管理"""
    resource_class = DatabaseConfigResource
    list_display = ['name', 'project', 'db_type', 'host', 'port', 'database', 'username', 'is_active', 'created_at']
    list_filter = ['project', 'db_type', 'is_active', 'created_at']
    search_fields = ['name', 'host', 'database', 'username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'