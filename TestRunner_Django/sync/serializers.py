from rest_framework import serializers
from .models import SyncConfig, SyncHistory, GlobalSyncConfig
from interfaces.models import Interface
from testcases.models import TestCase, TestCaseStep

class SyncConfigSerializer(serializers.ModelSerializer):
    """同步配置序列化器"""
    interface_info = serializers.SerializerMethodField()
    testcase_info = serializers.SerializerMethodField()
    step_info = serializers.SerializerMethodField()
    created_by_info = serializers.SerializerMethodField()

    class Meta:
        model = SyncConfig
        fields = '__all__'
        read_only_fields = ['created_time', 'updated_time', 'created_by']

    def get_interface_info(self, obj):
        return {
            'id': obj.interface.id,
            'name': obj.interface.name,
            'method': obj.interface.method,
            'url': obj.interface.url
        }

    def get_testcase_info(self, obj):
        return {
            'id': obj.testcase.id,
            'name': obj.testcase.name
        }

    def get_step_info(self, obj):
        return {
            'id': obj.step.id,
            'name': obj.step.name,
            'order': obj.step.order
        }

    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username
            }
        return None

    def get_default_sync_fields(self):
        """获取默认同步字段"""
        # 获取激活的全局配置
        global_config = GlobalSyncConfig.objects.filter(is_active=True).first()
        if global_config:
            return global_config.sync_fields
        return []

    def validate(self, attrs):
        # 验证interface、testcase和step的关联关系
        interface = attrs.get('interface')
        testcase = attrs.get('testcase')
        step = attrs.get('step')

        if step.testcase != testcase:
            raise serializers.ValidationError('步骤不属于指定的测试用例')
        
        if step.origin_interface != interface:
            raise serializers.ValidationError('步骤未关联指定的接口')

        # 验证sync_fields是否是有效的接口字段
        valid_fields = [
            'method', 'url', 'headers', 'params', 'body',
            'setup_hooks', 'teardown_hooks', 'variables',
            'validators', 'extract'
        ]
        sync_fields = attrs.get('sync_fields', [])
        invalid_fields = [f for f in sync_fields if f not in valid_fields]
        if invalid_fields:
            raise serializers.ValidationError(f'无效的同步字段: {invalid_fields}')

        return attrs

    def create(self, validated_data):
        """创建时使用全局配置默认值"""
        # 获取激活的全局配置
        global_config = GlobalSyncConfig.objects.filter(is_active=True).first()
        
        if global_config:
            # 如果没有提供，使用全局配置的值
            if 'sync_fields' not in validated_data:
                validated_data['sync_fields'] = global_config.sync_fields
            if 'sync_enabled' not in validated_data:
                validated_data['sync_enabled'] = global_config.sync_enabled
            if 'sync_mode' not in validated_data:
                validated_data['sync_mode'] = global_config.sync_mode
        
        # 设置创建人
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class SyncHistorySerializer(serializers.ModelSerializer):
    """同步历史序列化器"""
    sync_config_info = serializers.SerializerMethodField()
    operator_info = serializers.SerializerMethodField()

    class Meta:
        model = SyncHistory
        fields = '__all__'
        read_only_fields = ['sync_time']

    def get_sync_config_info(self, obj):
        return {
            'id': obj.sync_config.id,
            'name': obj.sync_config.name,
            'interface': {
                'id': obj.sync_config.interface.id,
                'name': obj.sync_config.interface.name
            },
            'testcase': {
                'id': obj.sync_config.testcase.id,
                'name': obj.sync_config.testcase.name
            },
            'step': {
                'id': obj.sync_config.step.id,
                'name': obj.sync_config.step.name
            }
        }

    def get_operator_info(self, obj):
        if obj.operator:
            return {
                'id': obj.operator.id,
                'username': obj.operator.username
            }
        return None

    def validate(self, attrs):
        # 验证sync_fields是否是配置中允许的字段
        sync_config = attrs.get('sync_config')
        sync_fields = attrs.get('sync_fields', [])
        invalid_fields = [f for f in sync_fields if f not in sync_config.sync_fields]
        if invalid_fields:
            raise serializers.ValidationError(f'同步字段不在配置允许范围内: {invalid_fields}')

        return attrs

    def create(self, validated_data):
        # 设置操作人
        validated_data['operator'] = self.context['request'].user
        return super().create(validated_data)

class GlobalSyncConfigSerializer(serializers.ModelSerializer):
    """全局同步配置序列化器"""
    created_by_info = serializers.SerializerMethodField()
    is_current = serializers.SerializerMethodField()
    sync_mode_display = serializers.SerializerMethodField()
    sync_fields_count = serializers.SerializerMethodField()

    class Meta:
        model = GlobalSyncConfig
        fields = '__all__'
        read_only_fields = ['created_time', 'updated_time', 'created_by']

    def get_created_by_info(self, obj):
        if obj.created_by:
            return {
                'id': obj.created_by.id,
                'username': obj.created_by.username
            }
        return None

    def get_is_current(self, obj):
        """是否是当前生效的配置"""
        return obj.is_active

    def get_sync_mode_display(self, obj):
        """获取同步模式的显示文本"""
        return obj.get_sync_mode_display()

    def get_sync_fields_count(self, obj):
        """获取同步字段数量"""
        return len(obj.sync_fields)

    def validate_sync_fields(self, value):
        """验证同步字段是否有效"""
        valid_fields = [
            'method', 'url', 'headers', 'params', 'body',
            'setup_hooks', 'teardown_hooks', 'variables',
            'validators', 'extract'
        ]
        invalid_fields = [f for f in value if f not in valid_fields]
        if invalid_fields:
            raise serializers.ValidationError(f'无效的同步字段: {invalid_fields}')
        return value

    def create(self, validated_data):
        """创建时设置创建人"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data) 