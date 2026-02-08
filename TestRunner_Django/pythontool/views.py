from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.paginator import Paginator
import subprocess
from django.utils import timezone
import os
import logging
from datetime import datetime
from django.conf import settings

from .models import Tool, Tools
from .serializers import ToolSerializer, ToolsSerializer

# 设置日志
logger = logging.getLogger(__name__)


class ToolViewSet(viewsets.ModelViewSet):
    """Python工具视图集"""
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        group_name = self.request.query_params.get('group_name')

        if name:
            queryset = queryset.filter(name__icontains=name)
        if group_name:
            queryset = queryset.filter(group_name__icontains=group_name)

        return queryset

    def list(self, request, *args, **kwargs):
        """获取工具列表"""
        try:
            page = int(request.query_params.get('page', 1))
            size = int(request.query_params.get('size', 10))
            name_filter = request.query_params.get('name', '')

            # 构建查询
            tools = Tool.objects.all().order_by('-create_time')
            if name_filter:
                tools = tools.filter(name__icontains=name_filter)

            # 分页处理
            paginator = Paginator(tools, size)
            page_obj = paginator.get_page(page)

            # 格式化结果
            formatted_tools = []
            for tool in page_obj.object_list:
                tool_dict = {
                    'id': tool.id,
                    'name': tool.name,
                    'group_name': tool.group_name,  # 新增：返回分组名称
                    'remark': tool.remark,
                    'pythonScript': tool.pythonScript,
                    'params': tool.params,
                    'create_time': timezone.localtime(tool.create_time).strftime(
                        "%Y-%m-%d %H:%M:%S") if tool.create_time else None,
                    'creator': tool.creator.username if tool.creator else '未知用户',
                    'connect_pools': tool.connect_pools,
                    'has_params': bool(tool.params)
                }
                print('测试时间', tool_dict)
                formatted_tools.append(tool_dict)

            return Response({
                'count': paginator.count,
                'results': formatted_tools,
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """创建新工具"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)  # 调用 perform_create 设置 creator
            return Response({
                'message': '保存成功',
                'id': serializer.instance.id
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def perform_create(self, serializer):
        """保存创建的对象，并设置创建人"""
        # 将当前登录用户作为 creator 保存
        serializer.save(creator=self.request.user)

    def update(self, request, *args, **kwargs):
        """更新工具"""
        try:
            tool = self.get_object()
            data = request.data
            print("更新工具接收的数据:", data)  # 调试信息

            # 处理字段映射
            update_data = {
                'name': data.get('name', tool.name),
                'group_name': data.get('group_name', tool.group_name),  # 新增：处理分组名称
                'remark': data.get('remark', tool.remark),
                'pythonScript': data.get('pythonScript', tool.pythonScript),
                'params': data.get('params', tool.params),
                'connect_pools': data.get('connect_pools', tool.connect_pools) or data.get('selectedConnectPools',
                                                                                           tool.connect_pools)
                # 兼容前端的 selectedConnectPools 字段
            }

            print("处理后的更新数据:", update_data)  # 调试信息

            serializer = self.get_serializer(tool, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': '更新成功',
                    'id': tool.id
                })
            else:
                return Response({
                    'error': '数据验证失败',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 新增：兼容旧接口的 pythonlist 方法
    @action(detail=False, methods=['get'])
    def pythonlist(self, request):
        """兼容旧接口的列表方法"""
        return self.list(request)

    # 新增：兼容旧接口的 detail 方法
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """兼容旧接口的详情方法"""
        tool = self.get_object()
        tool_dict = {
            'id': tool.id,
            'name': tool.name,
            'group_name': tool.group_name,
            'remark': tool.remark,
            'pythonScript': tool.pythonScript,
            'params': tool.params,
            'create_time': timezone.localtime(tool.create_time).strftime("%Y-%m-%d %H:%M:%S"),
            'creator': tool.creator.username if tool.creator else '未知用户',
            'connect_pools': tool.connect_pools,
            'has_params': bool(tool.params)
        }
        return Response(tool_dict)


class ToolsViewSet(viewsets.ModelViewSet):
    """依赖工具视图集"""
    queryset = Tools.objects.all()
    serializer_class = ToolsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """重写查询集，支持名称过滤"""
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', '')

        if name:
            queryset = queryset.filter(name__icontains=name)

        return queryset.order_by('name')  # 按名称排序

    def list(self, request, *args, **kwargs):
        """获取依赖工具列表 - 支持分页和无分页两种模式"""
        try:
            # 检查是否要求不分页
            no_pagination = request.query_params.get('no_pagination') == 'true'
            name_filter = request.query_params.get('name', '')

            # 构建查询
            tools = self.get_queryset()

            if no_pagination:
                # 不分页模式：直接返回所有数据
                serializer = self.get_serializer(tools, many=True)
                return Response(serializer.data)
            else:
                # 分页模式：兼容原有逻辑
                page = int(request.query_params.get('page', 1))
                size = int(request.query_params.get('size', 10))

                # 分页处理
                paginator = Paginator(tools, size)
                page_obj = paginator.get_page(page)

                # 序列化数据
                serializer = self.get_serializer(page_obj, many=True)

                return Response({
                    'count': paginator.count,
                    'results': serializer.data,
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PythonRunView(APIView):
    """Python脚本执行视图"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """执行Python脚本"""
        start_time = datetime.now()
        logger.info(f"=== 开始处理请求 {request.method} ===")

        try:
            data = request.data
            tool_id = data.get('id')

            if not tool_id:
                logger.error("缺少必要参数: id")
                return Response({'error': '缺少必要参数: id'}, status=status.HTTP_400_BAD_REQUEST)

            # 获取工具配置
            try:
                tool = Tool.objects.get(id=tool_id)
                logger.info(f"加载工具成功 ID: {tool_id} | 名称: {tool.name}")
            except Tool.DoesNotExist:
                logger.error(f"工具不存在 ID: {tool_id}")
                return Response({'error': '工具不存在'}, status=status.HTTP_404_NOT_FOUND)

            # 动态查找Python解释器
            python_interpreter_candidates = [
                os.path.join(settings.BASE_DIR, "venv", "bin", "python3"),
                os.path.expanduser("~/venv/bin/python3"),
                "/usr/local/bin/python3",
                "/usr/bin/python3",
                "python3"
            ]
            python_interpreter = next((p for p in python_interpreter_candidates if os.path.exists(p)), None)

            if not python_interpreter:
                error_msg = "Python解释器未找到，候选路径:\n" + "\n".join(python_interpreter_candidates)
                logger.critical(error_msg)
                return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            logger.info(f"使用Python解释器: {python_interpreter}")

            # 生成临时文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_filename = f"script_{tool_id}_{timestamp}.py"
            temp_file_path = os.path.join("/tmp", temp_filename)

            logger.info(f"创建临时文件: {temp_file_path}")

            try:
                # 写入组合脚本
                with open(temp_file_path, 'w+') as f:
                    # 写入公共库
                    for pool in tool.connect_pools:
                        try:
                            common_tool = Tools.objects.get(name=pool)
                            f.write(f"# === {pool} ===\n")
                            f.write(common_tool.pythonScript + "\n\n")
                            logger.debug(f"注入公共方法: {pool}")
                        except Tools.DoesNotExist:
                            logger.error(f"公共方法不存在: {pool}")
                            return Response({'error': f'未找到公共方法: {pool}'}, status=status.HTTP_404_NOT_FOUND)

                    # 写入主脚本
                    f.write(f"# === 主脚本 ===\n")
                    f.write(tool.pythonScript)
                    logger.debug(f"脚本内容已写入临时文件")

                # 构建执行命令
                command = [python_interpreter, temp_file_path]
                for key, value in data.items():
                    if key == 'id':
                        continue
                    command.extend([f"-{key}", str(value)])

                logger.info(f"执行命令: {' '.join(command)}")

                # 执行子进程
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                # 记录执行结果
                logger.info(f"执行完成，耗时: {(datetime.now() - start_time).total_seconds()}秒")
                logger.debug(f"STDOUT:\n{result.stdout}")
                logger.debug(f"STDERR:\n{result.stderr}")

                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {str(e)}")

                if result.returncode == 0:
                    response_data = {'message': '执行成功', 'output': result.stdout.strip()}
                    logger.info("执行成功")
                    return Response(response_data)
                else:
                    response_data = {
                        'error': '脚本执行失败',
                        'detail': {
                            'stderr': result.stderr.strip(),
                            'stdout': result.stdout.strip(),
                            'exit_code': result.returncode,
                        }
                    }
                    logger.error(f"执行失败 CODE:{result.returncode}")
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            except subprocess.TimeoutExpired:
                logger.error("执行超时")
                return Response({'error': '执行超时'}, status=status.HTTP_504_GATEWAY_TIMEOUT)

            except Exception as e:
                logger.exception("执行异常")
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.exception("未捕获的异常")
            return Response({'error': f'服务器错误: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)