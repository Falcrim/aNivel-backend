from decimal import Decimal
from rest_framework import serializers
from core.models import Project, Subcategory, UnitOfMeasure
from labor.models import LaborCatalogItem


class FromLaborCatalogActionSerializer(serializers.Serializer):
    """Payload para agregar una tarea desde el catálogo al presupuesto de obra."""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    catalog_item = serializers.PrimaryKeyRelatedField(queryset=LaborCatalogItem.objects.all())
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=Decimal('0'))
    cost_override = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True, default=None)
    contractor_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    detail = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all(), required=False, allow_null=True, default=None)


class CustomLaborBudgetItemActionSerializer(serializers.Serializer):
    """Payload para crear una tarea de mano de obra ad-hoc directamente en obra sin catálogo."""
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all())
    name = serializers.CharField(max_length=255)
    unit = serializers.PrimaryKeyRelatedField(queryset=UnitOfMeasure.objects.all())
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4, min_value=Decimal('0'))
    unit_cost = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal('0'))
    contractor_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    detail = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
