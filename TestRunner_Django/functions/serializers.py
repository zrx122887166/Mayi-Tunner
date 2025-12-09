from rest_framework import serializers
from .models import CustomFunction

class CustomFunctionSerializer(serializers.ModelSerializer):
    """自定义函数序列化器"""
    class Meta:
        model = CustomFunction
        fields = '__all__'
        read_only_fields = ['created_by', 'created_time', 'updated_time']
        extra_kwargs = {
            'project': {'required': False},  # 更新时project字段不是必填的
            'name': {'max_length': 100}  # 只限制名称长度
        }

    def validate_code(self, value):
        """验证函数代码"""
        # 检查代码长度
        if len(value) > 10000:
            raise serializers.ValidationError("函数代码长度不能超过10000个字符")
            
        # 检查是否包含函数定义
        # if not value.strip().startswith('def '):
        #     raise serializers.ValidationError("代码必须以'def'开头定义一个函数")
            
        # 检查危险函数和模块
        forbidden_keywords = [
            'eval(', 'exec(', 'execfile(',
            'import os', 'import subprocess', 'import sys',
            '__import__', 'open(', 'file(',
            'remove(', 'rmdir(', 'unlink(',
            'system(', 'popen(', 'spawn'
        ]
        for keyword in forbidden_keywords:
            if keyword in value:
                raise serializers.ValidationError(f"代码中不允许使用危险函数或模块：{keyword}")

        return value

    def validate(self, attrs):
        """验证整个对象"""
        # 验证用户是否有权限操作该项目
        project = attrs.get('project')
        if project:  # 只在提供project时验证权限
            user = self.context['request'].user
            if not user.is_superuser and not user.joined_projects.filter(id=project.id).exists():
                raise serializers.ValidationError({"project": "您没有权限在此项目中创建函数"})
                
        return attrs 