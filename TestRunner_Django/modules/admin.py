from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Module

class ModuleResource(resources.ModelResource):
    class Meta:
        model = Module
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)

@admin.register(Module)
class ModuleAdmin(ImportExportModelAdmin):
    """模块管理"""
    resource_class = ModuleResource
    list_display = ['name', 'project', 'parent', 'description', 'create_time', 'update_time']
    list_filter = ['project', 'parent', 'create_time']
    search_fields = ['name', 'description']
    readonly_fields = ['create_time', 'update_time']
    date_hierarchy = 'create_time'