from rest_framework import serializers
from inventory.models.tool_category import ToolCategory


class ToolCategorySerializer(serializers.ModelSerializer):
    tools_count = serializers.SerializerMethodField()

    def get_tools_count(self, obj) -> int:
        return obj.tools.filter(is_active=True).count()

    class Meta:
        model = ToolCategory
        fields = [
            'id',
            'name',
            'description',
            'tools_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']
