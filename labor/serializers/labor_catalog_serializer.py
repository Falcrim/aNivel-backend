from rest_framework import serializers
from core.serializers import SubcategorySerializer, UnitOfMeasureSerializer
from labor.models import LaborCatalogItem


class LaborCatalogItemReadSerializer(serializers.ModelSerializer):
    """Serializer optimizado para lectura y catálogo de mano de obra con detalles."""
    subcategory_detail = SubcategorySerializer(source='subcategory', read_only=True)
    unit_detail = UnitOfMeasureSerializer(source='unit', read_only=True)

    class Meta:
        model = LaborCatalogItem
        fields = [
            'id',
            'subcategory',
            'subcategory_detail',
            'name',
            'detail',
            'unit',
            'unit_detail',
            'suggested_cost',
            'contractor_type',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class LaborCatalogItemWriteSerializer(serializers.ModelSerializer):
    """Serializer para creación y actualización de ítems de catálogo de mano de obra."""
    class Meta:
        model = LaborCatalogItem
        fields = [
            'id',
            'subcategory',
            'name',
            'detail',
            'unit',
            'suggested_cost',
            'contractor_type',
            'is_active',
        ]


LaborCatalogItemSerializer = LaborCatalogItemReadSerializer
