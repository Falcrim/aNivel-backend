from django.contrib import admin
from .models import MaterialCatalogItem


@admin.register(MaterialCatalogItem)
class MaterialCatalogItemAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'subcategory',
        'supplier',
        'unit_purchase',
        'conversion_factor',
        'unit_measure',
        'price_per_purchase_unit',
        'waste_pct',
        'is_active',
    )
    list_filter = ('subcategory', 'supplier', 'is_active', 'unit_purchase', 'unit_measure')
    search_fields = ('name', 'description', 'subcategory__name', 'supplier__name')
