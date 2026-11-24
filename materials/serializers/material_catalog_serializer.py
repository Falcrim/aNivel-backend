from rest_framework import serializers
from core.serializers import SubcategorySerializer, UnitOfMeasureSerializer, PurchaseUnitSerializer
from materials.models import MaterialCatalogItem


class MaterialCatalogItemReadSerializer(serializers.ModelSerializer):
    """Serializer optimizado para lectura y consulta del catálogo maestro con relaciones expandidas."""
    subcategory_detail = SubcategorySerializer(source='subcategory', read_only=True)
    unit_measure_detail = UnitOfMeasureSerializer(source='unit_measure', read_only=True)
    unit_purchase_detail = PurchaseUnitSerializer(source='unit_purchase', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, default=None)
    supplier_photo_url = serializers.CharField(source='supplier.photo_url', read_only=True, default=None)

    class Meta:
        model = MaterialCatalogItem
        fields = [
            'id',
            'subcategory',
            'subcategory_detail',
            'supplier',
            'supplier_name',
            'supplier_photo_url',
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
            'supplier',
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
