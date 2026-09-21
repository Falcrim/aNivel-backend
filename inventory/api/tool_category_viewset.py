from rest_framework import viewsets, permissions, filters
from inventory.models.tool_category import ToolCategory
from inventory.serializers.tool_category_serializer import ToolCategorySerializer


class ToolCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD de categorías de herramientas y equipos.
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ToolCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return ToolCategory.objects.prefetch_related('tools').all()
