from rest_framework import viewsets, mixins, permissions, filters, status
from rest_framework.response import Response
from inventory.models.tool_transfer import ToolTransfer
from inventory.serializers.tool_transfer_serializer import (
    ToolTransferReadSerializer,
    ToolTransferCreateSerializer
)


class ToolTransferViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """
    Registro y consulta de movimientos y traslados de herramientas entre locaciones.
    """
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['tool__name', 'tool__code', 'responsible_person', 'notes']
    ordering_fields = ['transfer_date', 'created_at']
    ordering = ['-transfer_date']

    def get_queryset(self):
        qs = ToolTransfer.objects.select_related(
            'tool',
            'origin_location',
            'destination_location',
            'destination_location__project',
            'created_by'
        ).all()

        tool_id = self.request.query_params.get('tool')
        if tool_id:
            qs = qs.filter(tool_id=tool_id)

        destination_id = self.request.query_params.get('destination')
        if destination_id:
            qs = qs.filter(destination_location_id=destination_id)

        origin_id = self.request.query_params.get('origin')
        if origin_id:
            qs = qs.filter(origin_location_id=origin_id)

        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(destination_location__project_id=project_id)

        return qs

    def get_serializer_class(self):
        if self.action == 'create':
            return ToolTransferCreateSerializer
        return ToolTransferReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        transfer = serializer.save()
        read_serializer = ToolTransferReadSerializer(transfer)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)
