from rest_framework import serializers
from core.serializers import (
    ProjectSerializer,
    SubcategorySerializer,
    UnitOfMeasureSerializer,
    PurchaseUnitSerializer,
)
from materials.models import MaterialBudgetItem
from materials.serializers.material_catalog_serializer import MaterialCatalogItemReadSerializer


class MaterialBudgetItemReadSerializer(serializers.ModelSerializer):
    """Serializer optimizado para lectura y consulta del presupuesto con relaciones expandidas."""
    project_detail = ProjectSerializer(source='project', read_only=True)
    subcategory_detail = SubcategorySerializer(source='subcategory', read_only=True)
    unit_measure_detail = UnitOfMeasureSerializer(source='unit_measure', read_only=True)
    unit_purchase_detail = PurchaseUnitSerializer(source='unit_purchase', read_only=True)
    catalog_item_detail = MaterialCatalogItemReadSerializer(source='catalog_item', read_only=True)

    weight_total = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    estimated_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MaterialBudgetItem
        fields = [
            'id',
            'project',
            'project_detail',
            'catalog_item',
            'catalog_item_detail',
            'subcategory',
            'subcategory_detail',
            'name',
            'detail',
            'is_global',
            'unit_measure',
            'unit_measure_detail',
            'unit_purchase',
            'unit_purchase_detail',
            'conversion_factor',
            'weight_per_purchase_unit',
            'waste_pct',
            'quantity_obra',
            'quantity_purchase',
            'price_per_purchase_unit',
            'weight_total',
            'estimated_cost',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['weight_total', 'estimated_cost', 'created_at', 'updated_at']


class MaterialBudgetItemWriteSerializer(serializers.ModelSerializer):
    """Serializer optimizado para operaciones de modificación directa (PUT/PATCH) de líneas de presupuesto."""
    class Meta:
        model = MaterialBudgetItem
        fields = [
            'id',
            'project',
            'catalog_item',
            'subcategory',
            'name',
            'detail',
            'is_global',
            'unit_measure',
            'unit_purchase',
            'conversion_factor',
            'weight_per_purchase_unit',
            'waste_pct',
            'quantity_obra',
            'quantity_purchase',
            'price_per_purchase_unit',
        ]
        extra_kwargs = {
            'quantity_purchase': {'required': False},  # Se calcula automáticamente en ítems no globales
        }


# Alias por defecto para compatibilidad
MaterialBudgetItemSerializer = MaterialBudgetItemReadSerializer
