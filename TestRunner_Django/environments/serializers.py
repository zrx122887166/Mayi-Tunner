from rest_framework import serializers
from .models import Environment, EnvironmentVariable, Project, GlobalRequestHeader

class EnvironmentVariableSerializer(serializers.ModelSerializer):
    """环境变量序列化器"""
    class Meta:
        model = EnvironmentVariable
        fields = [
            'id', 'name', 'value', 'type', 'description',
            'is_sensitive', 'created_time', 'updated_time', 'environment'
        ]
        read_only_fields = ['created_time', 'updated_time']

    def to_representation(self, instance):
        """重写返回方法，如果是敏感数据则隐藏value值"""
        ret = super().to_representation(instance)
        if instance.is_sensitive:
            ret['value'] = '******'
        return ret

class ProjectSerializer(serializers.ModelSerializer):
    """项目序列化器"""
    class Meta:
        model = Project
        fields = ['id', 'name']
        ref_name = 'EnvironmentProjectSerializer'

class EnvironmentSerializer(serializers.ModelSerializer):
    """环境配置序列化器"""
    variables = EnvironmentVariableSerializer(many=True, read_only=True)
    project_info = ProjectSerializer(source='project', read_only=True)
    parent_info = serializers.SerializerMethodField()
    database_config_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Environment
        fields = [
            'id', 'name', 'base_url', 'verify_ssl',
            'description', 'project', 'project_info',
            'parent', 'parent_info', 'is_active',
            'created_by', 'created_time', 'updated_time',
            'variables', 'database_config', 'database_config_info'
        ]
        read_only_fields = ['created_by', 'created_time', 'updated_time']
        extra_kwargs = {
            'project': {'write_only': True, 'required': False},
            'parent': {'write_only': True, 'required': False},
            'database_config': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        """创建时自动设置创建人"""
        if 'project' not in validated_data:
            raise serializers.ValidationError({'project': ['创建环境时project字段是必需的']})
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """更新时检查数据库配置是否属于同一个项目"""
        database_config = validated_data.get('database_config')
        if database_config and database_config.project_id != instance.project_id:
            raise serializers.ValidationError({'database_config': ['数据库配置必须属于同一个项目']})
        return super().update(instance, validated_data)

    def get_parent_info(self, obj):
        """获取父环境信息"""
        if obj.parent:
            return {
                'id': obj.parent.id,
                'name': obj.parent.name,
                'base_url': obj.parent.base_url,
                'description': obj.parent.description
            }
        return None

    def get_database_config_info(self, obj):
        """获取数据库配置信息"""
        if obj.database_config:
            return {
                'id': obj.database_config.id,
                'name': obj.database_config.name,
                'db_type': obj.database_config.db_type,
                'host': obj.database_config.host
            }
        return None

class GlobalRequestHeaderSerializer(serializers.ModelSerializer):
    """全局请求头参数序列化器"""
    project_name = serializers.StringRelatedField(source='project.name', read_only=True)
    created_by_name = serializers.StringRelatedField(source='created_by.username', read_only=True)
    
    class Meta:
        model = GlobalRequestHeader
        fields = [
            'id', 'name', 'value',
            'description', 'is_enabled', 'project', 'project_name',
            'created_by', 'created_by_name', 'created_time', 'updated_time'
        ]
        read_only_fields = ['created_by', 'created_time', 'updated_time']
        
    def create(self, validated_data):
        """创建时自动设置创建人"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data) 