from django.contrib import admin
from .models import MaterialCatalogItem, MaterialBudgetItem


@admin.register(MaterialCatalogItem)
class MaterialCatalogItemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'subcategory',
        'unit_purchase',
        'conversion_factor',
        'unit_measure',
        'price_per_purchase_unit',
        'waste_pct',
        'is_active',
    )
    list_filter = ('subcategory', 'is_active', 'unit_purchase', 'unit_measure')
    search_fields = ('name', 'description', 'subcategory__name')


@admin.register(MaterialBudgetItem)
class MaterialBudgetItemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'project',
        'subcategory',
        'is_global',
        'quantity_obra',
        'waste_pct',
        'quantity_purchase',
        'unit_purchase',
        'price_per_purchase_unit',
        'estimated_cost',
    )
    list_filter = ('project', 'subcategory', 'is_global', 'unit_purchase')
    search_fields = ('name', 'detail', 'project__name', 'subcategory__name')
    readonly_fields = ('quantity_purchase', 'estimated_cost', 'weight_total')
