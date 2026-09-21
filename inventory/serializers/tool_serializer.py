from rest_framework import serializers
from inventory.models.tool import Tool, ToolStatus
from inventory.models.location import Location
from inventory.models.tool_category import ToolCategory


class ToolReadSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    current_location_name = serializers.CharField(source='current_location.name', read_only=True)
    current_location_type = serializers.CharField(source='current_location.location_type', read_only=True)
    current_project_id = serializers.IntegerField(source='current_location.project_id', read_only=True, default=None)
    current_project_name = serializers.CharField(source='current_location.project.name', read_only=True, default=None)

    class Meta:
        model = Tool
        fields = [
            'id',
            'code',
            'name',
            'category',
            'category_name',
            'detail',
            'brand',
            'model_name',
            'serial_number',
            'current_location',
            'current_location_name',
            'current_location_type',
            'current_project_id',
            'current_project_name',
            'status',
            'status_display',
            'purchase_date',
            'purchase_price',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class ToolWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tool
        fields = [
            'id',
            'code',
            'name',
            'category',
            'detail',
            'brand',
            'model_name',
            'serial_number',
            'current_location',
            'status',
            'purchase_date',
            'purchase_price',
            'is_active',
        ]

    def validate_code(self, value: str) -> str:
        code_clean = value.strip().upper()
        qs = Tool.objects.filter(code__iexact=code_clean)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(f"Ya existe una herramienta registrada con el código '{code_clean}'.")
        return code_clean
