from rest_framework import serializers
from .models import Module

class ModuleSerializer(serializers.ModelSerializer):
    """模块序列化器"""
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = '__all__'
        read_only_fields = ['create_time', 'update_time']

    def get_children(self, obj):
        """获取子模块"""
        children = obj.children.all()
        if children:
            return ModuleSerializer(children, many=True).data
        return []

class ModuleCreateSerializer(serializers.ModelSerializer):
    """模块创建序列化器"""
    class Meta:
        model = Module
        fields = ['name', 'project', 'parent', 'description']

    def validate(self, attrs):
        """验证模块创建数据"""
        project = attrs.get('project')
        parent = attrs.get('parent')
        
        if parent and parent.project != project:
            raise serializers.ValidationError({'parent': '父模块必须属于同一个项目'})
        
        return attrs

class ModuleUpdateSerializer(serializers.ModelSerializer):
    """模块更新序列化器"""
    class Meta:
        model = Module
        fields = ['name', 'description']
        read_only_fields = ['project', 'parent'] 