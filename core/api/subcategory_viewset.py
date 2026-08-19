from rest_framework import viewsets

from core.models import Subcategory
from core.serializers.subcategory_serializer import SubcategorySerializer


class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.select_related('category').all()
    serializer_class = SubcategorySerializer