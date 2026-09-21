from rest_framework import serializers
from core.serializers import ProjectSerializer, SubcategorySerializer, UnitOfMeasureSerializer
from labor.models import LaborBudgetItem
from .labor_catalog_serializer import LaborCatalogItemReadSerializer


class LaborBudgetItemReadSerializer(serializers.ModelSerializer):
    """Serializer optimizado para lectura y consulta del presupuesto de mano de obra."""
    project_detail = ProjectSerializer(source='project', read_only=True)
    subcategory_detail = SubcategorySerializer(source='subcategory', read_only=True)
    unit_detail = UnitOfMeasureSerializer(source='unit', read_only=True)
    catalog_item_detail = LaborCatalogItemReadSerializer(source='catalog_item', read_only=True)

    estimated_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = LaborBudgetItem
        fields = [
            'id',
            'project',
            'project_detail',
            'catalog_item',
            'catalog_item_detail',
            'subcategory',
            'subcategory_detail',
            'contractor_name',
            'name',
            'detail',
            'unit',
            'unit_detail',
            'quantity',
            'unit_cost',
            'estimated_cost',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['estimated_cost', 'created_at', 'updated_at']


class LaborBudgetItemWriteSerializer(serializers.ModelSerializer):
    """Serializer para operaciones de modificación directa (PUT/PATCH) de líneas de mano de obra."""
    class Meta:
        model = LaborBudgetItem
        fields = [
            'id',
            'project',
            'catalog_item',
            'subcategory',
            'contractor_name',
            'name',
            'detail',
            'unit',
            'quantity',
            'unit_cost',
        ]


LaborBudgetItemSerializer = LaborBudgetItemReadSerializer
