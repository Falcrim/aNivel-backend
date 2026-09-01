from decimal import Decimal
from rest_framework import serializers
from core.models import Project, Subcategory, UnitOfMeasure, PurchaseUnit
from materials.models import MaterialCatalogItem


class FromCatalogActionSerializer(serializers.Serializer):
    """Payload para agregar un ítem normal desde el catálogo al presupuesto."""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    catalog_item = serializers.PrimaryKeyRelatedField(queryset=MaterialCatalogItem.objects.all())
    quantity_obra = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=Decimal('0'))
    detail = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    waste_pct = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, allow_null=True, default=None)
    price_override = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True, default=None)
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all(), required=False, allow_null=True, default=None)


class FromCatalogGlobalActionSerializer(serializers.Serializer):
    """Payload para agregar un ítem global/paquete cerrado desde el catálogo."""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    catalog_item = serializers.PrimaryKeyRelatedField(queryset=MaterialCatalogItem.objects.all())
    quantity_purchase = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=Decimal('0.0001'))
    price_per_purchase_unit = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True, default=None)
    detail = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all(), required=False, allow_null=True, default=None)


class CustomBudgetItemActionSerializer(serializers.Serializer):
    """Payload para crear un ítem de presupuesto ad-hoc directamente en obra sin catálogo."""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all())
    name = serializers.CharField(max_length=255)
    unit_measure = serializers.PrimaryKeyRelatedField(queryset=UnitOfMeasure.objects.all())
    unit_purchase = serializers.PrimaryKeyRelatedField(queryset=PurchaseUnit.objects.all())
    price_per_purchase_unit = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0'))
    is_global = serializers.BooleanField(default=False)
    quantity_obra = serializers.DecimalField(max_digits=15, decimal_places=4, required=False, allow_null=True, default=None)
    quantity_purchase = serializers.DecimalField(max_digits=15, decimal_places=4, required=False, allow_null=True, default=None)
    conversion_factor = serializers.DecimalField(max_digits=10, decimal_places=4, required=False, allow_null=True, default=None)
    weight_per_purchase_unit = serializers.DecimalField(max_digits=10, decimal_places=4, required=False, allow_null=True, default=None)
    waste_pct = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, default=Decimal('0'))
    detail = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
