from rest_framework import viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from core.models.supplier import Supplier, SupplierType
from core.serializers.supplier_serializer import SupplierSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    """
    CRUD completo para el Directorio Canónico de Proveedores y Contratistas.
    
    Filtros soportados:
    - Búsqueda: ?search=monterrey
    - Por tipo: ?supplier_type=material | ?supplier_type=labor | ?supplier_type=both
    - Por estado activo: ?is_active=true | ?is_active=false
    - Ordenamiento: ?ordering=name | ?ordering=-created_at
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'contact_name', 'phone', 'email', 'address', 'notes']
    ordering_fields = ['name', 'supplier_type', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        supplier_type = self.request.query_params.get('supplier_type')
        if supplier_type:
            st_lower = supplier_type.lower()
            if st_lower in (SupplierType.MATERIAL, SupplierType.LABOR):
                queryset = queryset.filter(supplier_type__in=[st_lower, SupplierType.BOTH])
            else:
                queryset = queryset.filter(supplier_type=st_lower)
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)
                
        return queryset
