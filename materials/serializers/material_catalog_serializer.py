from rest_framework import serializers
from core.serializers import SubcategorySerializer, UnitOfMeasureSerializer, PurchaseUnitSerializer
from materials.models import MaterialCatalogItem


class MaterialCatalogItemReadSerializer(serializers.ModelSerializer):
    """Serializer optimizado para lectura y consulta del catálogo maestro con relaciones expandidas."""
    subcategory_detail = SubcategorySerializer(source='subcategory', read_only=True)
    unit_measure_detail = UnitOfMeasureSerializer(source='unit_measure', read_only=True)
    unit_purchase_detail = PurchaseUnitSerializer(source='unit_purchase', read_only=True)

    class Meta:
        model = MaterialCatalogItem
        fields = [
            'id',
            'subcategory',
            'subcategory_detail',
            'name',
            'description',
            'unit_measure',
            'unit_measure_detail',
            'unit_purchase',
            'unit_purchase_detail',
            'conversion_factor',
            'weight_per_purchase_unit',
            'waste_pct',
            'price_per_purchase_unit',
            'is_active',
            'created_at',
            'updated_at',
        ]


class MaterialCatalogItemWriteSerializer(serializers.ModelSerializer):
    """Serializer optimizado para operaciones de creación y edición (CRUD) en el catálogo maestro."""
    class Meta:
        model = MaterialCatalogItem
        fields = [
            'id',
            'subcategory',
            'name',
            'description',
            'unit_measure',
            'unit_purchase',
            'conversion_factor',
            'weight_per_purchase_unit',
            'waste_pct',
            'price_per_purchase_unit',
            'is_active',
        ]


# Alias por defecto para compatibilidad
MaterialCatalogItemSerializer = MaterialCatalogItemReadSerializer
