from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer, LoginUserSerializer
from TestRunner.pagination import CustomPagination
import logging

logger = logging.getLogger('testrunner')

User = get_user_model()


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


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView, BaseAPIView):
    """用户登录视图"""
    permission_classes = [AllowAny]
    authentication_classes = []
    
    @swagger_auto_schema(
        tags=['认证接口'],
        operation_summary='用户登录',
        operation_description='登录并获取JWT令牌',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='密码', format='password'),
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
                            'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT访问令牌'),
                            'user': openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                                }
                            )
                        }
                    )
                }
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='错误信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                }
            )
        }
    )
    def post(self, request):
        self.log_request(request, '用户登录请求')
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            logger.warning(f'登录失败：用户名或密码为空 - username: {username}')
            return Response({
                'status': 'error',
                'code': status.HTTP_400_BAD_REQUEST,
                'message': _('用户名和密码不能为空'),
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if user is None:
            logger.warning(f'登录失败：用户名或密码错误 - username: {username}')
            return Response({
                'status': 'error',
                'code': status.HTTP_401_UNAUTHORIZED,
                'message': _('用户名或密码错误'),
                'data': {}
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        logger.info(f'用户登录成功 - username: {username}')
        return Response({
            'status': 'success',
            'code': status.HTTP_200_OK,
            'message': _('登录成功'),
            'data': {
                'token': access_token,
                'user': LoginUserSerializer(user).data
            }
        }, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet, BaseAPIView):
    """
    用户管理接口
    
    包含用户的增删改查等功能
    """
    queryset = User.objects.filter(is_deleted=False)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return self.serializer_class
    
    def get_error_response(self, message, code=status.HTTP_400_BAD_REQUEST):
        return Response({
            'status': 'error',
            'code': code,
            'message': message,
            'data': None
        }, status=code)
    
    def get_success_response(self, data=None, message='操作成功', code=status.HTTP_200_OK):
        return Response({
            'status': 'success',
            'code': code,
            'message': message,
            'data': data
        }, status=code)

    def get_queryset(self):
        """
        重写get_queryset方法，添加搜索功能
        """
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        return queryset

    @swagger_auto_schema(
        tags=['用户管理'],
        operation_summary='创建用户',
        operation_description='创建新用户（注册）',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='密码'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱地址（可选）'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='手机号（可选）'),
                'avatar': openapi.Schema(type=openapi.TYPE_STRING, description='头像URL（可选）')
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'phone': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'avatar': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        self.log_request(request, '创建用户请求')
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f'创建用户失败：数据验证错误 - errors: {serializer.errors}')
            return self.get_error_response(serializer.errors)
        self.perform_create(serializer)
        logger.info(f'用户创建成功 - username: {serializer.data.get("username")}')
        return self.get_success_response(
            data=serializer.data,
            message=_('用户创建成功'),
            code=status.HTTP_201_CREATED
        )

    @swagger_auto_schema(
        tags=['用户管理'],
        operation_summary='获取用户列表',
        operation_description='获取所有用户的列表，支持分页和搜索',
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
                'search',
                openapi.IN_QUERY,
                description='搜索关键词，支持用户名、邮箱、手机号模糊搜索',
                type=openapi.TYPE_STRING,
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
                                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                        'username': openapi.Schema(type=openapi.TYPE_STRING),
                                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                                        'phone': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                        'avatar': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                        'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
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
        self.log_request(request, '获取用户列表请求')
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.paginator.get_paginated_response(serializer.data)
            logger.info(f'获取用户列表成功 - page: {request.GET.get("page", 1)}, page_size: {request.GET.get("page_size", 10)}, search: {request.GET.get("search", "")}')
            return self.get_success_response(
                data=paginated_data,
                message=_('获取用户列表成功'),
                code=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(queryset, many=True)
        return self.get_success_response(
            data={'results': serializer.data},
            message=_('获取用户列表成功'),
            code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        tags=['用户管理'],
        operation_summary='获取用户详情',
        operation_description='获取指定用户的详细信息',
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'phone': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'avatar': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                }
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.get_success_response(
            data=serializer.data,
            message=_('获取用户详情成功')
        )

    @swagger_auto_schema(
        tags=['用户管理'],
        operation_summary='更新用户信息',
        operation_description='更新指定用户的完整信息（PUT方法需要提供所有必填字段）',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='用户名（必填）'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='邮箱地址（可选）'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='手机号（可选）'),
                'avatar': openapi.Schema(type=openapi.TYPE_STRING, description='头像URL（可选）'),
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='是否激活（可选）')
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
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'phone': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'avatar': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            'date_joined': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                        }
                    )
                }
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='接口状态'),
                    'code': openapi.Schema(type=openapi.TYPE_INTEGER, description='状态码'),
                    'message': openapi.Schema(type=openapi.TYPE_OBJECT, description='错误信息'),
                    'data': openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True)
                }
            )
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return self.get_error_response(serializer.errors)
        self.perform_update(serializer)
        return self.get_success_response(
            data=serializer.data,
            message=_('用户信息更新成功'),
            code=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        tags=['用户管理'],
        operation_summary='删除用户',
        operation_description='软删除指定用户',
        responses={
            status.HTTP_200_OK: openapi.Schema(
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
        try:
            instance = self.get_object()
            instance.is_deleted = True
            instance.save()
            return self.get_success_response(
                message=_('用户删除成功'),
                code=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f'删除用户失败 - error: {str(e)}')
            return self.get_error_response(
                message=_('删除用户失败'),
                code=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 