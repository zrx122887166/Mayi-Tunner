from rest_framework import serializers
from testcases.models import TestCase
from testcases.serializers import TestCaseSerializer, TestReportSerializer
from .models import TestTaskSuite, TestTaskCase, TestTaskExecution, TestTaskCaseResult


class TestTaskCaseSerializer(serializers.ModelSerializer):
    """测试任务用例关联序列化器"""
    testcase_id = serializers.PrimaryKeyRelatedField(
        queryset=TestCase.objects.all(),
        source='testcase',
        write_only=True
    )
    testcase = TestCaseSerializer(read_only=True)
    
    class Meta:
        model = TestTaskCase
        fields = ['id', 'testcase_id', 'testcase', 'order']
        read_only_fields = ['id']


class TestTaskCaseSimpleSerializer(serializers.ModelSerializer):
    """测试任务用例关联简化序列化器"""
    testcase_id = serializers.IntegerField(source='testcase.id', read_only=True)
    testcase_name = serializers.CharField(source='testcase.name', read_only=True)
    description = serializers.CharField(source='testcase.description', read_only=True)
    priority = serializers.CharField(source='testcase.priority', read_only=True)
    
    class Meta:
        model = TestTaskCase
        fields = ['id', 'testcase_id', 'testcase_name', 'description', 'priority', 'order']


class TestTaskSuiteSerializer(serializers.ModelSerializer):
    """测试任务集序列化器"""
    task_cases = TestTaskCaseSimpleSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    test_cases = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="测试用例ID列表"
    )
    
    class Meta:
        model = TestTaskSuite
        fields = [
            'id', 'name', 'description', 'priority', 'fail_fast',
            'project', 'project_name', 'created_by', 'created_by_name',
            'created_time', 'updated_time', 'task_cases', 'test_cases'
        ]
        read_only_fields = ['id', 'created_by', 'created_time', 'updated_time']
    
    def create(self, validated_data):
        # 获取并移除测试用例ID列表
        test_cases = validated_data.pop('test_cases', [])
        
        # 获取当前用户
        user = self.context['request'].user
        validated_data['created_by'] = user
        
        # 创建任务集
        instance = super().create(validated_data)
        
        # 添加测试用例
        if test_cases:
            from .services import TestTaskService
            TestTaskService.add_testcases(instance, test_cases)
        
        return instance
        
    def update(self, instance, validated_data):
        # 获取并移除测试用例ID列表
        test_cases = validated_data.pop('test_cases', None)
        
        # 更新基本信息
        instance = super().update(instance, validated_data)
        
        # 如果提供了测试用例列表，则更新关联的测试用例
        if test_cases is not None:
            from .services import TestTaskService
            # 1. 删除所有现有的关联
            instance.task_cases.all().delete()
            # 2. 重新添加测试用例
            TestTaskService.add_testcases(instance, test_cases)
        
        return instance


class TestTaskCaseCreateSerializer(serializers.Serializer):
    """测试任务用例添加序列化器"""
    testcase_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="测试用例ID列表"
    )
    
    def validate_testcase_ids(self, value):
        # 验证测试用例是否存在
        testcase_count = TestCase.objects.filter(id__in=value).count()
        if testcase_count != len(value):
            raise serializers.ValidationError("部分测试用例不存在")
        return value


class TestTaskCaseResultSerializer(serializers.ModelSerializer):
    """测试任务用例执行结果序列化器"""
    testcase_name = serializers.CharField(source='testcase.name', read_only=True)
    report = TestReportSerializer(read_only=True)
    
    class Meta:
        model = TestTaskCaseResult
        fields = [
            'id', 'testcase', 'testcase_name', 'status',
            'start_time', 'end_time', 'duration',
            'error_message', 'report'
        ]
        read_only_fields = ['id', 'testcase', 'testcase_name', 'status',
                           'start_time', 'end_time', 'duration',
                           'error_message', 'report']


class TestTaskExecutionSerializer(serializers.ModelSerializer):
    """测试任务执行记录序列化器"""
    task_suite_name = serializers.CharField(source='task_suite.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    case_results = TestTaskCaseResultSerializer(many=True, read_only=True)
    duration = serializers.FloatField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = TestTaskExecution
        fields = [
            'id', 'task_suite', 'task_suite_name', 'status',
            'environment', 'environment_name',
            'start_time', 'end_time', 'duration',
            'total_count', 'success_count', 'fail_count', 'error_count',
            'success_rate', 'executed_by', 'executed_by_name',
            'created_time', 'case_results'
        ]
        read_only_fields = ['id', 'status', 'start_time', 'end_time',
                           'total_count', 'success_count', 'fail_count', 'error_count',
                           'executed_by', 'created_time']
    
    def create(self, validated_data):
        # 获取当前用户
        user = self.context['request'].user
        validated_data['executed_by'] = user
        
        # 获取任务集
        task_suite = validated_data['task_suite']
        
        # 设置总用例数
        validated_data['total_count'] = task_suite.task_cases.count()
        
        return super().create(validated_data)


class TestTaskExecutionListSerializer(serializers.ModelSerializer):
    """测试任务执行记录列表序列化器（简化版）"""
    environment_name = serializers.CharField(source='environment.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.username', read_only=True)
    duration = serializers.FloatField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    
    class Meta:
        model = TestTaskExecution
        fields = [
            'id', 'status', 'environment', 'environment_name',
            'start_time', 'end_time', 'duration',
            'total_count', 'success_rate',
            'executed_by', 'executed_by_name', 'created_time'
        ]
        read_only_fields = ['id', 'status', 'start_time', 'end_time',
                           'total_count', 'executed_by', 'created_time']


class TestTaskExecutionCreateSerializer(serializers.Serializer):
    """测试任务执行创建序列化器"""
    task_suite_id = serializers.IntegerField(help_text="任务集ID")
    environment_id = serializers.IntegerField(help_text="环境ID", required=False, allow_null=True)
    
    def validate_task_suite_id(self, value):
        # 验证任务集是否存在
        try:
            task_suite = TestTaskSuite.objects.get(id=value)
            # 验证任务集是否有测试用例
            if task_suite.task_cases.count() == 0:
                raise serializers.ValidationError("任务集中没有测试用例")
            return value
        except TestTaskSuite.DoesNotExist:
            raise serializers.ValidationError("任务集不存在") 