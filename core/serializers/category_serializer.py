from rest_framework import serializers
from core.models import Category


class CategorySubcategoryInlineSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class CategorySerializer(serializers.ModelSerializer):
    subcategories_count = serializers.SerializerMethodField()
    subcategories = CategorySubcategoryInlineSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'subcategories_count', 'subcategories']

    def get_subcategories_count(self, obj) -> int:
        if hasattr(obj, 'subcategories_count'):
            return obj.subcategories_count
        return obj.subcategories.count()