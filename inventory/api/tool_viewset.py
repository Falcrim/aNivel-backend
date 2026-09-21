from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from inventory.models.tool import Tool
from inventory.serializers.tool_serializer import ToolReadSerializer, ToolWriteSerializer
from inventory.serializers.tool_transfer_serializer import ToolTransferReadSerializer


class ToolViewSet(viewsets.ModelViewSet):
    """
    Gestión completa de inventario de herramientas, maquinaria y activos.
    """
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code', 'brand', 'model_name', 'serial_number', 'detail']
    ordering_fields = ['name', 'code', 'status', 'created_at', 'purchase_date']
    ordering = ['name']

    def get_queryset(self):
        qs = Tool.objects.select_related(
            'category',
            'current_location',
            'current_location__project'
        ).all()

        # Filtrar por locación específica
        location_id = self.request.query_params.get('location')
        if location_id:
            qs = qs.filter(current_location_id=location_id)

        # Filtrar por obra asignada a través de la locación actual
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(current_location__project_id=project_id)

        # Filtrar por tipo de locación actual (ej. WAREHOUSE, PROJECT, WORKSHOP)
        location_type = self.request.query_params.get('location_type')
        if location_type:
            qs = qs.filter(current_location__location_type=location_type)

        # Filtrar por estado operativo (AVAILABLE, IN_USE, etc.)
        tool_status = self.request.query_params.get('status')
        if tool_status:
            qs = qs.filter(status=tool_status)

        # Filtrar por categoría
        category_id = self.request.query_params.get('category')
        if category_id:
            qs = qs.filter(category_id=category_id)

        # Filtrar por activo/inactivo
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ('true', '1', 'yes'))

        return qs

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ToolWriteSerializer
        return ToolReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        read_serializer = ToolReadSerializer(instance)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()
        read_serializer = ToolReadSerializer(updated_instance)
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """
        Retorna la cronología histórica completa de traslados de esta herramienta.
        """
        tool = self.get_object()
        transfers = tool.transfers.select_related(
            'origin_location',
            'destination_location',
            'destination_location__project',
            'created_by'
        ).all()
        serializer = ToolTransferReadSerializer(transfers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
