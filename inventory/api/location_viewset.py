from rest_framework import viewsets, permissions, filters
from inventory.models.location import Location
from inventory.serializers.location_serializer import LocationSerializer


class LocationViewSet(viewsets.ModelViewSet):
    """
    CRUD para locaciones (almacenes centrales, talleres y frentes de obra).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LocationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'address', 'project__name']
    ordering_fields = ['name', 'created_at', 'location_type']
    ordering = ['name']

    def get_queryset(self):
        qs = Location.objects.select_related('project').prefetch_related('tools_currently_here')
        
        # Filtros opcionales por query params
        location_type = self.request.query_params.get('location_type')
        if location_type:
            qs = qs.filter(location_type=location_type)

        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1', 'yes'))

        return qs
