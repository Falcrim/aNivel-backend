from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from labor.models import LaborCatalogItem
from labor.serializers import (
    LaborCatalogItemReadSerializer,
    LaborCatalogItemWriteSerializer,
)


class LaborCatalogItemViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para el Catálogo Maestro de Mano de Obra (Tarifario referencial).

    Filtros soportados:
    - Por subcategoría: ?subcategory=1 o ?subcategory_id=1
    - Por estado activo: ?is_active=true
    - Búsqueda: ?search=muro o ?search=pintura
    - Ordenamiento: ?ordering=subcategory__name,name o ?ordering=-suggested_cost
    - Sin paginación: ?paginate=false
    """
    queryset = LaborCatalogItem.objects.select_related(
        'subcategory',
        'subcategory__category',
        'unit',
        'supplier'
    ).all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'detail', 'subcategory__name', 'contractor_type', 'supplier__name']
    ordering_fields = ['subcategory__name', 'name', 'suggested_cost']
    ordering = ['subcategory__name', 'name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return LaborCatalogItemWriteSerializer
        return LaborCatalogItemReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        subcategory_id = self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id')
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)

        supplier_id = self.request.query_params.get('supplier') or self.request.query_params.get('supplier_id')
        if supplier_id:
            queryset = queryset.filter(supplier_id=supplier_id)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])

        return queryset

    def paginate_queryset(self, queryset):
        if self.request.query_params.get('paginate') == 'false':
            return None
        return super().paginate_queryset(queryset)

    @action(detail=False, methods=['get'], url_path='grouped-by-subcategory')
    def grouped_by_subcategory(self, request):
        """
        Retorna las tareas del catálogo organizadas y agrupadas por subcategoría.
        Ideal para selectores de catálogo y acordeones en el frontend.
        Endpoint: GET /api/labor/catalog/grouped-by-subcategory/
        """
        queryset = self.filter_queryset(self.get_queryset())

        grouped_data = {}
        for item in queryset:
            subcat_id = item.subcategory_id
            if subcat_id not in grouped_data:
                grouped_data[subcat_id] = {
                    'subcategory_id': item.subcategory.id,
                    'subcategory_name': item.subcategory.name,
                    'category_name': item.subcategory.category.name,
                    'items_count': 0,
                    'items': []
                }
            grouped_data[subcat_id]['items'].append(
                LaborCatalogItemReadSerializer(item).data
            )
            grouped_data[subcat_id]['items_count'] += 1

        return Response(list(grouped_data.values()), status=status.HTTP_200_OK)
