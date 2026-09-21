from django.contrib import admin
from inventory.models.location import Location
from inventory.models.tool_category import ToolCategory
from inventory.models.tool import Tool
from inventory.models.tool_transfer import ToolTransfer


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location_type', 'project', 'is_active', 'created_at')
    list_filter = ('location_type', 'is_active')
    search_fields = ('name', 'code', 'address', 'project__name')
    ordering = ('name',)


@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'current_location', 'status', 'brand', 'is_active')
    list_filter = ('status', 'category', 'current_location__location_type', 'is_active')
    search_fields = ('code', 'name', 'brand', 'model_name', 'serial_number', 'detail')
    ordering = ('name',)


@admin.register(ToolTransfer)
class ToolTransferAdmin(admin.ModelAdmin):
    list_display = ('tool', 'origin_location', 'destination_location', 'transfer_date', 'responsible_person', 'created_by')
    list_filter = ('transfer_date', 'destination_location__location_type')
    search_fields = ('tool__name', 'tool__code', 'responsible_person', 'notes')
    ordering = ('-transfer_date',)
    readonly_fields = ('transfer_date', 'created_at', 'updated_at')
