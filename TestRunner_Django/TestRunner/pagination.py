from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """统一的分页类"""
    page_size = 10  # 默认每页显示10条
    page_size_query_param = 'page_size'  # 每页数量的参数名
    max_page_size = 100  # 每页最大显示数量

    def get_paginated_response(self, data):
        return {
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        } 