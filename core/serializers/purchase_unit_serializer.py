from rest_framework import serializers
from core.models import PurchaseUnit


class PurchaseUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseUnit
        fields = ['id', 'name', 'abbreviation']
