from django.contrib import admin
from labor.models import LaborCatalogItem, LaborBudgetItem


@admin.register(LaborCatalogItem)
class LaborCatalogItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'subcategory', 'unit', 'suggested_cost', 'contractor_type', 'is_active']
    list_filter = ['subcategory', 'is_active', 'contractor_type']
    search_fields = ['name', 'detail', 'contractor_type']


@admin.register(LaborBudgetItem)
class LaborBudgetItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'subcategory', 'contractor_name', 'unit', 'quantity', 'unit_cost', 'estimated_cost']
    list_filter = ['project', 'subcategory', 'contractor_name']
    search_fields = ['name', 'detail', 'contractor_name', 'project__name']
