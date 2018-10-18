from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    # 每页数据条数
    page_size = 4
    #前端url中访问的key
    page_size_query_param = 'page_size'
    # 前端设置的最大页面显示条数
    max_page_size = 20


