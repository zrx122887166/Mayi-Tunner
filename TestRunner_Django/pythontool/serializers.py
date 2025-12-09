# serializers.py
from rest_framework import serializers
from .models import Tool, Tools

class ToolSerializer(serializers.ModelSerializer):
    """Python工具序列化器"""
    has_params = serializers.SerializerMethodField()
    creator_name = serializers.ReadOnlyField(source='creator.username')
    # 前端传 'scripts'，映射到模型的 'pythonScript'
    scripts = serializers.CharField(write_only=True, source='pythonScript', required=False, allow_blank=True)
    # 前端传 'selectedConnectPools'，映射到模型的 'connect_pools'
    selectedConnectPools = serializers.ListField(write_only=True, source='connect_pools', required=False, allow_empty=True)

    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'remark', 'pythonScript', 'scripts', # 同时包含读写字段和只读字段
            'params', 'selectedConnectPools', 'connect_pools',
            'creator', 'creator_name', 'create_time', 'has_params'
        ]
        read_only_fields = ['id', 'creator', 'creator_name', 'create_time', 'updated_time', 'pythonScript', 'connect_pools']

    def get_has_params(self, obj):
        """计算是否有参数"""
        return bool(obj.params) if obj.params else False

    def create(self, validated_data):
        """创建工具（可以在这里添加额外的创建逻辑）"""
        return Tool.objects.create(** validated_data)

    def update(self, instance, validated_data):
        """更新工具"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ToolsSerializer(serializers.ModelSerializer):
    """依赖工具序列化器"""

    class Meta:
        model = Tools
        fields = ['id', 'name', 'remark', 'pythonScript', 'create_time']
        read_only_fields = ['id', 'create_time']