from collections import OrderedDict
from rest_framework import pagination
from .response import ApiResponse


class Pagination(pagination.PageNumberPagination):

    paginate_by_param = 'page'
    page_size_query_param = 'count'

    def get_paginated_data(self, data: dict):
        return OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])

    def get_paginated_response(self, data: dict):
        return ApiResponse(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))
