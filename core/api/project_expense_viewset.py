from decimal import Decimal
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from core.models import ProjectExpense, ExpenseCategoryType, PaymentStatus
from core.serializers import ProjectExpenseSerializer


class ProjectExpenseViewSet(viewsets.ModelViewSet):
    """
    CRUD para compras, gastos reales y pagos ejecutados en una obra concreta.
    Optimizado con select_related y endpoints de resumen para rendición.
    """
    queryset = ProjectExpense.objects.all().select_related('project', 'subcategory', 'subcategory__category')
    serializer_class = ProjectExpenseSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['item_name', 'supplier_name', 'receipt_number', 'details', 'rendicion_number']
    ordering_fields = ['expense_date', 'total_price', 'created_at', 'item_name']
    ordering = ['-expense_date', '-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        project_id = params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        cat_type = params.get('category_type')
        if cat_type:
            qs = qs.filter(category_type=cat_type)

        subcat_id = params.get('subcategory')
        if subcat_id:
            qs = qs.filter(subcategory_id=subcat_id)

        pay_status = params.get('payment_status')
        if pay_status:
            qs = qs.filter(payment_status=pay_status)

        rendicion = params.get('rendicion_number')
        if rendicion:
            qs = qs.filter(rendicion_number=rendicion)

        return qs

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Retorna totales y métricas de gastos reales por categoría y estado de pago.
        Uso: GET /api/core/project-expenses/summary/?project=1
        """
        project_id = request.query_params.get('project')
        if not project_id:
            return Response(
                {"error": "El parámetro 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = ProjectExpense.objects.filter(project_id=project_id)

        agg = qs.aggregate(
            total_count=Count('id'),
            total_amount=Sum('total_price'),
            paid_amount=Sum('total_price', filter=Q(payment_status=PaymentStatus.PAID)),
            in_process_amount=Sum('total_price', filter=Q(payment_status=PaymentStatus.IN_PROCESS)),
            pending_amount=Sum('total_price', filter=Q(payment_status=PaymentStatus.PENDING)),
            materials_amount=Sum('total_price', filter=Q(category_type=ExpenseCategoryType.MATERIALS)),
            labor_amount=Sum('total_price', filter=Q(category_type=ExpenseCategoryType.LABOR)),
            operating_amount=Sum('total_price', filter=Q(category_type=ExpenseCategoryType.OPERATING)),
            administrative_amount=Sum('total_price', filter=Q(category_type=ExpenseCategoryType.ADMINISTRATIVE)),
            receipts_count=Count('id', filter=Q(receipt_file__isnull=False) & ~Q(receipt_file='')),
        )

        rendiciones = list(
            qs.exclude(rendicion_number='')
            .values_list('rendicion_number', flat=True)
            .distinct()
            .order_by('rendicion_number')
        )

        return Response({
            "project_id": int(project_id),
            "total_count": agg['total_count'] or 0,
            "total_amount": float(agg['total_amount'] or Decimal('0.00')),
            "paid_amount": float(agg['paid_amount'] or Decimal('0.00')),
            "in_process_amount": float(agg['in_process_amount'] or Decimal('0.00')),
            "pending_amount": float(agg['pending_amount'] or Decimal('0.00')),
            "materials_amount": float(agg['materials_amount'] or Decimal('0.00')),
            "labor_amount": float(agg['labor_amount'] or Decimal('0.00')),
            "operating_amount": float(agg['operating_amount'] or Decimal('0.00')),
            "administrative_amount": float(agg['administrative_amount'] or Decimal('0.00')),
            "receipts_count": agg['receipts_count'] or 0,
            "rendiciones": rendiciones,
        })
