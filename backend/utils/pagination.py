from rest_framework.pagination import PageNumberPagination

from .constants import DEFAULT_PAGE_SIZE


class FoodgramPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = DEFAULT_PAGE_SIZE
