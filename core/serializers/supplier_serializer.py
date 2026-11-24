from rest_framework import serializers
from core.models.supplier import Supplier, SupplierType


class SupplierSerializer(serializers.ModelSerializer):
    supplier_type_display = serializers.CharField(source='get_supplier_type_display', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id',
            'name',
            'supplier_type',
            'supplier_type_display',
            'contact_name',
            'phone',
            'email',
            'address',
            'photo',
            'photo_url',
            'notes',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'supplier_type_display', 'photo_url', 'created_at', 'updated_at']

    def get_photo_url(self, obj: Supplier) -> str | None:
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None
