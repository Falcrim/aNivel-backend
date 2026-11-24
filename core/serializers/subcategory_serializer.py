from rest_framework import serializers
from core.models import Subcategory, Category


class SubcategoryCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'code', 'name', 'is_active']


class SubcategorySerializer(serializers.ModelSerializer):
    category_detail = SubcategoryCategorySimpleSerializer(source='category', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'category', 'category_detail', 'category_name', 'name']
