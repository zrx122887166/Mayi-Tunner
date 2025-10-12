from rest_framework.response import Response
from rest_framework import status


class ResponseHandler:
    """响应处理工具类"""
    @staticmethod
    def success(data=None, message="操作成功", code=status.HTTP_200_OK):
        """返回成功响应"""
        return Response({
            "status": "success",
            "code": code,
            "message": message,
            "data": data or {}
        }, status=code)

    @staticmethod
    def error(message="操作失败", errors=None, code=status.HTTP_400_BAD_REQUEST):
        """返回错误响应"""
        return Response({
            "status": "error",
            "code": code,
            "message": message,
            "data": {},
            "errors": errors or {}
        }, status=code) 