import os
from decimal import Decimal
from rest_framework import serializers
from core.models import ProjectExpense, ExpenseCategoryType, PaymentStatus
from .project_document_serializer import format_file_size

ALLOWED_RECEIPT_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp', 'doc', 'docx', 'xlsx', 'xls'}
MAX_RECEIPT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class ProjectExpenseSerializer(serializers.ModelSerializer):
    category_type_display = serializers.CharField(source='get_category_type_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True, default='')
    receipt_file_url = serializers.SerializerMethodField()
    receipt_file_size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ProjectExpense
        fields = [
            'id',
            'project',
            'project_name',
            'category_type',
            'category_type_display',
            'subcategory',
            'subcategory_name',
            'item_name',
            'unit_name',
            'quantity',
            'unit_price',
            'total_price',
            'payment_status',
            'payment_status_display',
            'expense_date',
            'payment_method',
            'supplier_name',
            'details',
            'rendicion_number',
            'receipt_file',
            'receipt_file_url',
            'receipt_number',
            'receipt_file_name',
            'receipt_file_size',
            'receipt_file_size_formatted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'category_type_display',
            'payment_status_display',
            'project_name',
            'subcategory_name',
            'receipt_file_url',
            'receipt_file_name',
            'receipt_file_size',
            'receipt_file_size_formatted',
            'created_at',
            'updated_at',
        ]

    def get_receipt_file_url(self, obj: ProjectExpense) -> str:
        if not obj.receipt_file:
            return ''
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.receipt_file.url)
        return obj.receipt_file.url

    def get_receipt_file_size_formatted(self, obj: ProjectExpense) -> str:
        return format_file_size(obj.receipt_file_size)

    def validate_receipt_file(self, value):
        if not value:
            return value

        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if ext not in ALLOWED_RECEIPT_EXTENSIONS:
            allowed = ', '.join(sorted(ALLOWED_RECEIPT_EXTENSIONS))
            raise serializers.ValidationError(
                f"Formato .{ext} no permitido para comprobante. Formatos válidos: {allowed}."
            )

        if value.size > MAX_RECEIPT_SIZE_BYTES:
            raise serializers.ValidationError(
                f"El comprobante supera los 25 MB ({format_file_size(value.size)})."
            )

        return value

    def create(self, validated_data):
        receipt = validated_data.get('receipt_file')
        if receipt:
            validated_data['receipt_file_name'] = receipt.name
            validated_data['receipt_file_size'] = receipt.size

        # Auto calcular total si no fue provisto
        qty = validated_data.get('quantity', Decimal('1.00'))
        price = validated_data.get('unit_price', Decimal('0.00'))
        if not validated_data.get('total_price') and qty and price:
            validated_data['total_price'] = (qty * price).quantize(Decimal('0.01'))

        return super().create(validated_data)

    def update(self, instance, validated_data):
        receipt = validated_data.get('receipt_file')
        if receipt:
            # Si reemplaza comprobante, borrar el anterior
            if instance.receipt_file and instance.receipt_file.storage.exists(instance.receipt_file.name):
                instance.receipt_file.delete(save=False)
            validated_data['receipt_file_name'] = receipt.name
            validated_data['receipt_file_size'] = receipt.size

        qty = validated_data.get('quantity', instance.quantity)
        price = validated_data.get('unit_price', instance.unit_price)
        if 'total_price' not in validated_data and qty and price:
            validated_data['total_price'] = (qty * price).quantize(Decimal('0.01'))

        return super().update(instance, validated_data)
