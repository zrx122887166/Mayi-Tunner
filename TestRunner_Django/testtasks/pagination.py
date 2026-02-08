from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    标准分页器，确保分页结果符合统一的响应格式
    """
    page_size = 10  # 默认每页显示10条
    page_size_query_param = 'page_size'  # 允许客户端通过此参数覆盖默认分页大小
    max_page_size = 100  # 每页最大显示数量
    
    def get_paginated_response(self, data):
        """
        重写分页响应方法，返回统一格式的响应
        
        注意：这个方法不直接返回统一格式的响应，而是返回一个包含分页信息的数据结构，
        由视图集的list方法进一步包装成统一格式的响应。
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        }) 