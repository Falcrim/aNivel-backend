from rest_framework import viewsets

from core.models import Category
from core.serializers.category_serializer import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer