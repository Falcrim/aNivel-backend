from rest_framework import viewsets, filters
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
    """
    queryset = LaborCatalogItem.objects.select_related(
        'subcategory',
        'subcategory__category',
        'unit'
    ).all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'detail', 'subcategory__name', 'contractor_type']
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

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() in ['true', '1'])

        return queryset
