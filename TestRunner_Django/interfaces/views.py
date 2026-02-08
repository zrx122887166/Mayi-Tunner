import logging
import json  # 导入json模块
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from copy import deepcopy
from types import SimpleNamespace

from .models import Interface, InterfaceResult
from .serializers import InterfaceSerializer, InterfaceResultSerializer
from .utils import ResponseHandler
from .runner import InterfaceRunner
from projects.models import Project
from environments.models import Environment
from TestRunner.pagination import CustomPagination

logger = logging.getLogger('testrunner')

class BaseAPIView:
    """API基类"""
    def log_request(self, request, message=''):
        """记录请求日志"""
        method = request.method
        path = request.path
        user = request.user.username if request.user.is_authenticated else 'AnonymousUser'
        params = {
            'GET': request.GET.dict(),
            'POST': request.data if method == 'POST' else {},
            'user': user
        }
        logger.info(f"{message} - {method} {path} - Params: {params}")

class InterfaceViewSet(viewsets.ModelViewSet, BaseAPIView):
    """接口视图集"""
    queryset = Interface.objects.all()
    serializer_class = InterfaceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """获取当前用户有权限的接口列表"""
        # 处理swagger文档生成的情况
        if getattr(self, 'swagger_fake_view', False):
            return Interface.objects.none()

        user = self.request.user
        if user.is_superuser:
            queryset = Interface.objects.all()
        else:
            # 获取用户所属的项目ID列表
            project_ids = user.joined_projects.values_list('id', flat=True)
            queryset = Interface.objects.filter(project_id__in=project_ids)

        # 按项目过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # 专门查询无模块的接口
        no_module = self.request.query_params.get('no_module')
        if no_module and no_module.lower() in ('true', '1', 'yes'):
            return queryset.filter(module__isnull=True)

        # 按模块过滤
        module_id = self.request.query_params.get('module_id')
        if module_id:
            queryset = queryset.filter(module_id=module_id)

        return queryset

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='获取接口列表',
        operation_description='获取当前用户有权限的接口列表，支持分页、按项目和模块过滤',
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description='项目ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'module_id',
                openapi.IN_QUERY,
                description='模块ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'no_module',
                openapi.IN_QUERY,
                description='设置为true时，专门查询无模块的接口',
                type=openapi.TYPE_BOOLEAN
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='总数'),
                            'next': openapi.Schema(type=openapi.TYPE_STRING, description='下一页'),
                            'previous': openapi.Schema(type=openapi.TYPE_STRING, description='上一页'),
                            'results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            )
                        }
                    )
                }
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """获取接口列表"""
        self.log_request(request, '获取接口列表请求')
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'results': serializer.data
            }
            logger.info(f'获取接口列表成功 - page: {request.GET.get("page", 1)}, page_size: {request.GET.get("page_size", 10)}')
            return ResponseHandler.success(
                data=response_data,
                message="获取接口列表成功"
            )
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success(
            data={'results': serializer.data},
            message="获取接口列表成功"
        )

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='获取接口详情',
        operation_description='获取指定接口的详细信息',
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='接口详情数据')
                }
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取接口详情"""
        self.log_request(request, '获取接口详情请求')
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        logger.info(f'获取接口详情成功 - id: {instance.id}, name: {instance.name}')
        return ResponseHandler.success(
            data=serializer.data,
            message="获取接口详情成功"
        )

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='调试接口',
        operation_description='调试已保存的接口',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'environment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='环境ID，如果URL是相对路径则必填'),
                'method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='请求方法',
                    enum=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
                ),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='接口地址'),
                'headers': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='请求头',
                    example={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer token"
                    }
                ),
                'params': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='查询参数',
                    example={
                        "key1": "value1",
                        "key2": "value2"
                    }
                ),
                'body': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='请求体',
                    example={
                        "name": "test",
                        "age": 18
                    }
                ),
                'upload': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='文件上传',
                    example={
                        "file": "${multipart_encoder(file_path='D:/test.txt')}"
                    }
                ),
                'variables': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='变量定义',
                    example={
                        "username": "test",
                        "current_time": "${get_timestamp()}"
                    }
                ),
                'setup_hooks': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='前置钩子',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        example={"hook_var": "${get_timestamp()}"}
                    )
                ),
                'teardown_hooks': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='后置钩子',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        example={"hook_var": "${get_timestamp()}"}
                    )
                ),
                'validators': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='断言规则',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        example={"eq": ["status_code", 200]}
                    )
                ),
                'extract': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='提取变量',
                    example={
                        "token": "body.json.token",
                        "user_id": "body.json.id"
                    }
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='执行状态'),
                            'elapsed': openapi.Schema(type=openapi.TYPE_NUMBER, description='响应时间(ms)'),
                            'request': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='请求信息',
                                properties={
                                    'method': openapi.Schema(type=openapi.TYPE_STRING, description='请求方法'),
                                    'url': openapi.Schema(type=openapi.TYPE_STRING, description='请求URL'),
                                    'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求头'),
                                    'body': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求体')
                                }
                            ),
                            'response': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='响应信息',
                                properties={
                                    'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                                    'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应头'),
                                    'content': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应内容')
                                }
                            ),
                            'validation_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='断言结果',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'check': openapi.Schema(type=openapi.TYPE_STRING, description='检查项'),
                                        'expect': openapi.Schema(type=openapi.TYPE_STRING, description='期望值'),
                                        'actual': openapi.Schema(type=openapi.TYPE_STRING, description='实际值'),
                                        'result': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='验证结果')
                                    }
                                )
                            ),
                            'extracted_variables': openapi.Schema(type=openapi.TYPE_OBJECT, description='提取的变量'),
                            'setup_hooks_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='前置钩子执行结果',
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            ),
                            'teardown_hooks_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='后置钩子执行结果',
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            ),
                            'setup_hooks_info': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='前置钩子详细信息',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'type': openapi.Schema(type=openapi.TYPE_STRING, description='钩子类型（变量定义或函数调用）'),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名（如果是变量定义）'),
                                        'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值（如果是变量定义）'),
                                        'content': openapi.Schema(type=openapi.TYPE_STRING, description='钩子内容（如果是函数调用）'),
                                        'executed': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否已执行')
                                    }
                                )
                            ),
                            'teardown_hooks_info': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='后置钩子详细信息',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'type': openapi.Schema(type=openapi.TYPE_STRING, description='钩子类型（变量定义或函数调用）'),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名（如果是变量定义）'),
                                        'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值（如果是变量定义）'),
                                        'content': openapi.Schema(type=openapi.TYPE_STRING, description='钩子内容（如果是函数调用）'),
                                        'executed': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否已执行')
                                    }
                                )
                            )
                        }
                    )
                }
            )
        }
    )
    @action(detail=True, methods=['post'])
    def debug(self, request, pk=None):
        """调试接口"""
        self.log_request(request, '调试接口请求')
        interface = self.get_object()

        # 获取接口类型，默认为 http
        interface_type = interface.type
        logger.info(f'调试接口 - 类型: {interface_type}, 名称: {interface.name}')

        environment_id = request.data.get('environment_id')

        # 根据接口类型进行不同的处理
        if interface_type == 'http':
            # 检查提交的URL是否已包含http/https前缀
            url = request.data.get('url', interface.url)
            is_absolute_url = url and (url.startswith('http://') or url.startswith('https://'))

            # 如果不是绝对URL，则必须提供环境ID
            if not is_absolute_url and not environment_id:
                logger.warning('调试接口失败：URL不是绝对路径且缺少环境ID')
                return ResponseHandler.error(
                    message="缺少环境ID",
                    errors={"environment_id": ["该字段是必填项，除非提供了完整URL（包含http://或https://前缀）"]}
                )
        elif interface_type == 'sql':
            # SQL类型接口必须提供环境ID以获取数据库配置
            if not environment_id:
                logger.warning('调试SQL接口失败：缺少环境ID')
                return ResponseHandler.error(
                    message="缺少环境ID",
                    errors={"environment_id": ["SQL接口必须提供环境ID以获取数据库配置"]}
                )

        # 如果有环境ID，获取环境；否则创建一个临时环境对象
        if environment_id:
            environment = get_object_or_404(Environment, id=environment_id)

            # 获取环境的数据库配置（针对SQL接口）
            if interface_type == 'sql':
                db_config = environment.get_database_config()
                if not db_config:
                    logger.warning('调试SQL接口失败：环境未配置数据库')
                    return ResponseHandler.error(
                        message="环境未配置数据库",
                        errors={"environment_id": ["选择的环境未关联数据库配置，请在环境管理中设置数据库配置"]}
                    )
        else:
            # 创建一个简单对象，避免使用Django模型实例，防止尝试访问关联关系
            environment = SimpleNamespace()
            environment.pk = None  # 表明这是一个临时对象
            environment.base_url = ""  # 空base_url，URL本身已经是完整的
            environment.name = "临时环境(仅用于绝对URL)"
            environment.parent = None
            environment.project = interface.project
            logger.info(f'使用临时环境调试绝对URL')

        # 更新接口对象的临时属性用于此次调试
        if request.data:
            # 克隆一个新的接口对象，避免修改原始对象
            debug_interface = deepcopy(interface)

            # 根据接口类型更新不同的字段
            if interface_type == 'http':
                fields = ['method', 'url', 'headers', 'params', 'body']
            elif interface_type == 'sql':
                fields = ['sql_method', 'sql', 'sql_params', 'sql_size']
            else:
                fields = []

            # 更新通用字段
            common_fields = ['variables', 'validators', 'extract', 'setup_hooks', 'teardown_hooks']
            fields.extend(common_fields)

            # 更新请求参数
            for field in fields:
                if field in request.data:
                    setattr(debug_interface, field, request.data.get(field))

            # 特殊处理：如果前端传递方法字段不匹配接口类型
            if 'method' in request.data and interface_type == 'sql':
                debug_interface.sql_method = request.data.get('method')
            if 'sql_method' in request.data and interface_type == 'http':
                debug_interface.method = request.data.get('sql_method')
        else:
            debug_interface = interface

        # 准备环境参数
        env_config = {}

        # 获取环境变量
        if hasattr(environment, 'get_all_variables') and callable(environment.get_all_variables):
            env_config['variables'] = environment.get_all_variables()

        # 对于SQL接口，添加数据库配置
        if interface_type == 'sql' and hasattr(environment, 'get_database_config') and callable(environment.get_database_config):
            db_config = environment.get_database_config()
            if db_config:
                env_config['db_config'] = {
                    'user': db_config.username,
                    'password': db_config.password,
                    'ip': db_config.host,
                    'port': db_config.port,
                    'database': db_config.database
                }
                logger.info(f'使用数据库配置: {db_config.name} ({db_config.host}:{db_config.port}/{db_config.database})')

        # 构建测试运行器
        interface_data = debug_interface.get_interface_data()

        # 确保将project_id添加到interface_data中，这对于加载自定义函数是必要的
        interface_data['project_id'] = interface.project_id
        logger.info(f"接口调试 - 添加project_id: {interface.project_id}")

        # 处理前置钩子中的JSON字符串
        processed_setup_hooks = []
        for hook in debug_interface.setup_hooks:
            if isinstance(hook, str) and hook.startswith('{') and hook.endswith('}'):
                # 尝试解析JSON字符串
                try:
                    hook_dict = json.loads(hook)
                    processed_setup_hooks.append(hook_dict)
                    logger.info(f"解析前置钩子JSON字符串成功: {hook_dict}")
                except json.JSONDecodeError:
                    # 如果解析失败，保留原始字符串
                    processed_setup_hooks.append(hook)
                    logger.warning(f"解析前置钩子JSON字符串失败: {hook}")
            # 检查是否是函数ID（纯数字字符串）
            elif isinstance(hook, str) and hook.isdigit():
                # 尝试根据ID加载自定义函数
                try:
                    from functions.models import CustomFunction
                    function_id = int(hook)
                    custom_function = CustomFunction.objects.filter(id=function_id, is_active=True).first()
                    if custom_function:
                        logger.info(f"根据ID加载前置钩子函数: {function_id} -> {custom_function.name}")
                        # 保留原始ID，以便在运行时能够找到对应的函数
                        processed_setup_hooks.append(hook)
                    else:
                        logger.warning(f"找不到ID为{function_id}的前置钩子函数或函数未启用")
                        processed_setup_hooks.append(hook)  # 仍然保留原始ID
                except Exception as e:
                    logger.error(f"加载前置钩子函数ID {hook} 失败: {str(e)}")
                    processed_setup_hooks.append(hook)  # 仍然保留原始ID
            else:
                processed_setup_hooks.append(hook)
        debug_interface.setup_hooks = processed_setup_hooks

        # 处理后置钩子中的JSON字符串
        processed_teardown_hooks = []
        for hook in debug_interface.teardown_hooks:
            if isinstance(hook, str) and hook.startswith('{') and hook.endswith('}'):
                # 尝试解析JSON字符串
                try:
                    hook_dict = json.loads(hook)
                    processed_teardown_hooks.append(hook_dict)
                    logger.info(f"解析后置钩子JSON字符串成功: {hook_dict}")
                except json.JSONDecodeError:
                    # 如果解析失败，保留原始字符串
                    processed_teardown_hooks.append(hook)
                    logger.warning(f"解析后置钩子JSON字符串失败: {hook}")
            # 检查是否是函数ID（纯数字字符串）
            elif isinstance(hook, str) and hook.isdigit():
                # 尝试根据ID加载自定义函数
                try:
                    from functions.models import CustomFunction
                    function_id = int(hook)
                    custom_function = CustomFunction.objects.filter(id=function_id, is_active=True).first()
                    if custom_function:
                        logger.info(f"根据ID加载后置钩子函数: {function_id} -> {custom_function.name}")
                        # 保留原始ID，以便在运行时能够找到对应的函数
                        processed_teardown_hooks.append(hook)
                    else:
                        logger.warning(f"找不到ID为{function_id}的后置钩子函数或函数未启用")
                        processed_teardown_hooks.append(hook)  # 仍然保留原始ID
                except Exception as e:
                    logger.error(f"加载后置钩子函数ID {hook} 失败: {str(e)}")
                    processed_teardown_hooks.append(hook)  # 仍然保留原始ID
            else:
                processed_teardown_hooks.append(hook)
        debug_interface.teardown_hooks = processed_teardown_hooks

        # 记录前后置钩子信息
        logger.info(f"接口调试前置钩子(处理后): {debug_interface.setup_hooks}")
        logger.info(f"接口调试后置钩子(处理后): {debug_interface.teardown_hooks}")

        # 重新获取接口数据，确保包含处理后的钩子
        interface_data = debug_interface.get_interface_data()
        
        # 确保将project_id添加到interface_data中，这对于加载自定义函数和全局参数是必要的
        interface_data['project_id'] = interface.project_id
        logger.info(f"接口调试 - 重新添加project_id: {interface.project_id}")

        # 确保将从环境中获取的 base_url 和 verify_ssl 传递给 InterfaceRunner
        if environment_id:
            # environment 变量已在前面获取
            interface_data['base_url'] = environment.base_url
            interface_data['verify'] = environment.verify_ssl
            logger.info(f"使用环境配置: base_url='{environment.base_url}', verify={environment.verify_ssl}")
        elif not is_absolute_url: # 如果是相对URL但没有环境ID (虽然前面已阻止，但以防万一)
             interface_data['base_url'] = ""
             interface_data['verify'] = None
             logger.warning("相对URL但无环境ID，base_url设置为空")

        # 创建接口包装对象（与quick_debug方法中相同的类）
        # 注意：InterfaceWrapper 现在不需要了，因为我们直接修改 interface_data
        # class InterfaceWrapper:
        #     def __init__(self, data, project_obj):
        #         self.__dict__.update(data)
        #         self.project = project_obj
        #         self.project_id = project_obj.id
        #         self.name = data.get('name', '接口调试')
        #
        #     def get_interface_data(self):
        #         return {k: v for k, v in self.__dict__.items()
        #                 if k not in ['project']}

        # 创建包装对象 - 不再需要
        # interface_wrapper = InterfaceWrapper(interface_data, interface.project)

        # 创建InterfaceRunner实例 - 直接使用更新后的 interface_data
        runner = InterfaceRunner(interface_data)

        # 先运行接口获取数据
        try:
            # <<< START MODIFICATION >>>
            # base_url 和 verify 已在初始化时处理，这里只需处理 variables 和 db_config
            if env_config:
                if 'variables' in env_config:
                    # 更新 runner 的变量
                    runner.variables = runner.variables or {}
                    runner.variables.update(env_config['variables'])
                    runner.config.variables(**runner.variables)  # 设置config.variables以确保全局参数生效
                    logger.debug(f"Runner 变量已更新: {runner.variables}")

                if 'db_config' in env_config and interface_type == 'sql':
                    # 直接设置db_config到runner的interface_data中 (根据runner.py逻辑)
                    runner.interface_data['db_config'] = env_config['db_config']
                    logger.debug(f"Runner 数据库配置已更新: {runner.interface_data['db_config']}")
            # <<< END MODIFICATION >>>

            # 运行接口测试 - 不再需要传递 environment 参数给 run_interface
            runner.run_interface()
            summary = runner.get_summary()

            # 获取测试结果
            step_result = summary.step_results[0] if summary.step_results else None
            session_data = step_result.data if step_result else None

            # 从step_result中获取变量值
            step_variables = {}
            if step_result and hasattr(step_result, 'export_vars'):
                step_variables.update(step_result.export_vars)

            # 如果runner有variables属性，合并这些变量
            if hasattr(runner, 'variables'):
                step_variables.update(runner.variables)

            # 判断接口类型，构建不同的结果
            if interface_type == 'http':
                req_resp = session_data.req_resps[0] if session_data and session_data.req_resps else None

                # 构建HTTP接口结果
                result = {
                    "success": True,  # 接口调用成功
                    "elapsed": getattr(summary.time, 'duration', 0),
                    "request": {
                        "method": req_resp.request.method if req_resp else "",
                        "url": req_resp.request.url if req_resp else "",
                        "headers": dict(getattr(req_resp.request, 'headers', {})) if req_resp else {},
                        "body": None  # 默认为None，下面会根据实际情况填充
                    },
                    "response": {
                        "status_code": req_resp.response.status_code if req_resp else 0,
                        "headers": dict(getattr(req_resp.response, 'headers', {})) if req_resp else {},
                        "content": getattr(req_resp.response, 'body', None) if req_resp else None
                    },
                    "validation_results": session_data.validators.get("validate_extractor", []) if session_data else [],
                    "extracted_variables": step_result.export_vars if step_result else {}
                }

                # 安全地获取请求体
                if req_resp and hasattr(req_resp.request, 'body'):
                    result["request"]["body"] = req_resp.request.body
                elif req_resp and hasattr(req_resp.request, 'json'):
                    result["request"]["body"] = req_resp.request.json
            elif interface_type == 'sql':
                # 构建SQL接口结果
                sql_response = getattr(step_result, 'sql_response', None)

                result = {
                    "success": True,  # 接口调用成功
                    "elapsed": getattr(summary.time, 'duration', 0),
                    "request": {
                        "method": interface_data.get('method', ''),
                        "sql": interface_data.get('sql', ''),
                        "params": interface_data.get('params', {}),
                        "size": interface_data.get('size', 10) if interface_data.get('method') == 'fetchmany' else None,
                        "db_config": {
                            "host": env_config.get('db_config', {}).get('ip', ''),
                            "port": env_config.get('db_config', {}).get('port', ''),
                            "database": env_config.get('db_config', {}).get('database', '')
                        }
                    },
                    "response": sql_response if sql_response else None,
                    "validation_results": session_data.validators.get("validate_extractor", []) if session_data else [],
                    "extracted_variables": step_result.export_vars if step_result else {}
                }
            else:
                # 未知接口类型，返回通用结果
                result = {
                    "success": True,
                    "elapsed": getattr(summary.time, 'duration', 0),
                    "validation_results": session_data.validators.get("validate_extractor", []) if session_data else [],
                    "extracted_variables": step_result.export_vars if step_result else {}
                }

            # 提取并添加钩子函数的执行结果 - 增强版
            if debug_interface.setup_hooks:
                # 即使没有找到执行结果，也至少返回钩子定义
                setup_hooks_info = []
                for i, hook in enumerate(debug_interface.setup_hooks):
                    if isinstance(hook, dict):
                        # 检查是否是SQL钩子
                        if "type" in hook and hook["type"] == "sql":
                            # SQL钩子，作为一个整体处理
                            sql_info = {
                                "type": "sql_call",
                                "sql": hook.get("sql", ""),
                                "db_id": hook.get("db_id"),
                                "var_name": hook.get("var_name", ""),
                                "executed": True,
                                "value": step_variables.get(hook.get("var_name", ""), "")  # 添加实际查询结果值
                            }
                            setup_hooks_info.append(sql_info)
                        elif len(hook) == 1:
                            # 检查是否是嵌套的SQL钩子
                            var_name, hook_content = list(hook.items())[0]
                            if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                                # 嵌套的SQL钩子
                                sql_info = {
                                    "type": "sql_call",
                                    "sql": hook_content.get("sql", ""),
                                    "db_id": hook_content.get("db_id"),
                                    "var_name": var_name,
                                    "executed": True,
                                    "value": step_variables.get(var_name, "")  # 添加实际查询结果值
                                }
                                setup_hooks_info.append(sql_info)
                            else:
                                # 普通变量定义
                                setup_hooks_info.append({
                                    "type": "variable_definition",
                                    "name": var_name,
                                    "value": hook_content,
                                    "executed": True
                                })
                        else:
                            # 多键字典，逐个处理
                            for var_name, hook_content in hook.items():
                                setup_hooks_info.append({
                                    "type": "variable_definition",
                                    "name": var_name,
                                    "value": hook_content,
                                    "executed": True
                                })
                    else:
                        setup_hooks_info.append({
                            "type": "function_call",
                            "content": hook,
                            "executed": True
                        })
                result["setup_hooks_info"] = setup_hooks_info

            if debug_interface.teardown_hooks:
                # 即使没有找到执行结果，也至少返回钩子定义
                teardown_hooks_info = []
                for i, hook in enumerate(debug_interface.teardown_hooks):
                    if isinstance(hook, dict):
                        # 检查是否是SQL钩子
                        if "type" in hook and hook["type"] == "sql":
                            # SQL钩子，作为一个整体处理
                            sql_info = {
                                "type": "sql_call",
                                "sql": hook.get("sql", ""),
                                "db_id": hook.get("db_id"),
                                "var_name": hook.get("var_name", ""),
                                "executed": True,
                                "value": step_variables.get(hook.get("var_name", ""), "")  # 添加实际查询结果值
                            }
                            teardown_hooks_info.append(sql_info)
                        elif len(hook) == 1:
                            # 检查是否是嵌套的SQL钩子
                            var_name, hook_content = list(hook.items())[0]
                            if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                                # 嵌套的SQL钩子
                                sql_info = {
                                    "type": "sql_call",
                                    "sql": hook_content.get("sql", ""),
                                    "db_id": hook_content.get("db_id"),
                                    "var_name": var_name,
                                    "executed": True,
                                    "value": step_variables.get(var_name, "")  # 添加实际查询结果值
                                }
                                teardown_hooks_info.append(sql_info)
                            else:
                                # 普通变量定义
                                teardown_hooks_info.append({
                                    "type": "variable_definition",
                                    "name": var_name,
                                    "value": hook_content,
                                    "executed": True
                                })
                        else:
                            # 多键字典，逐个处理
                            for var_name, hook_content in hook.items():
                                teardown_hooks_info.append({
                                    "type": "variable_definition",
                                    "name": var_name,
                                    "value": hook_content,
                                    "executed": True
                                })
                    else:
                        teardown_hooks_info.append({
                            "type": "function_call",
                            "content": hook,
                            "executed": True
                        })
                result["teardown_hooks_info"] = teardown_hooks_info

            # 尝试从summary中获取钩子执行结果（旧逻辑保留，与新方法共存）
            if hasattr(summary, "details") and summary.details and len(summary.details) > 0:
                case_detail = summary.details[0]

                # 添加前置钩子结果
                setup_hooks = case_detail.get("setup_hooks", [])
                if setup_hooks:
                    result["setup_hooks_results"] = setup_hooks
                    logger.info(f"前置钩子执行结果: {setup_hooks}")

                # 添加后置钩子结果
                teardown_hooks = case_detail.get("teardown_hooks", [])
                if teardown_hooks:
                    result["teardown_hooks_results"] = teardown_hooks
                    logger.info(f"后置钩子执行结果: {teardown_hooks}")

            # 尝试从step_results中获取钩子执行结果（新增逻辑）
            if hasattr(summary, "step_results") and summary.step_results:
                step_result = summary.step_results[0]
                if hasattr(step_result, "hooks_results"):
                    hooks_results = step_result.hooks_results
                    if "setup_hooks" in hooks_results and hooks_results["setup_hooks"]:
                        result["setup_hooks_results"] = hooks_results["setup_hooks"]
                    if "teardown_hooks" in hooks_results and hooks_results["teardown_hooks"]:
                        result["teardown_hooks_results"] = hooks_results["teardown_hooks"]

            # 检查验证结果
            validation_results = session_data.validators if session_data else {}
            validation_success = validation_results.get("success", True)

            if validation_success:
                logger.info(f'接口调试成功 - interface: {interface.name}')
            else:
                failures = validation_results.get("failures", "未知断言失败")
                logger.warning(f'接口断言失败 - interface: {interface.name}, failures: {failures}')

                # 将失败信息添加到结果中
                result["validation_failures"] = failures

            return ResponseHandler.success(
                data=result,
                message="接口调试完成"
            )

        except AttributeError as e:
            # 具体处理请求体或其他属性访问错误
            error_message = str(e)
            logger.error(f'接口调试属性访问错误: {error_message}')
            return ResponseHandler.error(
                message="接口调试属性访问错误",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={'detail': [f"属性访问错误: {error_message}. 可能是HttpRunner库版本不兼容。"]}
            )
        except Exception as e:
            # 处理其他可能的错误
            error_message = str(e)
            logger.error(f'接口调试失败: {error_message}')
            return ResponseHandler.error(
                message="接口调试失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={'detail': [error_message]}
            )

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='快速调试接口',
        operation_description='快速调试接口，无需先创建和保存接口',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['project_id', 'method', 'url'],
            properties={
                'project_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='项目ID'),
                'environment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='环境ID，如果URL是相对路径则必填'),
                'method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='请求方法',
                    enum=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
                ),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='接口地址'),
                'headers': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='请求头',
                    example={
                        "Content-Type": "application/json",
                        "Authorization": "Bearer token"
                    }
                ),
                'params': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='查询参数',
                    example={
                        "key1": "value1",
                        "key2": "value2"
                    }
                ),
                'body': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='请求体',
                    example={
                        "name": "test",
                        "age": 18
                    }
                ),
                'upload': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='文件上传',
                    example={
                        "file": "${multipart_encoder(file_path='D:/test.txt')}"
                    }
                ),
                'variables': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='变量定义',
                    example={
                        "username": "test",
                        "current_time": "${get_timestamp()}"
                    }
                ),
                'setup_hooks': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='前置钩子',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        example={"hook_var": "${get_timestamp()}"}
                    )
                ),
                'teardown_hooks': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='后置钩子',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        example={"hook_var": "${get_timestamp()}"}
                    )
                ),
                'validators': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='断言规则',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        example={"eq": ["status_code", 200]}
                    )
                ),
                'extract': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description='提取变量',
                    example={
                        "token": "body.json.token",
                        "user_id": "body.json.id"
                    }
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='执行状态'),
                            'elapsed': openapi.Schema(type=openapi.TYPE_NUMBER, description='响应时间(ms)'),
                            'request': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='请求信息',
                                properties={
                                    'method': openapi.Schema(type=openapi.TYPE_STRING, description='请求方法'),
                                    'url': openapi.Schema(type=openapi.TYPE_STRING, description='请求URL'),
                                    'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求头'),
                                    'body': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求体')
                                }
                            ),
                            'response': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                description='响应信息',
                                properties={
                                    'status_code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                                    'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应头'),
                                    'content': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应内容')
                                }
                            ),
                            'validation_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='断言结果',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'check': openapi.Schema(type=openapi.TYPE_STRING, description='检查项'),
                                        'expect': openapi.Schema(type=openapi.TYPE_STRING, description='期望值'),
                                        'actual': openapi.Schema(type=openapi.TYPE_STRING, description='实际值'),
                                        'result': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='验证结果')
                                    }
                                )
                            ),
                            'extracted_variables': openapi.Schema(type=openapi.TYPE_OBJECT, description='提取的变量'),
                            'setup_hooks_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='前置钩子执行结果',
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            ),
                            'teardown_hooks_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='后置钩子执行结果',
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            ),
                            'setup_hooks_info': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='前置钩子详细信息',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'type': openapi.Schema(type=openapi.TYPE_STRING, description='钩子类型（变量定义或函数调用）'),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名（如果是变量定义）'),
                                        'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值（如果是变量定义）'),
                                        'content': openapi.Schema(type=openapi.TYPE_STRING, description='钩子内容（如果是函数调用）'),
                                        'executed': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否已执行')
                                    }
                                )
                            ),
                            'teardown_hooks_info': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='后置钩子详细信息',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'type': openapi.Schema(type=openapi.TYPE_STRING, description='钩子类型（变量定义或函数调用）'),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名（如果是变量定义）'),
                                        'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值（如果是变量定义）'),
                                        'content': openapi.Schema(type=openapi.TYPE_STRING, description='钩子内容（如果是函数调用）'),
                                        'executed': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否已执行')
                                    }
                                )
                            )
                        }
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def quick_debug(self, request):
        """快速调试接口，无需先创建和保存接口"""
        self.log_request(request, '快速调试接口请求')

        # 创建包装类，提供project属性
        class InterfaceWrapper:
            def __init__(self, data, project_obj):
                self.__dict__.update(data)
                self.project = project_obj
                self.project_id = project_obj.id
                self.name = data.get('name', '快速调试接口')

            def get_interface_data(self):
                return {k: v for k, v in self.__dict__.items()
                        if k not in ['project']}

        try:
            # 验证必要的参数
            project_id = request.data.get('project_id')
            interface_type = request.data.get('type', 'http')  # 默认为HTTP类型

            if not project_id:
                logger.warning('快速调试接口失败：缺少项目ID')
                return ResponseHandler.error(
                    message="缺少项目ID",
                    errors={"project_id": ["该字段是必填项"]}
                )

            # 根据接口类型验证必要参数
            if interface_type == 'http':
                method = request.data.get('method')
                url = request.data.get('url')

                if not method:
                    logger.warning('快速调试接口失败：缺少请求方法')
                    return ResponseHandler.error(
                        message="缺少请求方法",
                        errors={"method": ["该字段是必填项"]}
                    )

                if not url:
                    logger.warning('快速调试接口失败：缺少接口URL')
                    return ResponseHandler.error(
                        message="缺少接口URL",
                        errors={"url": ["该字段是必填项"]}
                    )
            elif interface_type == 'sql':
                method = request.data.get('method', request.data.get('sql_method'))
                sql = request.data.get('sql')

                if not method:
                    logger.warning('快速调试SQL接口失败：缺少SQL方法')
                    return ResponseHandler.error(
                        message="缺少SQL方法",
                        errors={"method": ["该字段是必填项"]}
                    )

                if not sql:
                    logger.warning('快速调试SQL接口失败：缺少SQL语句')
                    return ResponseHandler.error(
                        message="缺少SQL语句",
                        errors={"sql": ["该字段是必填项"]}
                    )

                # SQL接口必须提供环境ID以获取数据库配置
                environment_id = request.data.get('environment_id')
                if not environment_id:
                    logger.warning('快速调试SQL接口失败：缺少环境ID')
                    return ResponseHandler.error(
                        message="缺少环境ID",
                        errors={"environment_id": ["SQL接口必须提供环境ID以获取数据库配置"]}
                    )

            # 检查项目权限
            project = Project.objects.get(id=project_id)
            user = request.user

            # 检查用户是否有权限操作该项目
            if not project.has_permission(user):
                logger.warning(f'快速调试接口失败：用户无权限操作项目 - user_id: {user.id}, project_id: {project_id}')
                raise PermissionDenied("您没有操作该项目的权限")

            # 构建临时接口数据
            interface_data = {
                'name': request.data.get('name', f'快速调试接口 {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}'),
                'project_id': project_id,
                'type': interface_type
            }

            # 设置接口数据
            if interface_type == 'http':
                interface_data.update({
                    'method': method,
                    'url': url,
                    'headers': request.data.get('headers', {}),
                    'params': request.data.get('params', {}),
                    'body': request.data.get('body', {}),
                })
            elif interface_type == 'sql':
                interface_data.update({
                    'method': method,
                    'sql': sql,
                    'params': request.data.get('sql_params', {}),
                    'size': request.data.get('sql_size', 10),
                })

            # 设置通用字段
            interface_data.update({
                'variables': request.data.get('variables', {}),
                'validators': request.data.get('validators', []),
                'extract': request.data.get('extract', {}),
                'setup_hooks': request.data.get('setup_hooks', []),
                'teardown_hooks': request.data.get('teardown_hooks', []),
            })

            # 确保前后置钩子字段存在且不为None
            if interface_data.get('setup_hooks') is None:
                interface_data['setup_hooks'] = []
            if interface_data.get('teardown_hooks') is None:
                interface_data['teardown_hooks'] = []

            # 处理前置钩子中的JSON字符串
            processed_setup_hooks = []
            for hook in interface_data['setup_hooks']:
                if isinstance(hook, str) and hook.startswith('{') and hook.endswith('}'):
                    # 尝试解析JSON字符串
                    try:
                        hook_dict = json.loads(hook)
                        processed_setup_hooks.append(hook_dict)
                        logger.info(f"解析前置钩子JSON字符串成功: {hook_dict}")
                    except json.JSONDecodeError:
                        # 如果解析失败，保留原始字符串
                        processed_setup_hooks.append(hook)
                        logger.warning(f"解析前置钩子JSON字符串失败: {hook}")
                else:
                    processed_setup_hooks.append(hook)
            interface_data['setup_hooks'] = processed_setup_hooks

            # 处理后置钩子中的JSON字符串
            processed_teardown_hooks = []
            for hook in interface_data['teardown_hooks']:
                if isinstance(hook, str) and hook.startswith('{') and hook.endswith('}'):
                    # 尝试解析JSON字符串
                    try:
                        hook_dict = json.loads(hook)
                        processed_teardown_hooks.append(hook_dict)
                        logger.info(f"解析后置钩子JSON字符串成功: {hook_dict}")
                    except json.JSONDecodeError:
                        # 如果解析失败，保留原始字符串
                        processed_teardown_hooks.append(hook)
                        logger.warning(f"解析后置钩子JSON字符串失败: {hook}")
                else:
                    processed_teardown_hooks.append(hook)
            interface_data['teardown_hooks'] = processed_teardown_hooks

            # 记录前后置钩子信息
            logger.info(f"快速调试接口前置钩子(处理后): {interface_data['setup_hooks']}")
            logger.info(f"快速调试接口后置钩子(处理后): {interface_data['teardown_hooks']}")

            # 获取环境信息
            environment_id = request.data.get('environment_id')
            env_config = {}

            if environment_id:
                try:
                    environment = Environment.objects.get(id=environment_id)

                    # 检查环境是否属于该项目
                    if environment.project.id != int(project_id):
                        logger.warning(f'快速调试接口失败：环境不属于该项目 - environment_id: {environment_id}, project_id: {project_id}')
                        return ResponseHandler.error(
                            message="环境不属于该项目",
                            errors={"environment_id": ["环境必须属于指定的项目"]}
                        )

                    # 获取环境变量
                    if hasattr(environment, 'get_all_variables') and callable(environment.get_all_variables):
                        env_config['variables'] = environment.get_all_variables()

                    # 获取base_url (仅HTTP接口需要)
                    if interface_type == 'http':
                        interface_data['base_url'] = environment.base_url
                        interface_data['verify'] = environment.verify_ssl

                    # 获取数据库配置 (仅SQL接口需要)
                    if interface_type == 'sql':
                        db_config = environment.get_database_config()
                        if not db_config:
                            logger.warning('快速调试SQL接口失败：环境未配置数据库')
                            return ResponseHandler.error(
                                message="环境未配置数据库",
                                errors={"environment_id": ["选择的环境未关联数据库配置，请在环境管理中设置数据库配置"]}
                            )

                        env_config['db_config'] = {
                            'user': db_config.username,
                            'password': db_config.password,
                            'ip': db_config.host,
                            'port': db_config.port,
                            'database': db_config.database
                        }
                        logger.info(f'使用数据库配置: {db_config.name} ({db_config.host}:{db_config.port}/{db_config.database})')
                except Environment.DoesNotExist:
                    logger.warning(f'快速调试接口失败：环境不存在 - environment_id: {environment_id}')
                    return ResponseHandler.error(
                        message="环境不存在",
                        errors={"environment_id": ["指定的环境不存在"]}
                    )

            # 创建接口包装对象
            interface_wrapper = InterfaceWrapper(interface_data, project)

            # 创建InterfaceRunner实例
            runner = InterfaceRunner(interface_wrapper.get_interface_data())

            try:
                # 设置环境配置
                if env_config:
                    if 'variables' in env_config:
                        # 确保variables字段存在
                        runner.variables = runner.variables or {}
                        runner.variables.update(env_config['variables'])
                        runner.config.variables(**runner.variables)

                    if 'db_config' in env_config and interface_type == 'sql':
                        # 直接设置db_config到runner中
                        runner.interface_data['db_config'] = env_config['db_config']

                # 运行接口测试
                runner.run_interface()
                summary = runner.get_summary()

                # 获取测试结果
                step_result = summary.step_results[0] if summary.step_results else None
                session_data = step_result.data if step_result else None

                # 从step_result中获取变量值
                step_variables = {}
                if step_result and hasattr(step_result, 'export_vars'):
                    step_variables.update(step_result.export_vars)

                # 如果runner有variables属性，合并这些变量
                if hasattr(runner, 'variables'):
                    step_variables.update(runner.variables)

                # 判断接口类型，构建不同的结果
                if interface_type == 'http':
                    req_resp = session_data.req_resps[0] if session_data and session_data.req_resps else None

                    # 构建HTTP接口结果
                    result = {
                        "success": True,  # 接口调用成功
                        "elapsed": getattr(summary.time, 'duration', 0),
                        "request": {
                            "method": req_resp.request.method if req_resp else "",
                            "url": req_resp.request.url if req_resp else "",
                            "headers": dict(getattr(req_resp.request, 'headers', {})) if req_resp else {},
                            "body": None  # 默认为None，下面会根据实际情况填充
                        },
                        "response": {
                            "status_code": req_resp.response.status_code if req_resp else 0,
                            "headers": dict(getattr(req_resp.response, 'headers', {})) if req_resp else {},
                            "content": getattr(req_resp.response, 'body', None) if req_resp else None
                        },
                        "validation_results": session_data.validators.get("validate_extractor", []) if session_data else [],
                        "extracted_variables": step_result.export_vars if step_result else {}
                    }

                    # 安全地获取请求体
                    if req_resp and hasattr(req_resp.request, 'body'):
                        result["request"]["body"] = req_resp.request.body
                    elif req_resp and hasattr(req_resp.request, 'json'):
                        result["request"]["body"] = req_resp.request.json
                elif interface_type == 'sql':
                    # 构建SQL接口结果
                    sql_response = getattr(step_result, 'sql_response', None)

                    result = {
                        "success": True,  # 接口调用成功
                        "elapsed": getattr(summary.time, 'duration', 0),
                        "request": {
                            "method": interface_data.get('method', ''),
                            "sql": interface_data.get('sql', ''),
                            "params": interface_data.get('params', {}),
                            "size": interface_data.get('size', 10) if interface_data.get('method') == 'fetchmany' else None,
                            "db_config": {
                                "host": env_config.get('db_config', {}).get('ip', ''),
                                "port": env_config.get('db_config', {}).get('port', ''),
                                "database": env_config.get('db_config', {}).get('database', '')
                            }
                        },
                        "response": sql_response if sql_response else None,
                        "validation_results": session_data.validators.get("validate_extractor", []) if session_data else [],
                        "extracted_variables": step_result.export_vars if step_result else {}
                    }
                else:
                    # 未知接口类型，返回通用结果
                    result = {
                        "success": True,
                        "elapsed": getattr(summary.time, 'duration', 0),
                        "validation_results": session_data.validators.get("validate_extractor", []) if session_data else [],
                        "extracted_variables": step_result.export_vars if step_result else {}
                    }

                # 提取钩子执行结果
                if interface_data.get('setup_hooks'):
                    setup_hooks_info = []
                    for hook in interface_data['setup_hooks']:
                        if isinstance(hook, dict):
                            # 检查是否是SQL钩子
                            if "type" in hook and hook["type"] == "sql":
                                # SQL钩子，作为一个整体处理
                                sql_info = {
                                    "type": "sql_call",
                                    "sql": hook.get("sql", ""),
                                    "db_id": hook.get("db_id"),
                                    "var_name": hook.get("var_name", ""),
                                    "executed": True,
                                    "value": step_variables.get(hook.get("var_name", ""), "")  # 添加实际查询结果值
                                }
                                setup_hooks_info.append(sql_info)
                            elif len(hook) == 1:
                                # 检查是否是嵌套的SQL钩子
                                var_name, hook_content = list(hook.items())[0]
                                if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                                    # 嵌套的SQL钩子
                                    sql_info = {
                                        "type": "sql_call",
                                        "sql": hook_content.get("sql", ""),
                                        "db_id": hook_content.get("db_id"),
                                        "var_name": var_name,
                                        "executed": True,
                                        "value": step_variables.get(var_name, "")  # 添加实际查询结果值
                                    }
                                    setup_hooks_info.append(sql_info)
                                else:
                                    # 普通变量定义
                                    setup_hooks_info.append({
                                        "type": "variable_definition",
                                        "name": var_name,
                                        "value": hook_content,
                                        "executed": True
                                    })
                            else:
                                # 多键字典，逐个处理
                                for var_name, hook_content in hook.items():
                                    setup_hooks_info.append({
                                        "type": "variable_definition",
                                        "name": var_name,
                                        "value": hook_content,
                                        "executed": True
                                    })
                        else:
                            setup_hooks_info.append({
                                "type": "function_call",
                                "content": hook,
                                "executed": True
                            })
                    result["setup_hooks_info"] = setup_hooks_info

                if interface_data.get('teardown_hooks'):
                    teardown_hooks_info = []
                    for hook in interface_data['teardown_hooks']:
                        if isinstance(hook, dict):
                            # 检查是否是SQL钩子
                            if "type" in hook and hook["type"] == "sql":
                                # SQL钩子，作为一个整体处理
                                sql_info = {
                                    "type": "sql_call",
                                    "sql": hook.get("sql", ""),
                                    "db_id": hook.get("db_id"),
                                    "var_name": hook.get("var_name", ""),
                                    "executed": True,
                                    "value": step_variables.get(hook.get("var_name", ""), "")  # 添加实际查询结果值
                                }
                                teardown_hooks_info.append(sql_info)
                            elif len(hook) == 1:
                                # 检查是否是嵌套的SQL钩子
                                var_name, hook_content = list(hook.items())[0]
                                if isinstance(hook_content, dict) and hook_content.get("type") == "sql":
                                    # 嵌套的SQL钩子
                                    sql_info = {
                                        "type": "sql_call",
                                        "sql": hook_content.get("sql", ""),
                                        "db_id": hook_content.get("db_id"),
                                        "var_name": var_name,
                                        "executed": True,
                                        "value": step_variables.get(var_name, "")  # 添加实际查询结果值
                                    }
                                    teardown_hooks_info.append(sql_info)
                                else:
                                    # 普通变量定义
                                    teardown_hooks_info.append({
                                        "type": "variable_definition",
                                        "name": var_name,
                                        "value": hook_content,
                                        "executed": True
                                    })
                            else:
                                # 多键字典，逐个处理
                                for var_name, hook_content in hook.items():
                                    teardown_hooks_info.append({
                                        "type": "variable_definition",
                                        "name": var_name,
                                        "value": hook_content,
                                        "executed": True
                                    })
                        else:
                            teardown_hooks_info.append({
                                "type": "function_call",
                                "content": hook,
                                "executed": True
                            })
                    result["teardown_hooks_info"] = teardown_hooks_info

                # 尝试从summary中获取钩子执行结果
                if hasattr(summary, "details") and summary.details and len(summary.details) > 0:
                    case_detail = summary.details[0]
                    if "setup_hooks" in case_detail and case_detail["setup_hooks"]:
                        result["setup_hooks_results"] = case_detail["setup_hooks"]
                    if "teardown_hooks" in case_detail and case_detail["teardown_hooks"]:
                        result["teardown_hooks_results"] = case_detail["teardown_hooks"]

                # 尝试从step_results中获取钩子执行结果
                if hasattr(summary, "step_results") and summary.step_results:
                    step_result = summary.step_results[0]
                    if hasattr(step_result, "hooks_results"):
                        hooks_results = step_result.hooks_results
                        if "setup_hooks" in hooks_results and hooks_results["setup_hooks"]:
                            result["setup_hooks_results"] = hooks_results["setup_hooks"]
                        if "teardown_hooks" in hooks_results and hooks_results["teardown_hooks"]:
                            result["teardown_hooks_results"] = hooks_results["teardown_hooks"]

                # 检查验证结果
                validation_results = session_data.validators if session_data else {}
                validation_success = validation_results.get("success", True)

                if validation_success:
                    logger.info(f'快速调试接口成功 - project: {project.name}, type: {interface_type}')
                else:
                    failures = validation_results.get("failures", "未知断言失败")
                    logger.warning(f'快速调试接口断言失败 - project: {project.name}, failures: {failures}')
                    result["validation_failures"] = failures

                return ResponseHandler.success(
                    data=result,
                    message="快速调试接口完成"
                )

            except AttributeError as e:
                error_message = str(e)
                logger.error(f'快速调试接口属性访问错误: {error_message}')
                return ResponseHandler.error(
                    message="快速调试接口属性访问错误",
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    errors={'detail': [f"属性访问错误: {error_message}. 可能是HttpRunner库版本不兼容。"]}
                )
            except Exception as e:
                error_message = str(e)
                logger.error(f'快速调试接口失败: {error_message}')
                return ResponseHandler.error(
                    message="快速调试接口失败",
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    errors={'detail': [error_message]}
                )

        except Project.DoesNotExist:
            logger.warning(f'快速调试接口失败：项目不存在 - project_id: {project_id}')
            return ResponseHandler.error(
                message="项目不存在",
                errors={"project_id": ["指定的项目不存在"]}
            )
        except PermissionDenied as e:
            return ResponseHandler.error(
                message=str(e),
                code=status.HTTP_403_FORBIDDEN,
                errors={"project_id": ["无权限操作该项目"]}
            )
        except Exception as e:
            error_message = str(e)
            logger.error(f'快速调试接口失败: {error_message}')
            return ResponseHandler.error(
                message="快速调试接口失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={'detail': [error_message]}
            )

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='新建接口',
        operation_description='新建一个测试接口，需要提供必要的接口信息',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'method', 'url', 'project'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='接口名称'),
                'method': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='请求方法',
                    enum=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
                ),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='接口地址'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                'module': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属模块ID'),
                'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求头'),
                'params': openapi.Schema(type=openapi.TYPE_OBJECT, description='查询参数'),
                'body': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求体'),
                'setup_hooks': openapi.Schema(type=openapi.TYPE_ARRAY, description='前置钩子', items=openapi.Schema(type=openapi.TYPE_STRING)),
                'teardown_hooks': openapi.Schema(type=openapi.TYPE_ARRAY, description='后置钩子', items=openapi.Schema(type=openapi.TYPE_STRING)),
                'variables': openapi.Schema(type=openapi.TYPE_OBJECT, description='变量定义'),
                'validators': openapi.Schema(type=openapi.TYPE_ARRAY, description='断言规则', items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                'extract': openapi.Schema(type=openapi.TYPE_OBJECT, description='提取变量')
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='新建的接口信息')
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """新建接口"""
        self.log_request(request, '新建接口请求')
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            logger.info(f'新建接口成功 - name: {serializer.validated_data.get("name")}')
            return ResponseHandler.success(
                data=serializer.data,
                message="新建接口成功",
                code=status.HTTP_201_CREATED
            )
        except serializers.ValidationError as e:
            # 处理验证错误
            errors = e.detail

            # 检查是否有唯一性约束错误
            if 'non_field_errors' in errors and any('唯一' in str(error) or '必须能构成唯一集合' in str(error) for error in errors['non_field_errors']):
                # 提取项目ID和接口名称
                project_id = request.data.get('project')
                interface_name = request.data.get('name')

                # 构建更友好的错误信息
                error_message = f"创建失败：项目中已存在名为 '{interface_name}' 的接口，请使用其他名称"
                logger.warning(f'新建接口失败 - 名称冲突: {interface_name}, 项目ID: {project_id}')

                return ResponseHandler.error(
                    message=error_message,
                    errors={"name": [f"项目中已存在名为 '{interface_name}' 的接口，请使用其他名称"]},
                    code=status.HTTP_400_BAD_REQUEST
                )

            # 其他验证错误
            logger.warning(f'新建接口失败 - 验证错误: {errors}')
            return ResponseHandler.error(
                message="创建接口失败，请检查输入",
                errors=errors,
                code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # 处理其他异常
            logger.error(f'新建接口失败 - 异常: {str(e)}')
            return ResponseHandler.error(
                message=f"创建接口失败: {str(e)}",
                errors={"detail": [str(e)]},
                code=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        """创建接口时验证项目权限"""
        project = serializer.validated_data.get('project')
        user = self.request.user

        # 检查用户是否有权限操作该项目
        if not user.is_superuser and not user.joined_projects.filter(id=project.id).exists():
            raise PermissionDenied("您没有权限在此项目中创建接口")

        serializer.save(created_by=user)

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='更新接口',
        operation_description='更新指定接口的全部信息',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'method', 'url', 'project'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='接口名称'),
                'method': openapi.Schema(type=openapi.TYPE_STRING, description='请求方法', enum=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='接口地址'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                'module': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属模块ID'),
                'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求头'),
                'params': openapi.Schema(type=openapi.TYPE_OBJECT, description='查询参数'),
                'body': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求体'),
                'setup_hooks': openapi.Schema(type=openapi.TYPE_ARRAY, description='前置钩子', items=openapi.Schema(type=openapi.TYPE_STRING)),
                'teardown_hooks': openapi.Schema(type=openapi.TYPE_ARRAY, description='后置钩子', items=openapi.Schema(type=openapi.TYPE_STRING)),
                'variables': openapi.Schema(type=openapi.TYPE_OBJECT, description='变量定义'),
                'validators': openapi.Schema(type=openapi.TYPE_ARRAY, description='断言规则', items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                'extract': openapi.Schema(type=openapi.TYPE_OBJECT, description='提取变量')
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的接口信息')
                }
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """更新接口"""
        self.log_request(request, '更新接口请求')
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            logger.info(f'更新接口成功 - id: {instance.id}, name: {instance.name}')
            return ResponseHandler.success(
                data=serializer.data,
                message="更新接口成功",
                code=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            # 处理验证错误
            errors = e.detail

            # 检查是否有唯一性约束错误 - 检查name字段
            if 'name' in errors and any('已存在' in str(error) for error in errors['name']):
                # 提取项目ID和接口名称
                project_id = request.data.get('project', instance.project_id)
                interface_name = request.data.get('name')

                logger.warning(f'更新接口失败 - 名称冲突: {interface_name}, 项目ID: {project_id}, 接口ID: {instance.id}')

                # 错误信息已经由序列化器提供，直接返回
                return ResponseHandler.error(
                    message="更新失败：接口名称已存在",
                    errors=errors,
                    code=status.HTTP_400_BAD_REQUEST
                )

            # 检查是否有唯一性约束错误 - 检查non_field_errors字段
            if 'non_field_errors' in errors and any('唯一' in str(error) or '必须能构成唯一集合' in str(error) for error in errors['non_field_errors']):
                # 提取项目ID和接口名称
                project_id = request.data.get('project', instance.project_id)
                interface_name = request.data.get('name', instance.name)

                # 构建更友好的错误信息
                error_message = f"更新失败：项目中已存在名为 '{interface_name}' 的接口，请使用其他名称"
                logger.warning(f'更新接口失败 - 名称冲突: {interface_name}, 项目ID: {project_id}, 接口ID: {instance.id}')

                return ResponseHandler.error(
                    message=error_message,
                    errors={"name": [f"项目中已存在名为 '{interface_name}' 的接口，请使用其他名称"]},
                    code=status.HTTP_400_BAD_REQUEST
                )

            # 其他验证错误
            logger.warning(f'更新接口失败 - 验证错误: {errors}, 接口ID: {instance.id}')
            return ResponseHandler.error(
                message="更新接口失败，请检查输入",
                errors=errors,
                code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            # 处理其他异常
            logger.error(f'更新接口失败 - 异常: {str(e)}, 接口ID: {instance.id}')
            return ResponseHandler.error(
                message=f"更新接口失败: {str(e)}",
                errors={"detail": [str(e)]},
                code=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='部分更新接口',
        operation_description='部分更新指定接口的信息',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='接口名称'),
                'method': openapi.Schema(type=openapi.TYPE_STRING, description='请求方法', enum=['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
                'url': openapi.Schema(type=openapi.TYPE_STRING, description='接口地址'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                'module': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属模块ID'),
                'headers': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求头'),
                'params': openapi.Schema(type=openapi.TYPE_OBJECT, description='查询参数'),
                'body': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求体'),
                'setup_hooks': openapi.Schema(type=openapi.TYPE_ARRAY, description='前置钩子', items=openapi.Schema(type=openapi.TYPE_STRING)),
                'teardown_hooks': openapi.Schema(type=openapi.TYPE_ARRAY, description='后置钩子', items=openapi.Schema(type=openapi.TYPE_STRING)),
                'variables': openapi.Schema(type=openapi.TYPE_OBJECT, description='变量定义'),
                'validators': openapi.Schema(type=openapi.TYPE_ARRAY, description='断言规则', items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                'extract': openapi.Schema(type=openapi.TYPE_OBJECT, description='提取变量')
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的接口信息')
                }
            )
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """部分更新接口"""
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['接口管理/接口'],
        operation_summary='删除接口',
        operation_description='删除指定的接口',
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息')
                }
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        """删除接口"""
        return super().destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        """更新接口时验证项目权限"""
        project = serializer.validated_data.get('project')
        user = self.request.user

        # 检查用户是否有权限操作该项目
        if project and not user.is_superuser and not user.joined_projects.filter(id=project.id).exists():
            raise PermissionDenied("您没有权限修改此项目的接口")

        serializer.save()

    def perform_destroy(self, instance):
        """删除接口时验证项目权限"""
        user = self.request.user

        # 检查用户是否有权限操作该项目
        if not user.is_superuser and not user.joined_projects.filter(id=instance.project_id).exists():
            raise PermissionDenied("您没有权限删除此项目的接口")

        instance.delete()

    @action(detail=True, methods=['GET'])
    def referenced_testcases(self, request, pk=None):
        """获取引用了该接口的测试用例列表"""
        interface = self.get_object()

        # 获取所有引用了该接口的测试步骤
        steps = TestCaseStep.objects.filter(
            origin_interface=interface
        ).select_related('testcase')

        # 按用例分组，避免重复
        testcases = {}
        for step in steps:
            if step.testcase_id not in testcases:
                testcases[step.testcase_id] = {
                    'testcase': step.testcase,
                    'steps': []
                }
            testcases[step.testcase_id]['steps'].append(step)

        # 构建响应数据
        data = []
        for testcase_info in testcases.values():
            testcase = testcase_info['testcase']
            steps = testcase_info['steps']
            data.append({
                'id': testcase.id,
                'name': testcase.name,
                'steps': [{
                    'id': step.id,
                    'name': step.name,
                    'order': step.order,
                    'sync_fields': step.sync_fields,
                    'last_sync_time': step.last_sync_time
                } for step in steps]
            })

        return Response({
            'status': 'success',
            'code': 200,
            'message': '获取引用接口的用例列表成功',
            'data': data
        })

class InterfaceResultViewSet(viewsets.ReadOnlyModelViewSet, BaseAPIView):
    """接口执行结果视图集"""
    queryset = InterfaceResult.objects.all()
    serializer_class = InterfaceResultSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """获取当前用户有权限的接口执行结果"""
        # 处理swagger文档生成的情况
        if getattr(self, 'swagger_fake_view', False):
            return InterfaceResult.objects.none()

        user = self.request.user
        if user.is_superuser:
            queryset = InterfaceResult.objects.all()
        else:
            # 获取用户所属的项目ID列表
            project_ids = user.joined_projects.values_list('id', flat=True)
            queryset = InterfaceResult.objects.filter(interface__project_id__in=project_ids)

        # 按接口和环境过滤
        interface_id = self.request.query_params.get('interface_id')
        environment_id = self.request.query_params.get('environment_id')

        if interface_id:
            queryset = queryset.filter(interface_id=interface_id)
        if environment_id:
            queryset = queryset.filter(environment_id=environment_id)

        return queryset

    @swagger_auto_schema(
        tags=['接口管理/执行结果'],
        operation_summary='获取测试结果列表',
        operation_description='获取当前用户有权限的接口执行结果列表，支持分页、按接口和环境过滤',
        manual_parameters=[
            openapi.Parameter(
                'interface_id',
                openapi.IN_QUERY,
                description='接口ID',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'environment_id',
                openapi.IN_QUERY,
                description='环境ID',
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='总数'),
                            'next': openapi.Schema(type=openapi.TYPE_STRING, description='下一页'),
                            'previous': openapi.Schema(type=openapi.TYPE_STRING, description='上一页'),
                            'results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_OBJECT)
                            )
                        }
                    )
                }
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """获取测试结果列表"""
        self.log_request(request, '获取测试结果列表请求')
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response_data = {
                'count': self.paginator.page.paginator.count,
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
                'results': serializer.data
            }
            logger.info(f'获取测试结果列表成功 - page: {request.GET.get("page", 1)}, page_size: {request.GET.get("page_size", 10)}')
            return ResponseHandler.success(
                data=response_data,
                message="获取测试结果列表成功"
            )
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success(
            data={'results': serializer.data},
            message="获取测试结果列表成功"
        )

    @swagger_auto_schema(
        tags=['接口管理/执行结果'],
        operation_summary='获取测试结果详情',
        operation_description='获取指定的接口执行结果详细信息',
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='执行状态'),
                            'elapsed': openapi.Schema(type=openapi.TYPE_NUMBER, description='响应时间(ms)'),
                            'request': openapi.Schema(type=openapi.TYPE_OBJECT, description='请求信息'),
                            'response': openapi.Schema(type=openapi.TYPE_OBJECT, description='响应信息'),
                            'validation_results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                description='断言结果',
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'check': openapi.Schema(type=openapi.TYPE_STRING, description='检查项'),
                                        'expect': openapi.Schema(type=openapi.TYPE_STRING, description='期望值'),
                                        'actual': openapi.Schema(type=openapi.TYPE_STRING, description='实际值'),
                                        'result': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='验证结果')
                                    }
                                )
                            ),
                            'extracted_variables': openapi.Schema(type=openapi.TYPE_OBJECT, description='提取的变量')
                        }
                    )
                }
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取测试结果详情"""
        self.log_request(request, '获取测试结果详情请求')
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        logger.info(f'获取测试结果详情成功 - id: {instance.id}')
        return ResponseHandler.success(
            data=serializer.data,
            message="获取测试结果详情成功"
        )
