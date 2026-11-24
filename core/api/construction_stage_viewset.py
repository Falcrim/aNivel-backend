from rest_framework import viewsets, filters
from core.models import ConstructionStage
from core.serializers import ConstructionStageSerializer


class ConstructionStageViewSet(viewsets.ModelViewSet):
    """
    API endpoint para administración de Etapas Constructivas Dinámicas.
    Permite crear, listar, ordenar y buscar etapas de obra.
    """
    queryset = ConstructionStage.objects.all()
    serializer_class = ConstructionStageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            if is_active.lower() in ['true', '1']:
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() in ['false', '0']:
                queryset = queryset.filter(is_active=False)
        return queryset
