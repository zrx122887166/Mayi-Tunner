from rest_framework import serializers
from .models import Tool, Tools

class ToolSerializer(serializers.ModelSerializer):
    """Python工具序列化器（适配最新模型）"""
    has_params = serializers.SerializerMethodField()
    creator_name = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Tool
        fields = [
            'id', 'name', 'remark', 'pythonScript', 'params',
            'connect_pools', 'creator', 'creator_name',
            'create_time', 'updated_time', 'has_params'  # 注意：是updated_time
        ]
        read_only_fields = ['id', 'creator', 'creator_name', 'create_time', 'updated_time']

    def get_has_params(self, obj):
        """判断是否有参数（前端展示用）"""
        return bool(obj.params) if obj.params else False

    def create(self, validated_data):
        """自动关联创建人"""
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)

# class ToolsSerializer(serializers.ModelSerializer):
#     """依赖工具序列化器（适配最新模型）"""
    # 若添加了creator字段，补充以下配置
    # creator_name = serializers.ReadOnlyField(source='creator.username', required=False)

    # class Meta:
    #     model = Tools
    #     fields = ['id', 'name', 'remark', 'pythonScript', 'creator', 'creator_name', 'create_time']  # 按需加creator
    #     read_only_fields = ['id', 'creator', 'creator_name', 'create_time']  # 按需加creator


class ToolsSerializer(serializers.ModelSerializer):
    """依赖工具序列化器"""

    class Meta:
        model = Tools
        fields = ['id', 'name', 'remark', 'pythonScript', 'create_time']
        read_only_fields = ['id', 'create_time']