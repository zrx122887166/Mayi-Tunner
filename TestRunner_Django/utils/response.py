from rest_framework.response import Response

class APIResponse(Response):
    """
    统一的API响应格式
    """
    def __init__(self, status="success", code=200, message="", data=None, errors=None, **kwargs):
        response_data = {
            "status": status,
            "code": code,
            "message": message,
            "data": data if data is not None else {},
        }
        
        if errors is not None:
            response_data["errors"] = errors
            
        super().__init__(data=response_data, status=code, **kwargs) 