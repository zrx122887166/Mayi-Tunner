import os
import tempfile
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import CustomFunction
from .serializers import CustomFunctionSerializer
from TestRunner.pagination import CustomPagination
import logging

logger = logging.getLogger('testrunner')

class CustomFunctionViewSet(viewsets.ModelViewSet):
    """自定义函数视图集"""
    queryset = CustomFunction.objects.all()
    serializer_class = CustomFunctionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='获取函数列表',
        operation_description='获取当前用户可访问的所有自定义函数列表，支持分页和按项目过滤',
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
                description='项目ID，用于过滤特定项目的函数',
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
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='函数ID'),
                                        'name': openapi.Schema(type=openapi.TYPE_STRING, description='函数名称'),
                                        'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                                        'description': openapi.Schema(type=openapi.TYPE_STRING, description='函数描述'),
                                        'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用'),
                                        'created_by': openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='用户ID'),
                                                'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名')
                                            }
                                        ),
                                        'created_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                                        'updated_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
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
        """获取函数列表"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': '获取函数列表成功',
                'data': {
                    'count': self.paginator.page.paginator.count,
                    'next': self.paginator.get_next_link(),
                    'previous': self.paginator.get_previous_link(),
                    'results': serializer.data
                }
            })
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': '获取函数列表成功',
            'data': {'results': serializer.data}
        })

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='创建函数',
        operation_description='创建新的自定义函数',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'code', 'project'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='函数名称'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='函数描述'),
                'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用，默认True')
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='函数ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='函数名称'),
                            'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='函数描述'),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用'),
                            'created_by': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='用户ID'),
                                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名')
                                }
                            ),
                            'created_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                            'updated_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
                        }
                    )
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        """创建函数"""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '创建函数失败',
                'data': {},
                'errors': serializer.errors
            })
        self.perform_create(serializer)
        return Response({
            'status': 'success',
            'code': status.HTTP_201_CREATED,
            'message': '创建函数成功',
            'data': serializer.data
        })

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='获取函数详情',
        operation_description='获取指定函数的详细信息',
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='函数ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='函数名称'),
                            'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='函数描述'),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用'),
                            'created_by': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='用户ID'),
                                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名')
                                }
                            ),
                            'created_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                            'updated_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
                        }
                    )
                }
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        """获取函数详情"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': '获取函数详情成功',
            'data': serializer.data
        })

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='更新函数',
        operation_description='更新指定函数的信息',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='函数名称'),
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='函数描述'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用')
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='函数ID'),
                            'name': openapi.Schema(type=openapi.TYPE_STRING, description='函数名称'),
                            'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                            'description': openapi.Schema(type=openapi.TYPE_STRING, description='函数描述'),
                            'project': openapi.Schema(type=openapi.TYPE_INTEGER, description='所属项目ID'),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否启用'),
                            'created_by': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='用户ID'),
                                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名')
                                }
                            ),
                            'created_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='创建时间'),
                            'updated_time': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', description='更新时间')
                        }
                    )
                }
            )
        }
    )
    def update(self, request, *args, **kwargs):
        """更新函数"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '更新函数失败',
                'data': {},
                'errors': serializer.errors
            })
        self.perform_update(serializer)
        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': '更新函数成功',
            'data': serializer.data
        })

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='删除函数',
        operation_description='删除指定的函数',
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
        """删除函数"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'status': 'success',
            'code': status.HTTP_204_NO_CONTENT,
            'message': '删除函数成功',
            'data': {}
        })

    def get_queryset(self):
        """获取当前用户有权限的函数列表"""
        # 处理swagger文档生成的情况
        if getattr(self, 'swagger_fake_view', False):
            return CustomFunction.objects.none()
            
        user = self.request.user
        if user.is_superuser:
            queryset = CustomFunction.objects.all()
        else:
            # 获取用户所属的项目ID列表
            project_ids = user.joined_projects.values_list('id', flat=True)
            queryset = CustomFunction.objects.filter(project_id__in=project_ids)

        # 按项目过滤
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset

    def perform_create(self, serializer):
        """创建时自动关联创建人"""
        serializer.save(created_by=self.request.user)

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='生成debugtalk.py',
        operation_description='根据项目的自定义函数生成debugtalk.py文件内容',
        manual_parameters=[
            openapi.Parameter(
                'project_id',
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
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'content': openapi.Schema(type=openapi.TYPE_STRING, description='文件内容')
                        }
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['get'])
    def generate_debugtalk(self, request):
        """生成debugtalk.py文件内容"""
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '请指定项目ID',
                'errors': {'project_id': ['该字段是必填项']}
            })

        # 获取项目下所有启用的自定义函数
        functions = CustomFunction.objects.filter(
            project_id=project_id,
            is_active=True
        ).order_by('name')

        # 生成文件内容
        content = [
            '"""',
            'This file is auto-generated by TestRunner.',
            'Please do not modify this file manually.',
            '"""',
            '',
            'import random',
            'import time',
            'import datetime',
            'import hashlib',
            'import json',
            '',
        ]

        # 添加每个自定义函数
        for func in functions:
            # 添加函数注释
            if func.description:
                content.extend([
                    f'def {func.name}:',
                    f'    """{func.description}"""',
                ])
            # 添加函数代码
            content.append(func.code)
            content.append('')  # 空行分隔

        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': 'debugtalk.py生成成功',
            'data': {
                'content': '\n'.join(content)
            }
        })

    @swagger_auto_schema(
        tags=['自定义函数'],
        operation_summary='测试函数',
        operation_description='测试自定义函数的可用性',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['code'],
            properties={
                'code': openapi.Schema(type=openapi.TYPE_STRING, description='函数代码'),
                'test_args': openapi.Schema(type=openapi.TYPE_OBJECT, description='测试参数')
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
                            'result': openapi.Schema(type=openapi.TYPE_STRING, description='执行结果')
                        }
                    )
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def test_function(self, request):
        """测试函数"""
        code = request.data.get('code')
        test_args = request.data.get('test_args', {})

        if not code:
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '请提供函数代码',
                'errors': {'code': ['该字段是必填项']}
            })

        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            # 导入并执行函数
            import importlib.util
            spec = importlib.util.spec_from_file_location("temp_module", temp_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 获取函数对象
            func_name = code.split('def ')[1].split('(')[0].strip()
            func = getattr(module, func_name)

            # 执行函数
            result = func(**test_args) if test_args else func()

            return Response({
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': '函数测试成功',
                'data': {
                    'result': str(result)
                }
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': '函数测试失败',
                'errors': {'detail': str(e)}
            })

        finally:
            # 清理临时文件
            if 'temp_file' in locals():
                os.unlink(temp_file)
