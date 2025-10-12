from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
import pymysql
import psycopg2
import sqlite3
from sqlalchemy import create_engine, text

from .models import DatabaseConfig
from .serializers import DatabaseConfigSerializer

class DatabaseConfigViewSet(viewsets.ModelViewSet):
    """数据库配置视图集"""
    queryset = DatabaseConfig.objects.all()
    serializer_class = DatabaseConfigSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['project', 'is_active', 'db_type']
    search_fields = ['name', 'host', 'database']
    ordering_fields = ['name', 'created_at', 'updated_at']
    
    def get_queryset(self):
        """根据条件筛选查询集"""
        queryset = super().get_queryset()
        return queryset
    
    def list(self, request, *args, **kwargs):
        """重写列表查询方法，按照统一响应格式返回"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            return Response({
                "status": "success",
                "code": 200,
                "message": "数据库配置列表获取成功",
                "data": response.data
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "code": 200,
            "message": "数据库配置列表获取成功",
            "data": serializer.data
        })
    
    def create(self, request, *args, **kwargs):
        """重写创建方法，按照统一响应格式返回"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({
                "status": "success",
                "code": status.HTTP_201_CREATED,
                "message": "数据库配置创建成功",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": "error",
            "code": status.HTTP_400_BAD_REQUEST,
            "message": "数据库配置创建失败",
            "data": {},
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """重写详情查询方法，按照统一响应格式返回"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "status": "success",
            "code": 200,
            "message": "数据库配置详情获取成功",
            "data": serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """重写更新方法，按照统一响应格式返回"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response({
                "status": "success",
                "code": 200,
                "message": "数据库配置更新成功",
                "data": serializer.data
            })
        
        return Response({
            "status": "error",
            "code": status.HTTP_400_BAD_REQUEST,
            "message": "数据库配置更新失败",
            "data": {},
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """重写删除方法，按照统一响应格式返回"""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "code": status.HTTP_204_NO_CONTENT,
            "message": "数据库配置删除成功",
            "data": {}
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'], url_path='test_connection')
    def test_saved_connection(self, request, pk=None):
        """测试已保存的数据库配置连接
        
        返回:
            连接成功或失败的消息
        """
        try:
            # 获取数据库配置对象
            db_config = self.get_object()
            
            # 从数据库配置对象获取连接信息
            db_type = db_config.db_type
            host = db_config.host
            port = db_config.port
            database = db_config.database
            user = db_config.username
            password = db_config.password
            
            # 根据不同数据库类型测试连接
            if db_type == 'mysql':
                # MySQL连接测试
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    connect_timeout=5
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                connection.close()
                
            elif db_type == 'postgresql':
                # PostgreSQL连接测试
                connection = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname=database,
                    connect_timeout=5
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                connection.close()
                
            elif db_type == 'sqlite':
                # SQLite连接测试
                connection = sqlite3.connect(database)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                connection.close()
                
            else:
                # 使用SQLAlchemy连接其他类型数据库
                conn_strings = {
                    'oracle': f"oracle://{user}:{password}@{host}:{port}/{database}",
                    'sqlserver': f"mssql+pymssql://{user}:{password}@{host}:{port}/{database}"
                }
                
                if db_type not in conn_strings:
                    return Response({
                        "status": "error",
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "不支持的数据库类型",
                        "data": {},
                        "errors": {
                            "detail": [f"不支持的数据库类型: {db_type}"]
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                engine = create_engine(conn_strings[db_type])
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
            
            # 返回成功响应，符合前端期望的格式
            return Response({
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "数据库连接测试成功",
                "data": {
                    "test_result": {
                        "connected": True,
                        "db_type": db_type,
                        "message": "成功连接到数据库"
                    }
                }
            })
            
        except Exception as e:
            # 捕获连接异常并返回错误响应
            return Response({
                "status": "error",
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "数据库连接测试失败",
                "data": {},
                "errors": {
                    "detail": [f"连接失败: {str(e)}"]
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'], url_path='test-connection')
    def test_connection(self, request):
        """测试数据库连接
        
        请求参数:
            db_type: 数据库类型 (mysql, postgresql, sqlite, oracle, sqlserver)
            host: 主机地址
            port: 端口号
            database: 数据库名
            user: 用户名
            password: 密码
            
        返回:
            连接成功或失败的消息
        """
        try:
            # 从请求中获取数据库连接信息
            db_type = request.data.get('db_type', 'mysql')
            host = request.data.get('host')
            port = int(request.data.get('port', 3306))
            database = request.data.get('database')
            user = request.data.get('user')
            password = request.data.get('password')
            
            # 验证必填字段
            if not all([database]) or (db_type != 'sqlite' and not all([host, user, password])):
                return Response({
                    "status": "error",
                    "code": status.HTTP_400_BAD_REQUEST,
                    "message": "缺少必要的连接参数",
                    "data": {},
                    "errors": {
                        "detail": ["请提供完整的数据库连接信息"]
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 根据不同数据库类型测试连接
            if db_type == 'mysql':
                # MySQL连接测试
                connection = pymysql.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    connect_timeout=5
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                connection.close()
                
            elif db_type == 'postgresql':
                # PostgreSQL连接测试
                connection = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    dbname=database,
                    connect_timeout=5
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                connection.close()
                
            elif db_type == 'sqlite':
                # SQLite连接测试
                connection = sqlite3.connect(database)
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                connection.close()
                
            else:
                # 使用SQLAlchemy连接其他类型数据库
                conn_strings = {
                    'oracle': f"oracle://{user}:{password}@{host}:{port}/{database}",
                    'sqlserver': f"mssql+pymssql://{user}:{password}@{host}:{port}/{database}"
                }
                
                if db_type not in conn_strings:
                    return Response({
                        "status": "error",
                        "code": status.HTTP_400_BAD_REQUEST,
                        "message": "不支持的数据库类型",
                        "data": {},
                        "errors": {
                            "detail": [f"不支持的数据库类型: {db_type}"]
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                engine = create_engine(conn_strings[db_type])
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
            
            # 返回成功响应，符合前端期望的格式
            return Response({
                "status": "success",
                "code": status.HTTP_200_OK,
                "message": "数据库连接测试成功",
                "data": {
                    "connected": True,
                    "test_result": {
                        "db_type": db_type,
                        "message": "成功连接到数据库"
                    }
                }
            })
            
        except Exception as e:
            # 捕获连接异常并返回错误响应
            return Response({
                "status": "error",
                "code": status.HTTP_400_BAD_REQUEST,
                "message": "数据库连接测试失败",
                "data": {},
                "errors": {
                    "detail": [f"连接失败: {str(e)}"]
                }
            }, status=status.HTTP_400_BAD_REQUEST)
