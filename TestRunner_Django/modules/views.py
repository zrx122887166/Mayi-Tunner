from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Module
from .serializers import ModuleSerializer, ModuleCreateSerializer, ModuleUpdateSerializer
from utils.response import APIResponse
from TestRunner.pagination import CustomPagination
import logging

logger = logging.getLogger('testrunner')

class ModuleViewSet(viewsets.ModelViewSet):
    """模块管理视图集"""
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        """根据不同的操作选择不同的序列化器"""
        if self.action == 'create':
            return ModuleCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ModuleUpdateSerializer
        return ModuleSerializer

    def get_queryset(self):
        """获取当前用户有权限的模块列表"""
        # 处理swagger文档生成的情况
        if getattr(self, 'swagger_fake_view', False):
            return Module.objects.none()
            
        user = self.request.user
        if user.is_superuser:
            queryset = Module.objects.all()
        else:
            # 获取用户所属的项目ID列表
            project_ids = user.joined_projects.values_list('id', flat=True)
            queryset = Module.objects.filter(project_id__in=project_ids)
        
        # 按项目过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
            
        # 只在列表请求时过滤顶级模块
        if self.action == 'list':
            queryset = queryset.filter(parent=None)
            
        return queryset

    @swagger_auto_schema(
        tags=['模块管理'],
        operation_summary='获取模块列表',
        operation_description='获取当前用户可访问的所有模块列表，支持分页和按项目过滤',
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description='页码，从1开始',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description='每页显示数量，默认10，最大100',
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'project_id',
                openapi.IN_QUERY,
                description='项目ID，用于过滤特定项目的模块',
                type=openapi.TYPE_INTEGER,
                required=False
            ),
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
                            'count': openapi.Schema(type=openapi.TYPE_INTEGER, description='总记录数'),
                            'next': openapi.Schema(type=openapi.TYPE_STRING, description='下一页URL', nullable=True),
                            'previous': openapi.Schema(type=openapi.TYPE_STRING, description='上一页URL', nullable=True),
                            'results': openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='模块ID'),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='模块名称'),
                                        'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                                        'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description='父模块ID', nullable=True),
                                        'description': openapi.Schema(type=openapi.TYPE_STRING, description='模块描述'),
                                        'children': openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            description='子模块列表',
                                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                                        ),
                                        'create_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                                        'update_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
                                    }
                                )
                            )
                        }
                    )
                }
            )
        }
    )
    def list(self, request, *args, **kwargs):
        """获取模块列表"""
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
            return APIResponse(
                data=response_data,
                message="获取模块列表成功"
            )
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(
            data={'results': serializer.data},
            message="获取模块列表成功"
        )

    @swagger_auto_schema(
        tags=['模块管理'],
        operation_summary='创建模块',
        operation_description='创建新的模块',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'project'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='模块名称'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description='父模块ID', nullable=True),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='模块描述', nullable=True)
            }
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='模块ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='模块名称'),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                            'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description='父模块ID', nullable=True),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='模块描述'),
                            'create_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                            'update_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
                        }
                    )
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """创建模块"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return APIResponse(
            data=serializer.data,
            message="创建模块成功",
            code=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=['模块管理'],
        operation_summary='更新模块',
        operation_description='更新指定模块的名称和描述信息',
        request_body=ModuleUpdateSerializer,
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='模块ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='模块名称'),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                            'parent': openapi.Schema(type=openapi.TYPE_INTEGER, description='父模块ID', nullable=True),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='模块描述'),
                            'create_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                            'update_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
                        }
                    )
                }
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='错误信息'),
                    'errors': openapi.Schema(type=openapi.TYPE_OBJECT, description='错误详情')
                }
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """更新模块"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # 重新获取完整的模块数据
        response_serializer = ModuleSerializer(instance)
        return APIResponse(
            data=response_serializer.data,
            message="更新模块成功"
        )

    @swagger_auto_schema(
        tags=['模块管理'],
        operation_summary='删除模块',
        operation_description='删除指定的模块，如果模块包含子模块则无法删除',
        responses={
            status.HTTP_204_NO_CONTENT: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        """删除模块"""
        instance = self.get_object()
        if instance.children.exists():
            return APIResponse(
                status='error',
                code=status.HTTP_400_BAD_REQUEST,
                message='该模块包含子模块，无法删除'
            )
        self.perform_destroy(instance)
        return APIResponse(
            message="删除模块成功",
            code=status.HTTP_204_NO_CONTENT
        )

    @swagger_auto_schema(
        tags=['模块管理'],
        operation_summary='搜索模块',
        operation_description='根据关键字搜索模块',
        manual_parameters=[
            openapi.Parameter(
                'keyword',
                openapi.IN_QUERY,
                description='搜索关键字',
                type=openapi.TYPE_STRING,
                required=False
            ),
            openapi.Parameter(
                'project',
                openapi.IN_QUERY,
                description='项目ID',
                type=openapi.TYPE_INTEGER,
                required=True
            ),
        ],
        responses={
            status.HTTP_200_OK: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='提示信息'),
                    'data': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='模块ID'),
                                'name': openapi.Schema(type=openapi.TYPE_STRING, description='模块名称'),
                                'description': openapi.Schema(type=openapi.TYPE_STRING, description='模块描述')
                            }
                        )
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索模块"""
        keyword = request.query_params.get('keyword', '')
        project_id = request.query_params.get('project')
        
        if not project_id:
            return APIResponse(
                status='error',
                code=status.HTTP_400_BAD_REQUEST,
                message='请指定项目ID'
            )
            
        queryset = Module.objects.filter(
            Q(name__icontains=keyword) | Q(description__icontains=keyword),
            project_id=project_id
        )
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse(
            message='搜索成功',
            data=serializer.data
        )
