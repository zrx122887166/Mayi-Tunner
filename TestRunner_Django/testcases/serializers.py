from rest_framework import serializers
from .models import (
    TestCase, TestCaseStep, TestReport, TestReportDetail,
    TestCaseTag, TestCaseGroup
)
from django.db import transaction
from django.db import models
from interfaces.models import Interface


class TestCaseTagSerializer(serializers.ModelSerializer):
    """测试用例标签序列化器"""
    class Meta:
        model = TestCaseTag
        fields = ['id', 'name', 'color', 'project', 'created_by', 'created_time']
        read_only_fields = ['created_by', 'created_time']
        extra_kwargs = {
            'project': {'required': True},
            'name': {'required': True},
            'color': {'required': True}
        }

    def create(self, validated_data):
        """创建标签时设置创建人"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TestCaseGroupSerializer(serializers.ModelSerializer):
    """测试用例分组序列化器"""
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = TestCaseGroup
        fields = [
            'id', 'name', 'parent', 'project',
            'created_by', 'created_time', 'full_path',
            'children'
        ]
        read_only_fields = ['created_by', 'created_time']
        extra_kwargs = {
            'project': {'required': True},
            'name': {'required': True}
        }

    def get_children(self, obj):
        """获取子分组"""
        children = obj.children.all()
        if children:
            return TestCaseGroupSerializer(children, many=True).data
        return []

    def create(self, validated_data):
        """创建分组时设置创建人"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TestCaseStepSerializer(serializers.ModelSerializer):
    """测试步骤序列化器"""
    interface_id = serializers.IntegerField(write_only=True, help_text="关联的接口ID")
    interface_info = serializers.SerializerMethodField(read_only=True)
    interface_data = serializers.JSONField(required=False)
    
    class Meta:
        model = TestCaseStep
        fields = [
            'id', 'name', 'order', 'interface_id',
            'interface_info', 'interface_data', 'sync_fields', 
            'last_sync_time'
        ]
        read_only_fields = ['last_sync_time']
        
    def get_interface_info(self, obj):
        """获取关联接口的详细信息"""
        if obj.origin_interface:
            return {
                'id': obj.origin_interface.id,
                'name': obj.origin_interface.name,
                'method': obj.origin_interface.method,
                'url': obj.origin_interface.url,
                'module': {
                    'id': obj.origin_interface.module.id,
                    'name': obj.origin_interface.module.name
                } if obj.origin_interface.module else None,
                'project': {
                    'id': obj.origin_interface.project.id,
                    'name': obj.origin_interface.project.name
                }
            }
        return None

    def _build_interface_data(self, interface):
        """构建接口数据，确保包含所有必要字段"""
        return {
            'method': interface.method,
            'url': interface.url,
            'headers': interface.headers or [],
            'params': interface.params or [],
            'body': interface.body or {'type': 'raw', 'content': ''},
            'extract': {},  # 变量提取
            'variables': {},  # 变量配置
            'validators': [],  # 断言规则
            'setup_hooks': [],  # 前置钩子
            'teardown_hooks': []  # 后置钩子
        }

    def _create_sync_config(self, step, interface):
        """创建同步配置"""
        from sync.models import SyncConfig, GlobalSyncConfig
        
        # 检查是否已存在同步配置
        existing_config = SyncConfig.objects.filter(
            interface=interface,
            step=step
        ).first()
        
        if not existing_config:
            # 获取激活的全局配置
            global_config = GlobalSyncConfig.objects.filter(
                project=interface.project,
                is_active=True,
                sync_enabled=True
            ).first()
            
            if global_config:
                # 获取同步字段
                sync_fields = global_config.sync_fields
                
                # 准备触发条件
                # 如果是自动同步模式，默认监视所有同步字段
                # 如果是手动同步模式，不监视任何字段
                sync_trigger = {
                    "fields_to_watch": sync_fields if global_config.sync_mode == 'auto' else []
                }
                
                # 使用全局配置创建同步配置
                SyncConfig.objects.create(
                    name=f'自动创建 - {interface.name}',
                    description=f'从全局配置自动创建的同步配置',
                    interface=interface,
                    testcase=step.testcase,
                    step=step,
                    sync_fields=sync_fields,
                    sync_enabled=global_config.sync_enabled,
                    sync_mode=global_config.sync_mode,
                    sync_trigger=sync_trigger,
                    created_by=self.context['request'].user if 'request' in self.context else None
                )
                return True
        return False

    def create(self, validated_data):
        """创建测试步骤时，确保interface_data包含所有必要字段"""
        interface_id = validated_data.pop('interface_id')
        interface = Interface.objects.get(id=interface_id)
        
        # 构建完整的interface_data
        validated_data['interface_data'] = self._build_interface_data(interface)
        validated_data['origin_interface'] = interface
        
        # 创建步骤
        step = super().create(validated_data)
        
        # 创建同步配置
        self._create_sync_config(step, interface)
        
        return step

    def update(self, instance, validated_data):
        """更新测试步骤时，确保保留现有的扩展字段"""
        old_interface = instance.origin_interface
        new_interface = None
        
        if 'interface_id' in validated_data:
            interface_id = validated_data.pop('interface_id')
            new_interface = Interface.objects.get(id=interface_id)
            
            # 获取现有的interface_data
            current_data = instance.interface_data or {}
            
            # 构建新的interface_data，保留现有的扩展字段
            new_data = self._build_interface_data(new_interface)
            new_data.update({
                'extract': current_data.get('extract', {}),
                'variables': current_data.get('variables', {}),
                'validators': current_data.get('validators', []),
                'setup_hooks': current_data.get('setup_hooks', []),
                'teardown_hooks': current_data.get('teardown_hooks', [])
            })
            
            validated_data['interface_data'] = new_data
            validated_data['origin_interface'] = new_interface
        
        # 更新步骤
        step = super().update(instance, validated_data)
        
        # 如果接口发生变化，处理同步配置
        if new_interface and new_interface != old_interface:
            # 删除旧的同步配置
            from sync.models import SyncConfig
            SyncConfig.objects.filter(step=step).delete()
            
            # 创建新的同步配置
            self._create_sync_config(step, new_interface)
        
        return step


class TestCaseSerializer(serializers.ModelSerializer):
    """测试用例序列化器"""
    steps = TestCaseStepSerializer(many=True, read_only=True)
    steps_info = serializers.ListField(
        child=TestCaseStepSerializer(),
        write_only=True,
        required=False,
        help_text="测试步骤信息列表"
    )
    tags_info = TestCaseTagSerializer(source='tags', many=True, read_only=True)
    group_info = TestCaseGroupSerializer(source='group', read_only=True)
    related_interfaces = serializers.SerializerMethodField(help_text="关联的接口信息")
    
    def get_related_interfaces(self, obj):
        """获取用例关联的所有接口信息"""
        interfaces = {}
        for step in obj.steps.all().select_related('origin_interface__module', 'origin_interface__project'):
            if step.origin_interface:
                interface = step.origin_interface
                module_name = interface.module.name if interface.module else "未分类"
                
                if module_name not in interfaces:
                    interfaces[module_name] = []
                    
                interfaces[module_name].append({
                    'id': interface.id,
                    'name': interface.name,
                    'method': interface.method,
                    'url': interface.url,
                    'step_name': step.name,
                    'step_order': step.order
                })
        
        # 转换为列表格式，按模块分组
        return [
            {
                'module': module_name,
                'interfaces': sorted(interface_list, key=lambda x: x['step_order'])
            }
            for module_name, interface_list in interfaces.items()
        ]
    
    class Meta:
        model = TestCase
        fields = [
            'id', 'name', 'description', 'priority',
            'config', 'project', 'group',
            'tags', 'tags_info', 'group_info',
            'created_by', 'created_time', 'updated_time',
            'steps', 'steps_info', 'related_interfaces'
        ]
        read_only_fields = ['created_by', 'created_time', 'updated_time']
        extra_kwargs = {
            'project': {'required': True},
            'name': {'required': True},
            'priority': {'required': True}
        }
    
    def _create_step(self, instance, step_data, order):
        """创建单个测试步骤"""
        interface_id = step_data.pop('interface_id')
        interface = Interface.objects.get(id=interface_id)
        
        # 获取用户传入的interface_data
        user_interface_data = step_data.pop('interface_data', None)
        
        if user_interface_data:
            # 如果用户传入了interface_data，使用用户的数据，但确保所有必要字段都存在
            interface_data = {
                'method': user_interface_data.get('method', interface.method),
                'url': user_interface_data.get('url', interface.url),
                'headers': user_interface_data.get('headers', []),
                'params': user_interface_data.get('params', []),
                'body': user_interface_data.get('body', {'type': 'raw', 'content': ''}),
                'extract': user_interface_data.get('extract', {}),
                'variables': user_interface_data.get('variables', {}),
                'validators': user_interface_data.get('validators', []),
                'setup_hooks': user_interface_data.get('setup_hooks', []),
                'teardown_hooks': user_interface_data.get('teardown_hooks', [])
            }
        else:
            # 如果用户没有传入，则构建默认的interface_data
            interface_data = self._build_interface_data(interface)
        
        # 移除order字段，因为它会作为参数传入
        step_data.pop('order', None)
        
        # 创建测试步骤
        step = TestCaseStep.objects.create(
            testcase=instance,
            order=order,
            origin_interface=interface,
            interface_data=interface_data,
            **step_data
        )
        
        # 创建同步配置
        self._create_sync_config(step, interface)
        
        return step

    def _build_interface_data(self, interface):
        """构建接口数据"""
        return {
            'method': interface.method,
            'url': interface.url,
            'headers': interface.headers or [],
            'params': interface.params or [],
            'body': interface.body or {'type': 'raw', 'content': ''},
            'extract': {},  # 变量提取
            'variables': {},  # 变量配置
            'validators': [],  # 断言规则
            'setup_hooks': [],  # 前置钩子
            'teardown_hooks': []  # 后置钩子
        }
        
    def _create_sync_config(self, step, interface):
        """创建同步配置"""
        from sync.models import SyncConfig, GlobalSyncConfig
        
        # 检查是否已存在同步配置
        existing_config = SyncConfig.objects.filter(
            interface=interface,
            step=step
        ).first()
        
        if not existing_config:
            # 获取激活的全局配置
            global_config = GlobalSyncConfig.objects.filter(
                project=interface.project,
                is_active=True,
                sync_enabled=True
            ).first()
            
            if global_config:
                # 获取同步字段
                sync_fields = global_config.sync_fields
                
                # 准备触发条件
                # 如果是自动同步模式，默认监视所有同步字段
                # 如果是手动同步模式，不监视任何字段
                sync_trigger = {
                    "fields_to_watch": sync_fields if global_config.sync_mode == 'auto' else []
                }
                
                # 使用全局配置创建同步配置
                SyncConfig.objects.create(
                    name=f'自动创建 - {interface.name}',
                    description=f'从全局配置自动创建的同步配置',
                    interface=interface,
                    testcase=step.testcase,
                    step=step,
                    sync_fields=sync_fields,
                    sync_enabled=global_config.sync_enabled,
                    sync_mode=global_config.sync_mode,
                    sync_trigger=sync_trigger,
                    created_by=self.context['request'].user if 'request' in self.context else None
                )

    def create(self, validated_data):
        """创建用例并处理步骤信息"""
        # 移除steps_info字段，避免传入model create方法
        steps_info = validated_data.pop('steps_info', [])
        
        # 设置创建人
        validated_data['created_by'] = self.context['request'].user
        
        # 创建测试用例
        instance = super().create(validated_data)
        
        # 创建测试步骤
        for step_data in steps_info:
            # 使用步骤中定义的order，如果没有则使用当前最大order + 1
            if 'order' not in step_data:
                max_order = instance.steps.aggregate(
                    max_order=models.Max('order')
                )['max_order'] or 0
                step_data['order'] = max_order + 1
            
            # 创建步骤
            self._create_step(
                instance=instance,
                step_data=step_data.copy(),  # 使用copy避免修改原始数据
                order=step_data['order']
            )
        
        # 刷新实例以获取最新数据
        instance.refresh_from_db()
        return instance

    def update(self, instance, validated_data):
        """更新用例并处理步骤信息"""
        steps_info = validated_data.pop('steps_info', None)
        update_mode = validated_data.pop('update_mode', 'auto')  # 'auto', 'update', 'create'
        print(f"更新操作 - 接收到的steps_info: {steps_info}, 更新模式: {update_mode}")  # 调试日志
        
        try:
            # 更新测试用例基本信息
            instance = super().update(instance, validated_data)
            
            # 如果提供了steps_info，则添加步骤
            if steps_info is not None:
                with transaction.atomic():
                    # 获取已存在的步骤，包括顺序和详细信息
                    existing_steps = {step.order: step for step in instance.steps.all()}
                    existing_orders = set(existing_steps.keys())
                    print(f"已存在的步骤顺序: {existing_orders}")  # 调试信息
                    
                    # 创建新的测试步骤
                    for step_data in steps_info:
                        # 使用步骤中定义的order，如果没有则使用当前最大order + 1
                        if 'order' not in step_data:
                            max_order = max(existing_orders) if existing_orders else 0
                            step_data['order'] = max_order + 1
                        
                        current_order = step_data['order']
                        
                        # 检查是否存在相同顺序的步骤
                        if current_order in existing_orders:
                            # 获取已存在的相同顺序步骤
                            existing_step = existing_steps[current_order]
                            
                            # 1. 检查两个步骤的关键信息是否相同
                            is_same_interface = ('interface_id' in step_data and 
                                                existing_step.origin_interface and 
                                                existing_step.origin_interface.id == step_data['interface_id'])
                            is_same_name = step_data.get('name') == existing_step.name
                            
                            # 2. 如果接口ID和名称相同，可以认为是相同步骤，直接跳过创建
                            if is_same_interface and is_same_name:
                                print(f"步骤 {current_order} 已存在且内容相同，跳过创建")
                                continue
                            
                            # 3. 如果更新模式是'update'，则更新现有步骤而不是创建新步骤
                            if update_mode == 'update':
                                print(f"更新现有步骤: {existing_step.id}, 顺序: {current_order}")
                                
                                # 构建需要更新的数据
                                update_data = step_data.copy()
                                interface_id = update_data.pop('interface_id', None)
                                
                                # 如果提供了新的接口ID，获取接口实例
                                if interface_id:
                                    interface = Interface.objects.get(id=interface_id)
                                    
                                    # 获取现有的interface_data
                                    current_data = existing_step.interface_data or {}
                                    
                                    # 构建新的interface_data，合并用户提供的数据和现有数据
                                    user_interface_data = update_data.pop('interface_data', {})
                                    
                                    # 如果用户提供了interface_data，将其与基础数据合并
                                    if user_interface_data:
                                        interface_data = self._build_interface_data(interface)
                                        interface_data.update({
                                            'extract': user_interface_data.get('extract', current_data.get('extract', {})),
                                            'variables': user_interface_data.get('variables', current_data.get('variables', {})),
                                            'validators': user_interface_data.get('validators', current_data.get('validators', [])),
                                            'setup_hooks': user_interface_data.get('setup_hooks', current_data.get('setup_hooks', [])),
                                            'teardown_hooks': user_interface_data.get('teardown_hooks', current_data.get('teardown_hooks', []))
                                        })
                                    else:
                                        # 保留现有的扩展字段
                                        interface_data = self._build_interface_data(interface)
                                        interface_data.update({
                                            'extract': current_data.get('extract', {}),
                                            'variables': current_data.get('variables', {}),
                                            'validators': current_data.get('validators', []),
                                            'setup_hooks': current_data.get('setup_hooks', []),
                                            'teardown_hooks': current_data.get('teardown_hooks', [])
                                        })
                                    
                                    # 更新步骤数据
                                    existing_step.interface_data = interface_data
                                    existing_step.origin_interface = interface
                                    
                                    # 如果接口发生变化，处理同步配置
                                    if interface != existing_step.origin_interface:
                                        from sync.models import SyncConfig
                                        SyncConfig.objects.filter(step=existing_step).delete()
                                        self._create_sync_config(existing_step, interface)
                                
                                # 更新其他字段
                                if 'name' in update_data:
                                    existing_step.name = update_data['name']
                                if 'sync_fields' in update_data:
                                    existing_step.sync_fields = update_data['sync_fields']
                                    
                                # 保存更新
                                existing_step.save()
                                continue
                            
                            # 如果不是更新模式，且内容不相同，则需要调整顺序
                            print(f"检测到顺序冲突: {current_order}, 自动调整步骤顺序")  # 调试信息
                            
                            # 将所有大于等于当前顺序的步骤向后移动一位
                            steps_to_update = instance.steps.filter(order__gte=current_order).order_by('-order')
                            for s in steps_to_update:
                                s.order += 1
                                s.save()
                                print(f"步骤 {s.id} 顺序从 {s.order-1} 调整为 {s.order}")  # 调试信息
                            
                            # 更新已存在的步骤字典和顺序集合
                            existing_steps = {
                                (s.order + 1 if s.order >= current_order else s.order): s 
                                for s in existing_steps.values()
                            }
                            existing_orders = set(existing_steps.keys())
                            existing_orders.add(current_order)
                        else:
                            # 如果不存在冲突，添加到已存在的顺序集合中
                            existing_orders.add(current_order)
                        
                        # 创建步骤
                        step = self._create_step(
                            instance=instance,
                            step_data=step_data.copy(),  # 使用copy避免修改原始数据
                            order=current_order
                        )
                        
                        # 更新步骤字典
                        existing_steps[current_order] = step
                        
                        print(f"创建的步骤ID: {step.id}, 顺序: {step.order}, interface_data: {step.interface_data}")  # 调试日志
                
                # 刷新实例以获取最新数据
                instance.refresh_from_db()
                
                # 返回统一格式的成功响应数据
                response_data = {
                    "status": "success",
                    "code": 200,
                    "message": "测试步骤添加成功",
                    "data": self.to_representation(instance)
                }
                print("返回的响应数据:", response_data)  # 调试日志
                return response_data
                
        except Interface.DoesNotExist:
            return {
                "status": "error",
                "code": 404,
                "message": "接口不存在",
                "data": {},
                "errors": {"interface_id": ["指定的接口不存在"]}
            }
        except Exception as e:
            print(f"发生错误: {str(e)}")  # 调试日志
            return {
                "status": "error",
                "code": 500,
                "message": f"添加测试步骤失败: {str(e)}",
                "data": {},
                "errors": {"detail": ["服务器内部错误"]}
            }
        
        return instance


class TestReportDetailSerializer(serializers.ModelSerializer):
    """测试报告详情序列化器"""
    step_name = serializers.CharField(source='step.name', read_only=True)
    
    class Meta:
        model = TestReportDetail
        fields = [
            'id', 'step_name', 'success', 'elapsed',
            'request', 'response', 'validators',
            'extracted_variables', 'attachment'
        ]


class TestReportListSerializer(serializers.ModelSerializer):
    """测试报告列表序列化器 - 专用于列表视图，减少数据量"""
    testcase_name = serializers.CharField(source='testcase.name', read_only=True)
    success_rate = serializers.SerializerMethodField()
    environment_name = serializers.CharField(source='environment.name', read_only=True, default='')
    executed_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TestReport
        fields = [
            'id', 'name', 'testcase_name', 'status', 
            'success_count', 'fail_count', 'error_count',
            'success_rate', 'duration', 'start_time',
            'environment_name', 'executed_by_name'
        ]
        
    def get_success_rate(self, obj):
        """计算成功率"""
        total = obj.success_count + obj.fail_count + obj.error_count
        if total == 0:
            return "0"
        rate = obj.success_count / total
        return "1" if rate == 1 else f"{rate:.2f}"
    
    def get_executed_by_name(self, obj):
        """获取执行人名称"""
        if obj.executed_by:
            return obj.executed_by.username
        return ""


class TestReportSerializer(serializers.ModelSerializer):
    """测试报告序列化器 - 用于详情视图"""
    testcase_name = serializers.CharField(source='testcase.name', read_only=True)
    details = TestReportDetailSerializer(many=True, read_only=True)
    success_rate = serializers.SerializerMethodField()
    environment_info = serializers.SerializerMethodField()
    executed_by_info = serializers.SerializerMethodField()
    
    class Meta:
        model = TestReport
        fields = [
            'id', 'name', 'status', 'success_count',
            'fail_count', 'error_count', 'duration',
            'start_time', 'summary', 'testcase', 
            'testcase_name', 'environment', 'environment_info',
            'executed_by', 'executed_by_info', 'details', 'success_rate'
        ]
        read_only_fields = [
            'name', 'status', 'success_count', 'fail_count',
            'error_count', 'duration', 'start_time', 'summary',
            'executed_by', 'success_rate', 'environment_info',
            'executed_by_info'
        ]
        
    def get_success_rate(self, obj):
        """计算成功率"""
        total = obj.success_count + obj.fail_count + obj.error_count
        if total == 0:
            return "0"
        rate = obj.success_count / total
        return "1" if rate == 1 else f"{rate:.2f}"
        
    def get_environment_info(self, obj):
        """获取环境信息"""
        if obj.environment:
            return {
                'id': obj.environment.id,
                'name': obj.environment.name,
                'base_url': obj.environment.base_url,
                'description': obj.environment.description,
                'project': {
                    'id': obj.environment.project.id,
                    'name': obj.environment.project.name
                }
            }
        return None

    def get_executed_by_info(self, obj):
        """获取执行人信息"""
        if obj.executed_by:
            return {
                'id': obj.executed_by.id,
                'username': obj.executed_by.username,
                'email': obj.executed_by.email,
                'first_name': obj.executed_by.first_name,
                'last_name': obj.executed_by.last_name
            }
        return None


class InterfaceOptionSerializer(serializers.Serializer):
    """接口选项序列化器"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    method = serializers.CharField()
    url = serializers.CharField()
    description = serializers.CharField()
    example_data = serializers.JSONField(source='get_example_data')
    
    def get_example_data(self, obj):
        """获取示例数据"""
        return {
            'request': {
                'headers': obj.headers,
                'params': obj.params,
                'body': obj.body
            },
            'response': obj.response_example if hasattr(obj, 'response_example') else None
        }