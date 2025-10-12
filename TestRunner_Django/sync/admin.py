from django.contrib import admin
from .models import SyncConfig, SyncHistory, GlobalSyncConfig

@admin.register(SyncConfig)
class SyncConfigAdmin(admin.ModelAdmin):
    """同步配置管理"""
    list_display = ['name', 'interface', 'testcase', 'step', 'sync_enabled', 'sync_mode', 'created_by', 'created_time']
    list_filter = ['sync_enabled', 'sync_mode', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']
    raw_id_fields = ['interface', 'testcase', 'step', 'created_by']

@admin.register(SyncHistory)
class SyncHistoryAdmin(admin.ModelAdmin):
    """同步历史管理"""
    list_display = ['sync_config', 'sync_type', 'sync_status', 'operator', 'sync_time']
    list_filter = ['sync_type', 'sync_status', 'operator']
    search_fields = ['sync_config__name', 'error_message']
    readonly_fields = ['sync_time']
    raw_id_fields = ['sync_config', 'operator']

@admin.register(GlobalSyncConfig)
class GlobalSyncConfigAdmin(admin.ModelAdmin):
    """全局同步配置管理"""
    list_display = ['name', 'sync_enabled', 'sync_mode', 'is_active', 'created_by', 'created_time']
    list_filter = ['sync_enabled', 'sync_mode', 'is_active', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_time', 'updated_time']
    raw_id_fields = ['created_by']
