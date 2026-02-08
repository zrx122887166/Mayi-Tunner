from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import (
    APIException, NotAuthenticated, AuthenticationFailed,
    NotFound, PermissionDenied, ValidationError
)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器，确保所有异常返回统一的响应格式
    
    Args:
        exc: 异常对象
        context: 异常上下文
    
    Returns:
        Response: 统一格式的响应对象
    """
    # 首先调用DRF默认的异常处理器
    response = exception_handler(exc, context)
    
    # 如果DRF没有处理这个异常，我们自己处理
    if response is None:
        if isinstance(exc, Http404):
            data = {
                "status": "error",
                "code": status.HTTP_404_NOT_FOUND,
                "message": "未找到请求的资源",
                "data": {},
                "errors": {"detail": ["请求的资源不存在"]}
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        
        if isinstance(exc, Exception):
            data = {
                "status": "error",
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "服务器内部错误",
                "data": {},
                "errors": {"detail": [str(exc)]}
            }
            return Response(data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return None
    
    # 处理DRF的标准异常
    error_data = {
        "status": "error",
        "code": response.status_code,
        "message": get_error_message(exc),
        "data": {},
        "errors": {}
    }
    
    # 处理验证错误
    if isinstance(exc, ValidationError):
        error_data["errors"] = response.data
    else:
        error_data["errors"] = {"detail": [response.data.get("detail", str(exc))]}
    
    response.data = error_data
    return response


def get_error_message(exc):
    """
    根据异常类型获取错误消息
    
    Args:
        exc: 异常对象
    
    Returns:
        str: 错误消息
    """
    if isinstance(exc, NotAuthenticated):
        return "身份验证失败，请先登录"
    elif isinstance(exc, AuthenticationFailed):
        return "身份验证失败，请检查您的凭据"
    elif isinstance(exc, PermissionDenied):
        return "您没有执行此操作的权限"
    elif isinstance(exc, NotFound):
        return "未找到请求的资源"
    elif isinstance(exc, ValidationError):
        return "请求参数验证失败"
    else:
        return "请求处理失败" 