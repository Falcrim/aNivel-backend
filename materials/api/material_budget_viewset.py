from decimal import Decimal
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Project
from materials.models import MaterialBudgetItem
from materials.serializers import (
    MaterialBudgetItemReadSerializer,
    MaterialBudgetItemWriteSerializer,
    FromCatalogActionSerializer,
    FromCatalogGlobalActionSerializer,
    CustomBudgetItemActionSerializer,
)
from materials.services import MaterialBudgetService, MaterialBudgetMetricsService


class MaterialBudgetItemViewSet(viewsets.ModelViewSet):
    """
    CRUD completo y operaciones especializadas para el Presupuesto de Materiales por Obra.
    
    Filtros soportados en listado:
    - Por proyecto/obra: ?project=1 o ?project_id=1
    - Por subcategoría: ?subcategory=1 o ?subcategory_id=1
    - Por tipo (global/normal): ?is_global=true o ?is_global=false
    - Búsqueda: ?search=fierro
    - Ordenamiento: ?ordering=subcategory__name,name o ?ordering=-price_per_purchase_unit
    """
    queryset = MaterialBudgetItem.objects.with_relations()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'detail', 'subcategory__name', 'project__name']
    ordering_fields = ['subcategory__name', 'name', 'price_per_purchase_unit', 'quantity_purchase']
    ordering = ['subcategory__name', 'name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MaterialBudgetItemWriteSerializer
        return MaterialBudgetItemReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        project_id = self.request.query_params.get('project') or self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.for_project(project_id)

        subcategory_id = self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id')
        if subcategory_id:
            queryset = queryset.for_subcategory(subcategory_id)

        is_global = self.request.query_params.get('is_global')
        if is_global is not None:
            if is_global.lower() in ['true', '1']:
                queryset = queryset.global_items()
            else:
                queryset = queryset.standard_items()

        return queryset

    # -------------------------------------------------------------------
    # ENDPOINTS DE CREACIÓN ESPECÍFICA (Delega a MaterialBudgetService)
    # -------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='from-catalog')
    def from_catalog(self, request):
        """
        Crea una línea de presupuesto NORMAL desde un ítem del catálogo.
        Calcula la cantidad de compra con redondeo hacia arriba a partir de quantity_obra.
        Endpoint: POST /api/materials/budget/from-catalog/
        """
        serializer = FromCatalogActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        item = MaterialBudgetService.create_from_catalog(
            project=validated_data['project'],
            catalog_item=validated_data['catalog_item'],
            quantity_obra=validated_data['quantity_obra'],
            detail=validated_data.get('detail', ''),
            waste_pct=validated_data.get('waste_pct'),
            price_override=validated_data.get('price_override'),
            subcategory=validated_data.get('subcategory'),
        )

        return Response(MaterialBudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='from-catalog-global')
    def from_catalog_global(self, request):
        """
        Crea una línea de presupuesto GLOBAL (paquete/compra preventiva) desde catálogo.
        Endpoint: POST /api/materials/budget/from-catalog-global/
        """
        serializer = FromCatalogGlobalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        item = MaterialBudgetService.create_global_from_catalog(
            project=validated_data['project'],
            catalog_item=validated_data['catalog_item'],
            quantity_purchase=validated_data['quantity_purchase'],
            price_per_purchase_unit=validated_data.get('price_per_purchase_unit'),
            detail=validated_data.get('detail', ''),
            subcategory=validated_data.get('subcategory'),
        )

        return Response(MaterialBudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='custom')
    def custom(self, request):
        """
        Crea una línea de presupuesto AD-HOC/PERSONALIZADA directamente en obra (sin catálogo).
        Endpoint: POST /api/materials/budget/custom/
        """
        serializer = CustomBudgetItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        item = MaterialBudgetService.create_custom_item(
            project=validated_data['project'],
            subcategory=validated_data['subcategory'],
            name=validated_data['name'],
            unit_measure=validated_data['unit_measure'],
            unit_purchase=validated_data['unit_purchase'],
            price_per_purchase_unit=validated_data['price_per_purchase_unit'],
            is_global=validated_data.get('is_global', False),
            quantity_obra=validated_data.get('quantity_obra'),
            quantity_purchase=validated_data.get('quantity_purchase'),
            conversion_factor=validated_data.get('conversion_factor'),
            weight_per_purchase_unit=validated_data.get('weight_per_purchase_unit'),
            waste_pct=validated_data.get('waste_pct', Decimal('0')),
            detail=validated_data.get('detail', ''),
        )

        return Response(MaterialBudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

    # -------------------------------------------------------------------
    # ENDPOINTS DE AGRUPACIÓN Y MÉTRICAS (Delega a MaterialBudgetMetricsService)
    # -------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='by-project')
    def by_project(self, request):
        """
        Retorna los ítems del presupuesto de un proyecto agrupados por subcategoría,
        con subtotales calculados por subcategoría y totales globales de la obra.
        Endpoint: GET /api/materials/budget/by-project/?project_id=1
        """
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"detail": "El parámetro 'project_id' o 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = MaterialBudgetMetricsService.get_project_budget_grouped_by_subcategory(int(project_id))
            return Response(data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response(
                {"detail": f"No se encontró el proyecto con id {project_id}."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            return Response(
                {"detail": "El identificador del proyecto debe ser un número entero válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Retorna un resumen de métricas clave del presupuesto de materiales de un proyecto.
        Endpoint: GET /api/materials/budget/summary/?project_id=1
        """
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"detail": "El parámetro 'project_id' o 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = MaterialBudgetMetricsService.get_project_budget_summary(int(project_id))
            return Response(data, status=status.HTTP_200_OK)
        except ValueError:
            return Response(
                {"detail": "El identificador del proyecto debe ser un número entero válido."},
                status=status.HTTP_400_BAD_REQUEST
            )
