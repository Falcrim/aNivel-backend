from django.db.models import Count
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Category
from core.serializers import CategorySerializer, SubcategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD para Categorías de presupuesto (Materiales, Mano de Obra, Gastos Generales, etc.).
    """
    queryset = Category.objects.annotate(
        subcategories_count=Count('subcategories')
    ).prefetch_related('subcategories').all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'subcategories_count']
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