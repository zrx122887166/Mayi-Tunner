from rest_framework import status
from rest_framework.response import Response

class ResponseHandler:
    """统一响应处理工具类"""
    
    @staticmethod
    def success(data=None, message="操作成功", code=status.HTTP_200_OK):
        """
        处理成功响应
        :param data: 响应数据
        :param message: 提示信息
        :param code: 状态码
        :return: Response
        """
        response_data = {
            "status": "success",
            "code": code,
            "message": message,
            "data": data if data is not None else {}
        }
        return Response(response_data, status=code)

    @staticmethod
    def error(message="操作失败", code=status.HTTP_400_BAD_REQUEST, errors=None):
        """
        处理错误响应
        :param message: 错误信息
        :param code: 状态码
        :param errors: 详细错误信息
        :return: Response
        """
        response_data = {
            "status": "error",
            "code": code,
            "message": message,
            "data": {},
            "errors": errors if errors is not None else {}
        }
        return Response(response_data, status=code) 