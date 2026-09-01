from rest_framework import viewsets, filters
from core.models import Subcategory
from core.serializers import SubcategorySerializer


class SubcategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD para Subcategorías de presupuesto (Fierros, Cementos, Pinturas, etc.).
    
    Filtros soportados:
    - Por categoría: ?category=1 o ?category_id=1
    - Búsqueda: ?search=fierro
    """
    queryset = Subcategory.objects.select_related('category').all()
    serializer_class = SubcategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'category__name']
    ordering_fields = ['name', 'category__name']
    ordering = ['category__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get('category') or self.request.query_params.get('category_id')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset