from decimal import Decimal
from django.db import transaction
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import BudgetItem, BudgetCategoryType, Project, Subcategory, ConstructionStage
from core.serializers.budget_item_serializer import (
    BudgetItemReadSerializer,
    BudgetItemWriteSerializer,
    BudgetItemGroupedSerializer,
)
from core.services.budget_calculation_service import BudgetCalculationService


class BudgetItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet unificado para la gestión y consulta de partidas presupuestarias.
    Permite filtrar por proyecto, etapa constructiva, subcategoría, proveedor y familia de costo.
    """
    queryset = BudgetItem.objects.with_relations()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'detail', 'contractor_name', 'subcategory__name']
    ordering_fields = ['order', 'name', 'unit_price', 'created_at']
    ordering = ['order', 'name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BudgetItemWriteSerializer
        return BudgetItemReadSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        project_id = self.request.query_params.get('project') or self.request.query_params.get('project_id')
        if project_id:
            qs = qs.filter(project_id=project_id)

        category_type = self.request.query_params.get('category_type')
        if category_type:
            qs = qs.filter(category_type=category_type.lower())

        stage_id = self.request.query_params.get('stage') or self.request.query_params.get('stage_id')
        if stage_id:
            qs = qs.filter(stage_id=stage_id)

        subcategory_id = self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id')
        if subcategory_id:
            qs = qs.filter(subcategory_id=subcategory_id)

        supplier_id = self.request.query_params.get('supplier') or self.request.query_params.get('supplier_id')
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)

        return qs

    def paginate_queryset(self, queryset):
        # Permite bypass de paginación para clientes que necesitan listas completas
        if self.request.query_params.get('paginate') == 'false':
            return None
        return super().paginate_queryset(queryset)

    @action(detail=False, methods=['get'], url_path='by-project')
    def by_project(self, request):
        """
        Retorna las partidas agrupadas por subcategoría para alimentar
        el componente acordeón del frontend, con subtotales y resumen de unidades comerciales.
        """
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': "El parámetro 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        category_type = request.query_params.get('category_type')
        grouped_data = BudgetCalculationService.get_project_budget_grouped_by_subcategory(
            project_id=int(project_id),
            category_type=category_type
        )
        serializer = BudgetItemGroupedSerializer(grouped_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='by-stage')
    def by_stage(self, request):
        """
        Retorna las partidas organizadas en jerarquía de 2 niveles:
        Etapa Constructiva -> Subcategorías -> Partidas.
        Incluye métricas analíticas por etapa (% de familia, $/m2, Bs, $).
        """
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': "El parámetro 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        category_type = request.query_params.get('category_type')
        grouped_data = BudgetCalculationService.get_project_budget_grouped_by_stage(
            project_id=int(project_id),
            category_type=category_type
        )
        return Response(grouped_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Retorna el resumen financiero consolidado por familias de costo de la obra."""
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {'error': "El parámetro 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        summary_data = BudgetCalculationService.get_project_budget_summary(project_id=int(project_id))
        return Response(summary_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='from-catalog')
    @transaction.atomic
    def from_catalog(self, request):
        """
        Instancia una partida de presupuesto a partir de un ítem de catálogo
        (de Materiales o Mano de Obra), heredando sus especificaciones y proveedor.
        """
        project_id = request.data.get('project')
        catalog_type = request.data.get('catalog_type', 'materials').lower()
        catalog_id = request.data.get('catalog_id')
        stage_id = request.data.get('stage')
        subcategory_id = request.data.get('subcategory')
        quantity_obra = request.data.get('quantity_obra')
        quantity_purchase = request.data.get('quantity_purchase')
        price_override = request.data.get('price_override')
        waste_pct = request.data.get('waste_pct')
        contractor_name = request.data.get('contractor_name')
        detail = request.data.get('detail', '')
        apply_ceil = request.data.get('apply_ceil', True)
        is_global = request.data.get('is_global', False)

        if not project_id or not catalog_id:
            return Response(
                {'error': "Los campos 'project' y 'catalog_id' son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        project = Project.objects.filter(id=project_id).first()
        if not project:
            return Response({'error': "Proyecto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        subcat_override = Subcategory.objects.filter(id=subcategory_id).first() if subcategory_id else None

        if catalog_type == 'materials':
            from materials.models import MaterialCatalogItem
            catalog_item = MaterialCatalogItem.objects.select_related(
                'subcategory', 'supplier', 'unit_measure', 'unit_purchase'
            ).filter(id=catalog_id).first()
            if not catalog_item:
                return Response({'error': "Ítem de catálogo de materiales no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            unit_price = Decimal(str(price_override)) if price_override is not None else catalog_item.price_per_purchase_unit
            effective_waste = Decimal(str(waste_pct)) if waste_pct is not None else (catalog_item.waste_pct or Decimal('0.0000'))

            item = BudgetItem(
                project=project,
                category_type=BudgetCategoryType.MATERIALS,
                stage_id=stage_id,
                subcategory=subcat_override or catalog_item.subcategory,
                supplier=catalog_item.supplier,
                name=catalog_item.name,
                detail=detail or catalog_item.description or '',
                is_global=is_global,
                apply_ceil=apply_ceil,
                unit_measure=catalog_item.unit_measure,
                quantity_obra=Decimal(str(quantity_obra)) if (quantity_obra is not None and not is_global) else None,
                quantity_purchase=Decimal(str(quantity_purchase)) if (quantity_purchase is not None and is_global) else Decimal('0.0000'),
                unit_purchase=catalog_item.unit_purchase,
                conversion_factor=catalog_item.conversion_factor or Decimal('1.0000'),
                waste_pct=effective_waste,
                unit_price=unit_price or Decimal('0.00'),
                weight_per_purchase_unit=catalog_item.weight_per_purchase_unit,
                catalog_reference_id=catalog_item.id,
            )
            item.save()
            return Response(BudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

        elif catalog_type == 'labor':
            from labor.models import LaborCatalogItem
            catalog_item = LaborCatalogItem.objects.select_related(
                'subcategory', 'supplier', 'unit'
            ).filter(id=catalog_id).first()
            if not catalog_item:
                return Response({'error': "Ítem de catálogo de mano de obra no encontrado."}, status=status.HTTP_404_NOT_FOUND)

            unit_price = Decimal(str(price_override)) if price_override is not None else (catalog_item.suggested_cost or Decimal('0.00'))

            item = BudgetItem(
                project=project,
                category_type=BudgetCategoryType.LABOR,
                stage_id=stage_id,
                subcategory=subcat_override or catalog_item.subcategory,
                supplier=catalog_item.supplier,
                contractor_name=contractor_name if contractor_name is not None else (catalog_item.contractor_type or ''),
                name=catalog_item.name,
                detail=detail or catalog_item.detail or '',
                is_global=is_global,
                apply_ceil=False,
                unit_measure=catalog_item.unit,
                quantity_obra=Decimal(str(quantity_obra)) if quantity_obra is not None else Decimal('1.0000'),
                unit_purchase=None,
                conversion_factor=Decimal('1.0000'),
                waste_pct=Decimal('0.0000'),
                unit_price=unit_price,
                catalog_reference_id=catalog_item.id,
            )
            item.save()
            return Response(BudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

        return Response(
            {'error': f"Tipo de catálogo '{catalog_type}' no soportado."},
            status=status.HTTP_400_BAD_REQUEST
        )
