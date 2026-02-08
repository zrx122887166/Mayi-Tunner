from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

from .models import Environment, EnvironmentVariable, GlobalRequestHeader
from .serializers import EnvironmentSerializer, EnvironmentVariableSerializer, GlobalRequestHeaderSerializer
from projects.models import Project
from projects.views import BaseAPIView
from projects.utils import ResponseHandler
from TestRunner.pagination import CustomPagination

logger = logging.getLogger('testrunner')

class EnvironmentViewSet(viewsets.ModelViewSet, BaseAPIView):
    """
    环境配置管理的API接口

    提供环境配置的增删改查功能：
    - GET /environments/environments/ 获取环境列表
    - POST /environments/environments/ 创建新环境
    - GET /environments/environments/{id}/ 获取环境详情
    - PUT /environments/environments/{id}/ 更新环境配置
    - DELETE /environments/environments/{id}/ 删除环境
    - POST /environments/environments/{id}/clone/ 克隆环境
    """
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        """根据项目ID过滤环境列表"""
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='获取环境列表',
        operation_description='获取当前用户可访问的所有环境列表，用于在运行测试时选择运行环境。支持按项目过滤，分页展示。',
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description='项目ID，用于过滤指定项目的环境列表',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='页码，从1开始',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description='每页显示数量，默认10，最大100',
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='请求成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='总记录数'),
                                'next': openapi.Schema(type=openapi.TYPE_STRING, description='下一页链接'),
                                'previous': openapi.Schema(type=openapi.TYPE_STRING, description='上一页链接'),
                                'results': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='环境ID'),
                                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='环境名称'),
                                            'base_url': openapi.Schema(type=openapi.TYPE_STRING, description='基础URL，测试接口时会自动添加到URL前面'),
                                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='环境描述'),
                                            'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                                            'project_name': openapi.Schema(type=openapi.TYPE_STRING, description='所属项目名称'),
                                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否激活，只有激活的环境才能被选择运行测试'),
                                            'created_by': openapi.Schema(type=openapi.TYPE_INTEGER, description='创建人ID'),
                                            'created_by_name': openapi.Schema(type=openapi.TYPE_STRING, description='创建人名称'),
                                            'created_time': openapi.Schema(type=openapi.TYPE_STRING, description='创建时间'),
                                            'updated_time': openapi.Schema(type=openapi.TYPE_STRING, description='更新时间'),
                                            'variables': openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                description='环境变量列表，运行测试时会自动注入这些变量',
                                                items=openapi.Schema(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='变量ID'),
                                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名'),
                                                        'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                                                        'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型：string/integer/float/boolean/json'),
                                                        'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述'),
                                                        'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据，如果是则在返回时会隐藏value值')
                                                    }
                                                )
                                            )
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """获取环境列表"""
        self.log_request(request, '获取环境列表请求')
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
            return ResponseHandler.success(
                data=response_data,
                message="获取环境列表成功"
            )
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success(
            data={'results': serializer.data},
            message="获取环境列表成功"
        )

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='创建环境',
        operation_description='创建新的环境配置，用于在运行测试时提供基础URL和环境变量。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'base_url', 'project'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='环境名称，如：开发环境、测试环境、预发环境等'),
                'base_url': openapi.Schema(type=openapi.TYPE_STRING, description='基础URL，如：http://api.dev.example.com，测试接口时会自动添加到URL前面'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='环境描述，可以描述环境的用途、注意事项等'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID，环境必须属于某个项目'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否激活，默认为true。只有激活的环境才能被选择运行测试'),
                'database_config': openapi.Schema(type=openapi.TYPE_INTEGER, description='数据库配置ID，关联到数据库配置，必须与环境属于同一个项目')
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='创建成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：201'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='创建的环境信息')
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description='参数错误',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：error'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：400'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='错误信息'),
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description='错误详情')
                    }
                )
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """创建环境"""
        self.log_request(request, '创建环境请求')
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f'创建环境失败：数据验证错误 - errors: {serializer.errors}')
            return ResponseHandler.error(
                message="环境创建失败",
                errors=serializer.errors
            )
        self.perform_create(serializer)
        logger.info(f'环境创建成功 - name: {serializer.data.get("name")}, creator: {request.user.username}')
        return ResponseHandler.success(
            data=serializer.data,
            message="环境创建成功",
            code=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='克隆环境',
        operation_description='克隆现有环境及其变量。通过克隆功能，可以快速创建一个与现有环境配置相同的新环境，包括所有环境变量。新环境的名称会自动添加"_copy"后缀。可以指定目标项目ID来克隆到其他项目。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'project_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='目标项目ID，如果不提供则使用源环境的项目ID'
                ),
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='新环境的名称，如果不提供则自动添加"_copy"后缀'
                )
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='克隆成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：201'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='克隆后的环境信息')
                    }
                )
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description='参数错误',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：error'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：400'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='错误信息'),
                        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description='错误详情')
                    }
                )
            )
        }
    )
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """克隆环境配置及其变量"""
        environment = self.get_object()
        project_id = request.data.get('project_id')
        name = request.data.get('name')

        try:
            with transaction.atomic():
                # 确定目标项目
                if project_id:
                    try:
                        project = Project.objects.get(id=project_id)
                    except Project.DoesNotExist:
                        return ResponseHandler.error(
                            message="目标项目不存在",
                            code=status.HTTP_400_BAD_REQUEST
                        )
                else:
                    project = environment.project

                # 确定新环境名称
                if not name:
                    name = f"{environment.name}_copy"

                # 检查名称在目标项目中是否已存在
                if Environment.objects.filter(project=project, name=name).exists():
                    return ResponseHandler.error(
                        message="目标项目中已存在同名环境",
                        code=status.HTTP_400_BAD_REQUEST
                    )

                # 克隆环境
                new_env = Environment.objects.create(
                    name=name,
                    base_url=environment.base_url,
                    verify_ssl=environment.verify_ssl,
                    description=environment.description,
                    project=project,
                    created_by=request.user
                )
                
                # 克隆环境变量
                variables = environment.variables.all()
                for var in variables:
                    EnvironmentVariable.objects.create(
                        environment=new_env,
                        name=var.name,
                        value=var.value,
                        type=var.type,
                        description=var.description,
                        is_sensitive=var.is_sensitive
                    )
            
            serializer = self.get_serializer(new_env)
            return ResponseHandler.success(
                data=serializer.data,
                message="环境克隆成功",
                code=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f'环境克隆失败 - error: {str(e)}')
            return ResponseHandler.error(
                message="环境克隆失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='更新环境',
        operation_description='更新指定环境的配置信息',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='环境名称，如：开发环境、测试环境、预发环境等'),
                'base_url': openapi.Schema(type=openapi.TYPE_STRING, description='基础URL，如：http://api.dev.example.com，测试接口时会自动添加到URL前面'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='环境描述，可以描述环境的用途、注意事项等'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID，环境必须属于某个项目'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否激活，只有激活的环境才能被选择运行测试'),
                'database_config': openapi.Schema(type=openapi.TYPE_INTEGER, description='数据库配置ID，关联到数据库配置，必须与环境属于同一个项目')
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='更新成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的环境信息')
                    }
                )
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """更新环境"""
        self.log_request(request, '更新环境请求')
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            logger.warning(f'更新环境失败：数据验证错误 - errors: {serializer.errors}')
            return ResponseHandler.error(
                message="环境更新失败",
                errors=serializer.errors
            )
        self.perform_update(serializer)
        logger.info(f'环境更新成功 - id: {instance.id}, name: {serializer.data.get("name")}')
        return ResponseHandler.success(
            data=serializer.data,
            message="环境更新成功"
        )

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='删除环境',
        operation_description='删除指定的环境配置，同时会删除该环境下的所有环境变量',
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(
                description='删除成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：204'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='空对象')
                    }
                )
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        """删除环境"""
        self.log_request(request, '删除环境请求')
        try:
            instance = self.get_object()
            instance_id = instance.id
            instance_name = instance.name
            self.perform_destroy(instance)
            logger.info(f'环境删除成功 - id: {instance_id}, name: {instance_name}')
            return ResponseHandler.success(
                message="环境删除成功",
                code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f'环境删除失败 - error: {str(e)}')
            return ResponseHandler.error(
                message="环境删除失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='部分更新环境',
        operation_description='部分更新环境配置信息，只更新提供的字段',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='环境名称，如：开发环境、测试环境、预发环境等'),
                'base_url': openapi.Schema(type=openapi.TYPE_STRING, description='基础URL，如：http://api.dev.example.com，测试接口时会自动添加到URL前面'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='环境描述，可以描述环境的用途、注意事项等'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID，环境必须属于某个项目'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否激活，只有激活的环境才能被选择运行测试'),
                'database_config': openapi.Schema(type=openapi.TYPE_INTEGER, description='数据库配置ID，关联到数据库配置，必须与环境属于同一个项目')
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='更新成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的环境信息')
                    }
                )
            )
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """部分更新环境"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        tags=['环境管理'],
        operation_summary='获取环境详情',
        operation_description='获取指定ID的环境配置详情，包括环境变量等信息',
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='请求成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='环境配置详情')
                    }
                )
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取环境详情"""
        self.log_request(request, '获取环境详情请求')
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return ResponseHandler.success(
                data=serializer.data,
                message="获取环境详情成功"
            )
        except Exception as e:
            logger.error(f'获取环境详情失败 - error: {str(e)}')
            return ResponseHandler.error(
                message="获取环境详情失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EnvironmentVariableViewSet(viewsets.ModelViewSet, BaseAPIView):
    """
    环境变量管理的API接口

    提供环境变量的增删改查功能：
    - GET /environments/variables/ 获取变量列表
    - POST /environments/variables/ 创建新变量
    - GET /environments/variables/{id}/ 获取变量详情
    - PUT /environments/variables/{id}/ 更新变量
    - DELETE /environments/variables/{id}/ 删除变量
    - POST /environments/variables/batch_create/ 批量创建变量
    - POST /environments/variables/batch_update/ 批量更新变量
    """
    queryset = EnvironmentVariable.objects.all()
    serializer_class = EnvironmentVariableSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        """根据环境ID过滤变量列表"""
        queryset = super().get_queryset()
        environment_id = self.request.query_params.get('environment_id')
        if environment_id:
            queryset = queryset.filter(environment_id=environment_id)
        return queryset

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='批量创建环境变量',
        operation_description='批量创建环境变量。环境变量用于在运行测试时提供动态参数，比如认证信息、服务地址等。支持多种数据类型，可以标记敏感数据。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['environment_id', 'variables'],
            properties={
                'environment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='环境ID，指定要添加变量的环境'),
                'variables': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='要创建的环境变量列表',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['name', 'value'],
                        properties={
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名，如：API_KEY、DATABASE_URL等'),
                            'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                            'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型：string(字符串)/integer(整数)/float(浮点数)/boolean(布尔值)/json(JSON对象)'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述，说明变量的用途'),
                            'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据，如果是则在返回时会隐藏value值，适用于密码、token等敏感信息')
                        }
                    )
                )
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='创建成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：201'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description='创建的环境变量列表',
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='变量ID'),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名'),
                                    'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                                    'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型'),
                                    'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述'),
                                    'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据')
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建环境变量"""
        environment_id = request.data.get('environment_id')
        variables_data = request.data.get('variables', [])
        
        if not environment_id or not variables_data:
            return ResponseHandler.error(
                message="缺少必要参数",
                code=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            environment = Environment.objects.get(id=environment_id)
        except Environment.DoesNotExist:
            return ResponseHandler.error(
                message="指定的环境不存在",
                code=status.HTTP_404_NOT_FOUND
            )
        
        created_variables = []
        errors = []
        
        with transaction.atomic():
            for variable_data in variables_data:
                variable_data['environment'] = environment_id
                serializer = self.get_serializer(data=variable_data)
                try:
                    serializer.is_valid(raise_exception=True)
                    variable = serializer.save()
                    created_variables.append(variable)
                except Exception as e:
                    errors.append({
                        'name': variable_data.get('name', '未知'),
                        'error': str(e)
                    })
                    raise  # 回滚事务
        
        if errors:
            return ResponseHandler.error(
                message="部分或全部环境变量创建失败",
                errors=errors,
                code=status.HTTP_400_BAD_REQUEST
            )
        
        response_serializer = self.get_serializer(created_variables, many=True)
        return ResponseHandler.success(
            data=response_serializer.data,
            message="批量创建环境变量成功",
            code=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='批量更新环境变量',
        operation_description='批量更新环境变量。可以同时更新多个环境变量的值、类型、描述等信息。对于敏感数据，可以通过is_sensitive标记来保护。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['variables'],
            properties={
                'variables': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description='要更新的环境变量列表',
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['id'],
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='变量ID，用于定位要更新的变量'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='新的变量名'),
                            'value': openapi.Schema(type=openapi.TYPE_STRING, description='新的变量值'),
                            'type': openapi.Schema(type=openapi.TYPE_STRING, description='新的变量类型：string(字符串)/integer(整数)/float(浮点数)/boolean(布尔值)/json(JSON对象)'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='新的变量描述'),
                            'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据，如果是则在返回时会隐藏value值')
                        }
                    )
                )
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='更新成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description='更新后的环境变量列表',
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='变量ID'),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名'),
                                    'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                                    'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型'),
                                    'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述'),
                                    'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据')
                                }
                            )
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """批量更新环境变量"""
        variables_data = request.data.get('variables', [])
        if not variables_data:
            return ResponseHandler.error(
                message="缺少变量数据",
                code=status.HTTP_400_BAD_REQUEST
            )
            
        updated_variables = []
        with transaction.atomic():
            for variable_data in variables_data:
                variable_id = variable_data.pop('id', None)
                if not variable_id:
                    continue
                    
                variable = get_object_or_404(EnvironmentVariable, id=variable_id)
                serializer = self.get_serializer(
                    variable,
                    data=variable_data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                updated_variable = serializer.save()
                updated_variables.append(updated_variable)
        
        response_serializer = self.get_serializer(updated_variables, many=True)
        return ResponseHandler.success(
            data=response_serializer.data,
            message="批量更新环境变量成功"
        )

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='获取环境变量列表',
        operation_description='获取指定环境下的所有环境变量列表。支持分页展示。',
        manual_parameters=[
            openapi.Parameter(
                'environment_id',
                openapi.IN_QUERY,
                description='环境ID，用于过滤指定环境的变量列表',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='页码，从1开始',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description='每页显示数量，默认10，最大100',
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='请求成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='总记录数'),
                                'next': openapi.Schema(type=openapi.TYPE_STRING, description='下一页链接'),
                                'previous': openapi.Schema(type=openapi.TYPE_STRING, description='上一页链接'),
                                'results': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='变量ID'),
                                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名'),
                                            'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                                            'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型：string/integer/float/boolean/json'),
                                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述'),
                                            'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据，如果是则在返回时会隐藏value值')
                                        }
                                    )
                                )
                            }
                        )
                    }
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """获取环境变量列表"""
        self.log_request(request, '获取环境变量列表请求')
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
            return ResponseHandler.success(
                data=response_data,
                message="获取环境变量列表成功"
            )
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success(
            data={'results': serializer.data},
            message="获取环境变量列表成功"
        )

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='创建环境变量',
        operation_description='创建单个环境变量。如果需要批量创建，请使用 batch_create 接口。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['environment', 'name', 'value'],
            properties={
                'environment': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属环境ID'),
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名，如：API_KEY、DATABASE_URL等'),
                'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型：string(字符串)/integer(整数)/float(浮点数)/boolean(布尔值)/json(JSON对象)'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述，说明变量的用途'),
                'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据，如果是则在返回时会隐藏value值')
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='创建成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：201'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='创建的环境变量信息')
                    }
                )
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """创建环境变量"""
        self.log_request(request, '创建环境变量请求')
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f'创建环境变量失败：数据验证错误 - errors: {serializer.errors}')
            return ResponseHandler.error(
                message="环境变量创建失败",
                errors=serializer.errors
            )
        self.perform_create(serializer)
        logger.info(f'环境变量创建成功 - name: {serializer.data.get("name")}')
        return ResponseHandler.success(
            data=serializer.data,
            message="环境变量创建成功",
            code=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='获取环境变量详情',
        operation_description='获取单个环境变量的详细信息',
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='请求成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='变量ID'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名'),
                                'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                                'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型'),
                                'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述'),
                                'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据')
                            }
                        )
                    }
                )
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取环境变量详情"""
        self.log_request(request, '获取环境变量详情请求')
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponseHandler.success(
            data=serializer.data,
            message="获取环境变量详情成功"
        )

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='更新环境变量',
        operation_description='更新单个环境变量的信息。如果需要批量更新，请使用 batch_update 接口。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='变量名'),
                'value': openapi.Schema(type=openapi.TYPE_STRING, description='变量值'),
                'type': openapi.Schema(type=openapi.TYPE_STRING, description='变量类型：string(字符串)/integer(整数)/float(浮点数)/boolean(布尔值)/json(JSON对象)'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='变量描述'),
                'is_sensitive': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否敏感数据')
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='更新成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的环境变量信息')
                    }
                )
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """更新环境变量"""
        self.log_request(request, '更新环境变量请求')
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            logger.warning(f'更新环境变量失败：数据验证错误 - errors: {serializer.errors}')
            return ResponseHandler.error(
                message="环境变量更新失败",
                errors=serializer.errors
            )
        self.perform_update(serializer)
        logger.info(f'环境变量更新成功 - id: {instance.id}, name: {serializer.data.get("name")}')
        return ResponseHandler.success(
            data=serializer.data,
            message="环境变量更新成功"
        )

    @swagger_auto_schema(
        tags=['环境变量'],
        operation_summary='删除环境变量',
        operation_description='删除单个环境变量',
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(
                description='删除成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：204'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='空对象')
                    }
                )
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        """删除环境变量"""
        self.log_request(request, '删除环境变量请求')
        try:
            instance = self.get_object()
            instance_id = instance.id
            instance_name = instance.name
            self.perform_destroy(instance)
            logger.info(f'环境变量删除成功 - id: {instance_id}, name: {instance_name}')
            return ResponseHandler.success(
                message="环境变量删除成功",
                code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f'环境变量删除失败 - error: {str(e)}')
            return ResponseHandler.error(
                message="环境变量删除失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class GlobalRequestHeaderViewSet(viewsets.ModelViewSet, BaseAPIView):
    """全局请求头参数管理的API接口"""
    queryset = GlobalRequestHeader.objects.all()
    serializer_class = GlobalRequestHeaderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_queryset(self):
        """根据项目ID过滤参数列表"""
        queryset = super().get_queryset()
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
    
    @swagger_auto_schema(
        tags=['环境管理/全局请求头'],
        operation_summary='获取全局请求头列表',
        operation_description='获取项目下的全局请求头参数列表，这些请求头会自动添加到该项目下所有接口的请求中',
        manual_parameters=[
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description='项目ID，用于过滤指定项目的全局请求头',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='页码，从1开始',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description='每页显示数量，默认10，最大100',
                type=openapi.TYPE_INTEGER,
                required=False
            )
        ],
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='请求成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='全局请求头列表')
                    }
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """获取全局请求头列表"""
        self.log_request(request, '获取全局请求头列表请求')
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
            return ResponseHandler.success(
                data=response_data,
                message="获取全局请求头列表成功"
            )
        serializer = self.get_serializer(queryset, many=True)
        return ResponseHandler.success(
            data={'results': serializer.data},
            message="获取全局请求头列表成功"
        )
        
    @swagger_auto_schema(
        tags=['环境管理/全局请求头'],
        operation_summary='创建全局请求头',
        operation_description='创建新的全局请求头参数，创建后会自动添加到该项目下所有接口的请求中。支持使用$变量或${变量}格式引用环境变量。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'value', 'project'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='请求头名称，如：Content-Type, Authorization等'),
                'value': openapi.Schema(type=openapi.TYPE_STRING, description='请求头值，如：application/json, Bearer token等。支持使用$变量或${变量}引用环境变量'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='请求头描述，说明用途'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID，请求头只会应用于该项目下的接口'),
                'is_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用，默认为true。只有启用的才会生效')
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description='创建成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：201'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='创建的全局请求头信息')
                    }
                )
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """创建全局请求头"""
        self.log_request(request, '创建全局请求头请求')
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f'创建全局请求头失败：数据验证错误 - errors: {serializer.errors}')
            return ResponseHandler.error(
                message="全局请求头创建失败",
                errors=serializer.errors
            )
        self.perform_create(serializer)
        logger.info(f'全局请求头创建成功 - name: {serializer.data.get("name")}, creator: {request.user.username}')
        return ResponseHandler.success(
            data=serializer.data,
            message="全局请求头创建成功",
            code=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        tags=['环境管理/全局请求头'],
        operation_summary='获取全局请求头详情',
        operation_description='获取指定ID的全局请求头详情',
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='请求成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='全局请求头详情')
                    }
                )
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取全局请求头详情"""
        self.log_request(request, '获取全局请求头详情请求')
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return ResponseHandler.success(
            data=serializer.data,
            message="获取全局请求头详情成功"
        )
        
    @swagger_auto_schema(
        tags=['环境管理/全局请求头'],
        operation_summary='更新全局请求头',
        operation_description='更新指定ID的全局请求头信息。支持使用$变量或${变量}格式引用环境变量。',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='请求头名称'),
                'value': openapi.Schema(type=openapi.TYPE_STRING, description='请求头值，支持使用$变量或${变量}引用环境变量'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='请求头描述'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                'is_enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用')
            }
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='更新成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的全局请求头信息')
                    }
                )
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """更新全局请求头"""
        self.log_request(request, '更新全局请求头请求')
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            logger.warning(f'更新全局请求头失败：数据验证错误 - errors: {serializer.errors}')
            return ResponseHandler.error(
                message="全局请求头更新失败",
                errors=serializer.errors
            )
        self.perform_update(serializer)
        logger.info(f'全局请求头更新成功 - id: {instance.id}, name: {serializer.data.get("name")}')
        return ResponseHandler.success(
            data=serializer.data,
            message="全局请求头更新成功"
        )
        
    @swagger_auto_schema(
        tags=['环境管理/全局请求头'],
        operation_summary='部分更新全局请求头',
        operation_description='部分更新指定ID的全局请求头信息',
        responses={
            status.HTTP_200_OK: openapi.Response(
                description='更新成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：200'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='更新后的全局请求头信息')
                    }
                )
            )
        }
    )
    def partial_update(self, request, *args, **kwargs):
        """部分更新全局请求头"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
        
    @swagger_auto_schema(
        tags=['环境管理/全局请求头'],
        operation_summary='删除全局请求头',
        operation_description='删除指定ID的全局请求头',
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Response(
                description='删除成功',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态：success'),
                        'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码：204'),
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT, description='空对象')
                    }
                )
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        """删除全局请求头"""
        self.log_request(request, '删除全局请求头请求')
        try:
            instance = self.get_object()
            instance_id = instance.id
            instance_name = instance.name
            self.perform_destroy(instance)
            logger.info(f'全局请求头删除成功 - id: {instance_id}, name: {instance_name}')
            return ResponseHandler.success(
                message="全局请求头删除成功",
                code=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            logger.error(f'全局请求头删除失败 - error: {str(e)}')
            return ResponseHandler.error(
                message="全局请求头删除失败",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
