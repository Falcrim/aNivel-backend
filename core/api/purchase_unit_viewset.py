from rest_framework import viewsets, filters
from core.models import PurchaseUnit
from core.serializers import PurchaseUnitSerializer


class PurchaseUnitViewSet(viewsets.ModelViewSet):
    """
    CRUD para Unidades Comerciales de Compra (barra, bolsa, tubo, balde, Gbl, etc.).
    Permite búsqueda por nombre o abreviación (?search=barra).
    """
    queryset = PurchaseUnit.objects.all()
    serializer_class = PurchaseUnitSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'abbreviation']
    ordering_fields = ['name', 'abbreviation']
    ordering = ['name']
