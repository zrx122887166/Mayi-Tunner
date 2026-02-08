from rest_framework import serializers
from django.core.exceptions import PermissionDenied
from .models import Interface, InterfaceResult
from modules.serializers import ModuleSerializer

class InterfaceSerializer(serializers.ModelSerializer):
    """接口序列化器"""
    module_info = ModuleSerializer(source='module', read_only=True)
    
    class Meta:
        model = Interface
        fields = '__all__'
        read_only_fields = ['created_by', 'created_time', 'updated_time']

    def validate_project(self, value):
        """验证用户是否有权限操作该项目"""
        user = self.context['request'].user
        if not user.is_superuser and not user.joined_projects.filter(id=value.id).exists():
            raise serializers.ValidationError("您没有权限在此项目中操作接口")
        return value

    def validate(self, attrs):
        """自定义验证方法"""
        # 获取当前操作类型
        instance = getattr(self, 'instance', None)
        
        # 检查接口名称是否已存在于同一项目中
        name = attrs.get('name')
        project = attrs.get('project')
        
        if name and project:
            # 构建查询条件
            query = Interface.objects.filter(name=name, project=project)
            
            # 如果是更新操作，排除当前实例
            if instance:
                query = query.exclude(pk=instance.pk)
                
            # 检查是否存在同名接口
            if query.exists():
                raise serializers.ValidationError({
                    "name": [f"项目中已存在名为 '{name}' 的接口，请使用其他名称"]
                })
                
        # 验证模块是否属于项目
        module = attrs.get('module')
        if module and module.project != project:
            raise serializers.ValidationError({"module": "模块必须属于同一个项目"})
            
        # 验证 setup_hooks 格式
        setup_hooks = attrs.get('setup_hooks', [])
        if not isinstance(setup_hooks, list):
            raise serializers.ValidationError({"setup_hooks": "前置钩子必须是列表"})
        
        # 验证 teardown_hooks 格式
        teardown_hooks = attrs.get('teardown_hooks', [])
        if not isinstance(teardown_hooks, list):
            raise serializers.ValidationError({"teardown_hooks": "后置钩子必须是列表"})
            
        # 验证 variables 格式
        variables = attrs.get('variables', {})
        if not isinstance(variables, dict):
            raise serializers.ValidationError({"variables": "变量必须是字典"})
            
        # 验证 validators 格式
        validators = attrs.get('validators', [])
        if not isinstance(validators, list):
            raise serializers.ValidationError({"validators": "断言规则必须是列表"})
        
        # HttpRunner支持的所有断言类型
        supported_comparators = [
            'eq', 'ne', 'gt', 'ge', 'gte', 'lt', 'le', 'lte',
            'contains', 'contained_by', 'type_match', 'regex_match',
            'startswith', 'endswith', 'str_eq',
            'length_equal', 'length_greater_than', 'length_less_than',
            'length_greater_or_equals', 'length_less_or_equals'
        ]
        
        for validator in validators:
            if not isinstance(validator, dict):
                raise serializers.ValidationError({"validators": "断言规则必须是字典"})
            
            # 支持两种格式的验证器
            # 格式1: {"check": "field", "expect": value}
            if "check" in validator and "expect" in validator:
                continue
            
            # 格式2: {"comparator": ["field", value]}
            valid_format = False
            for key in validator.keys():
                if key in supported_comparators:
                    if not isinstance(validator[key], list) or len(validator[key]) != 2:
                        raise serializers.ValidationError({
                            "validators": f"断言规则 {key} 必须为包含两个元素的列表 [字段, 期望值]"
                        })
                    valid_format = True
                    break
            
            if not valid_format and not ("check" in validator and "expect" in validator):
                raise serializers.ValidationError({
                    "validators": f"断言规则必须使用支持的比较器: {', '.join(supported_comparators)}，或使用 check/expect 格式"
                })
        
        # 验证 extract 格式
        extract = attrs.get('extract', {})
        if not isinstance(extract, dict):
            raise serializers.ValidationError({"extract": "提取变量必须是字典"})
        
        return attrs

    def create(self, validated_data):
        """创建接口时自动关联创建人"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        """自定义返回数据"""
        data = super().to_representation(instance)
        # 如果是列表请求，不返回详细的模块信息
        if self.context['request'].parser_context['kwargs'].get('pk') is None:
            data.pop('module_info', None)
        return data

class InterfaceResultSerializer(serializers.ModelSerializer):
    """接口执行结果序列化器"""
    class Meta:
        model = InterfaceResult
        fields = '__all__'
        read_only_fields = ['executed_by', 'executed_time']

    def validate_interface(self, value):
        """验证用户是否有权限操作该接口的结果"""
        user = self.context['request'].user
        if not user.is_superuser and not user.joined_projects.filter(id=value.project_id).exists():
            raise serializers.ValidationError("您没有权限操作此接口的测试结果")
        return value

    def create(self, validated_data):
        """创建执行结果时自动关联执行人"""
        validated_data['executed_by'] = self.context['request'].user
        return super().create(validated_data) 