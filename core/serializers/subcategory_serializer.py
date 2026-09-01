from rest_framework import serializers
from core.models import Subcategory, Category


class SubcategoryCategorySimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']


class SubcategorySerializer(serializers.ModelSerializer):
    category_detail = SubcategoryCategorySimpleSerializer(source='category', read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'category', 'category_detail', 'name']
