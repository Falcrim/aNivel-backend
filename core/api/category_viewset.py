from django.db.models import Count
from rest_framework import viewsets, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Category
from core.serializers import CategorySerializer, SubcategorySerializer


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Lectura y renombrado de Categorías maestras de presupuesto.
    La creación y eliminación están bloqueadas por API (gestionadas por código/migraciones).
    """
    queryset = Category.objects.annotate(
        subcategories_count=Count('subcategories')
    ).prefetch_related('subcategories').all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    pagination_class = None
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'subcategories_count', 'code']
    ordering = ['name']

    @action(detail=True, methods=['get'], url_path='subcategories')
    def subcategories(self, request, pk=None):
        """
        Retorna todas las subcategorías pertenecientes a esta categoría específica.
        Endpoint: GET /api/core/categories/{id}/subcategories/
        """
        category = self.get_object()
        subcategories = category.subcategories.all()
        serializer = SubcategorySerializer(subcategories, many=True)
        return Response(serializer.data)
