from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from materials.models import MaterialCatalogItem
from materials.serializers import (
    MaterialCatalogItemReadSerializer,
    MaterialCatalogItemWriteSerializer,
)


class MaterialCatalogItemViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para el Catálogo Maestro de Materiales.
    
    Filtros soportados:
    - Por subcategoría: ?subcategory=1 o ?subcategory_id=1
    - Por estado activo: ?is_active=true o ?is_active=false
    - Búsqueda textual: ?search=fierro 12mm
    - Ordenamiento: ?ordering=name o ?ordering=-price_per_purchase_unit
    """
    queryset = MaterialCatalogItem.objects.select_related(
        'subcategory', 'subcategory__category', 'unit_measure', 'unit_purchase'
    ).all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'subcategory__name']
    ordering_fields = ['name', 'price_per_purchase_unit', 'subcategory__name', 'waste_pct']
    ordering = ['subcategory__name', 'name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MaterialCatalogItemWriteSerializer
        return MaterialCatalogItemReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por subcategoría
        subcategory_id = self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id')
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)
            
        # Filtro por activo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])
            
        return queryset

    @action(detail=False, methods=['get'], url_path='grouped-by-subcategory')
    def grouped_by_subcategory(self, request):
        """
        Retorna los ítems del catálogo organizados y agrupados por subcategoría.
        Ideal para selectores de catálogo y acordeones en el frontend.
        Endpoint: GET /api/materials/catalog/grouped-by-subcategory/
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
                MaterialCatalogItemReadSerializer(item).data
            )
            grouped_data[subcat_id]['items_count'] += 1

        return Response(list(grouped_data.values()), status=status.HTTP_200_OK)
