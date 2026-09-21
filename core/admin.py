from django.contrib import admin
from .models import (
    Project,
    Category,
    Subcategory,
    UnitOfMeasure,
    PurchaseUnit,
    ProjectDocument,
    ProjectExpense,
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


@admin.register(ProjectDocument)
class ProjectDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'document_type', 'supplier_name', 'quoted_amount', 'currency', 'created_at')
    list_filter = ('document_type', 'currency', 'project')
    search_fields = ('title', 'supplier_name', 'file_name', 'project__name')
    date_hierarchy = 'created_at'


@admin.register(ProjectExpense)
class ProjectExpenseAdmin(admin.ModelAdmin):
    list_display = (
        'item_name',
        'project',
        'category_type',
        'quantity',
        'unit_name',
        'unit_price',
        'total_price',
        'payment_status',
        'expense_date',
        'rendicion_number',
    )
    list_filter = ('category_type', 'payment_status', 'project', 'rendicion_number')
    search_fields = ('item_name', 'supplier_name', 'details', 'rendicion_number')
    date_hierarchy = 'expense_date'