from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginador estándar para listas del proyecto aNivel.
    
    Características:
    - Tamaño por defecto: 25 registros por página.
    - Configurable por cliente: ?page_size=50 (máximo 200).
    - Desactivable bajo demanda: ?paginate=false o ?page_size=all (retorna lista plana).
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200

    def paginate_queryset(self, queryset, request, view=None):
        paginate_param = request.query_params.get('paginate', '').lower()
        page_size_param = request.query_params.get(self.page_size_query_param, '').lower()

        if paginate_param in ('false', '0', 'no') or page_size_param in ('all', '0'):
            return None

        return super().paginate_queryset(queryset, request, view)
