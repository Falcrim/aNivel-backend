from decimal import Decimal
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from core.models import ProjectDocument, DocumentType
from core.serializers import ProjectDocumentSerializer


class ProjectDocumentViewSet(viewsets.ModelViewSet):
    """
    CRUD y gestión de documentos, cotizaciones y comprobantes de obras.
    Optimizado con select_related para evitar N+1 queries.
    """
    queryset = ProjectDocument.objects.all().select_related('project', 'subcategory')
    serializer_class = ProjectDocumentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'file_name', 'supplier_name', 'notes']
    ordering_fields = ['created_at', 'title', 'file_size', 'quoted_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)

        document_type = self.request.query_params.get('document_type')
        if document_type:
            qs = qs.filter(document_type=document_type)

        subcategory_id = self.request.query_params.get('subcategory')
        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)

        return qs

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Retorna métricas resumidas de los documentos de una obra concreta.
        Uso: GET /api/core/project-documents/summary/?project=1
        """
        project_id = request.query_params.get('project')
        if not project_id:
            return Response(
                {"error": "El parámetro 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = ProjectDocument.objects.filter(project_id=project_id)

        # Agregaciones eficientes en una sola consulta
        agg = qs.aggregate(
            total_docs=Count('id'),
            quotations_count=Count('id', filter=Q(document_type=DocumentType.QUOTATION)),
            technical_sheets_count=Count('id', filter=Q(document_type=DocumentType.TECHNICAL_SHEET)),
            blueprints_count=Count('id', filter=Q(document_type=DocumentType.BLUEPRINT)),
            others_count=Count('id', filter=Q(document_type=DocumentType.OTHER)),
            total_quoted_bob=Sum('quoted_amount', filter=Q(currency='BOB')),
            total_quoted_usd=Sum('quoted_amount', filter=Q(currency='USD')),
        )

        return Response({
            "project_id": int(project_id),
            "total_documents": agg['total_docs'] or 0,
            "quotations_count": agg['quotations_count'] or 0,
            "technical_sheets_count": agg['technical_sheets_count'] or 0,
            "blueprints_count": agg['blueprints_count'] or 0,
            "others_count": agg['others_count'] or 0,
            "total_quoted_bob": float(agg['total_quoted_bob'] or Decimal('0.00')),
            "total_quoted_usd": float(agg['total_quoted_usd'] or Decimal('0.00')),
        })
