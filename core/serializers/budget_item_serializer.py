from decimal import Decimal
from rest_framework import serializers
from core.models import BudgetItem, BudgetCategoryType


class BudgetItemReadSerializer(serializers.ModelSerializer):
    """Serializer detallado para lectura de partidas de presupuesto unificadas."""
    project_name = serializers.CharField(source='project.name', read_only=True)
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    
    stage_id = serializers.IntegerField(source='stage.id', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    stage_color = serializers.CharField(source='stage.color', read_only=True)

    subcategory_id = serializers.IntegerField(source='subcategory.id', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    category_name = serializers.CharField(source='subcategory.category.name', read_only=True)

    supplier_id = serializers.IntegerField(source='supplier.id', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_phone = serializers.CharField(source='supplier.phone', read_only=True)

    unit_measure_name = serializers.CharField(source='unit_measure.name', read_only=True)
    unit_measure_abbr = serializers.CharField(source='unit_measure.abbreviation', read_only=True)

    unit_purchase_name = serializers.CharField(source='unit_purchase.name', read_only=True)
    unit_purchase_abbr = serializers.CharField(source='unit_purchase.abbreviation', read_only=True)

    # Métricas calculadas por la estrategia activa (DDD)
    estimated_cost = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    weight_total = serializers.DecimalField(max_digits=15, decimal_places=4, read_only=True)
    cost_usd = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    cost_per_m2_usd = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = BudgetItem
        fields = [
            'id',
            'project',
            'project_name',
            'category_type',
            'category_type_display',
            'stage',
            'stage_id',
            'stage_name',
            'stage_color',
            'subcategory',
            'subcategory_id',
            'subcategory_name',
            'category_name',
            'supplier',
            'supplier_id',
            'supplier_name',
            'supplier_phone',
            'name',
            'detail',
            'is_global',
            'apply_ceil',
            'unit_measure',
            'unit_measure_name',
            'unit_measure_abbr',
            'quantity_obra',
            'unit_purchase',
            'unit_purchase_name',
            'unit_purchase_abbr',
            'conversion_factor',
            'waste_pct',
            'quantity_purchase',
            'unit_price',
            'weight_per_purchase_unit',
            'contractor_name',
            'percentage_applied',
            'target_base_cost',
            'notes',
            'catalog_reference_id',
            'order',
            'estimated_cost',
            'weight_total',
            'cost_usd',
            'cost_per_m2_usd',
            'created_at',
            'updated_at',
        ]


class BudgetItemWriteSerializer(serializers.ModelSerializer):
    """Serializer para creación, edición y reasignación de partidas presupuestarias."""

    class Meta:
        model = BudgetItem
        fields = [
            'id',
            'project',
            'category_type',
            'stage',
            'subcategory',
            'supplier',
            'name',
            'detail',
            'is_global',
            'apply_ceil',
            'unit_measure',
            'quantity_obra',
            'unit_purchase',
            'conversion_factor',
            'waste_pct',
            'quantity_purchase',
            'unit_price',
            'weight_per_purchase_unit',
            'contractor_name',
            'percentage_applied',
            'target_base_cost',
            'notes',
            'catalog_reference_id',
            'order',
        ]

    def validate(self, attrs):
        # Instanciar o simular validación limpia de la estrategia
        instance = self.instance or BudgetItem(**attrs)
        for attr, value in attrs.items():
            setattr(instance, attr, value)
        
        errors = instance.strategy.validate(instance)
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class BudgetItemGroupedSerializer(serializers.Serializer):
    """Serializer para visualización agrupada tipo acordeón por subcategoría."""
    subcategory_id = serializers.IntegerField(allow_null=True)
    subcategory_name = serializers.CharField()
    category_name = serializers.CharField()
    items_count = serializers.IntegerField()
    subtotal_cost_bs = serializers.CharField()
    subtotal_cost_usd = serializers.CharField()
    subtotal_weight_kg = serializers.CharField()
    total_purchase_units_summary = serializers.CharField()
    items = BudgetItemReadSerializer(many=True)
