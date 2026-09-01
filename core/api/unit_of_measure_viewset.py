from rest_framework import viewsets, filters
from core.models import UnitOfMeasure
from core.serializers import UnitOfMeasureSerializer


class UnitOfMeasureViewSet(viewsets.ModelViewSet):
    """
    CRUD para Unidades de Medida en obra (ml, m2, m3, kg, etc.).
    Permite búsqueda por nombre o abreviación (?search=ml).
    """
    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviation']
    ordering_fields = ['name', 'abbreviation']
    ordering = ['name']
