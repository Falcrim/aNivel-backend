from django.contrib import admin
from labor.models import LaborCatalogItem


@admin.register(LaborCatalogItem)
class LaborCatalogItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'subcategory', 'supplier', 'unit', 'suggested_cost', 'contractor_type', 'is_active']
    list_filter = ['subcategory', 'supplier', 'is_active', 'contractor_type']
    search_fields = ['name', 'detail', 'contractor_type', 'supplier__name']
