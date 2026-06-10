from rest_framework.pagination import PageNumberPagination
from rest_framework_datatables.pagination import DatatablesPageNumberPagination


class AOTSPageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


class DualFormatPagination(PageNumberPagination):
    """
    Standard REST pagination by default; legacy DataTables when format=datatables.
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def __init__(self):
        self._datatables = None

    def paginate_queryset(self, queryset, request, view=None):
        if request.query_params.get('format') == 'datatables':
            self._datatables = DatatablesPageNumberPagination()
            self._datatables.request = request
            return self._datatables.paginate_queryset(queryset, request, view)
        self._datatables = None
        return super().paginate_queryset(queryset, request, view)

    def get_paginated_response(self, data):
        if self._datatables is not None:
            return self._datatables.get_paginated_response(data)
        return super().get_paginated_response(data)
