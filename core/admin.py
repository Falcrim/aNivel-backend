from django.contrib import admin
from .models import (
    Project,
    Category,
    Subcategory,
    UnitOfMeasure,
    PurchaseUnit,
    Supplier,
    ConstructionStage,
    BudgetItem,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'built_area', 'exchange_rate')
    search_fields = ('name',)
    list_filter = ('status',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Subcategory)
class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')


@admin.register(PurchaseUnit)
class PurchaseUnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'supplier_type', 'contact_name', 'phone', 'is_active')
    list_filter = ('supplier_type', 'is_active')
    search_fields = ('name', 'contact_name', 'phone', 'email')


@admin.register(ConstructionStage)
class ConstructionStageAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'category_type', 'stage', 'subcategory', 'supplier', 'unit_price')
    list_filter = ('project', 'category_type', 'stage', 'subcategory')
    search_fields = ('name', 'detail', 'contractor_name', 'project__name')
