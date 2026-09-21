from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from inventory.models.tool_transfer import ToolTransfer
from inventory.models.tool import Tool
from inventory.models.location import Location
from inventory.services.transfer_service import ToolTransferService


class ToolTransferReadSerializer(serializers.ModelSerializer):
    tool_code = serializers.CharField(source='tool.code', read_only=True)
    tool_name = serializers.CharField(source='tool.name', read_only=True)
    origin_location_name = serializers.CharField(source='origin_location.name', read_only=True)
    origin_location_type = serializers.CharField(source='origin_location.location_type', read_only=True)
    destination_location_name = serializers.CharField(source='destination_location.name', read_only=True)
    destination_location_type = serializers.CharField(source='destination_location.location_type', read_only=True)
    destination_project_id = serializers.IntegerField(source='destination_location.project_id', read_only=True, default=None)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True, default=None)

    class Meta:
        model = ToolTransfer
        fields = [
            'id',
            'tool',
            'tool_code',
            'tool_name',
            'origin_location',
            'origin_location_name',
            'origin_location_type',
            'destination_location',
            'destination_location_name',
            'destination_location_type',
            'destination_project_id',
            'transfer_date',
            'responsible_person',
            'created_by',
            'created_by_username',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'origin_location', 'transfer_date', 'created_at']


class ToolTransferCreateSerializer(serializers.Serializer):
    tool_id = serializers.IntegerField()
    destination_location_id = serializers.IntegerField()
    responsible_person = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    override_status = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    def validate_tool_id(self, value: int) -> int:
        if not Tool.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La herramienta especificada no existe.")
        return value

    def validate_destination_location_id(self, value: int) -> int:
        if not Location.objects.filter(pk=value, is_active=True).exists():
            raise serializers.ValidationError("La locación de destino no existe o no está activa.")
        return value

    def create(self, validated_data: dict) -> ToolTransfer:
        tool = Tool.objects.get(pk=validated_data['tool_id'])
        destination_location = Location.objects.get(pk=validated_data['destination_location_id'])
        request = self.context.get('request')
        created_by = request.user if (request and hasattr(request, 'user')) else None

        try:
            transfer = ToolTransferService.execute_transfer(
                tool=tool,
                destination_location=destination_location,
                responsible_person=validated_data.get('responsible_person'),
                created_by=created_by,
                notes=validated_data.get('notes'),
                override_status=validated_data.get('override_status')
            )
            return transfer
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages if hasattr(e, 'messages') else str(e))
