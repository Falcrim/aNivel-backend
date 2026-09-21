from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import Project
from labor.models import LaborBudgetItem
from labor.serializers import (
    LaborBudgetItemReadSerializer,
    LaborBudgetItemWriteSerializer,
    FromLaborCatalogActionSerializer,
    CustomLaborBudgetItemActionSerializer,
)
from labor.services import LaborBudgetService, LaborBudgetMetricsService


class LaborBudgetItemViewSet(viewsets.ModelViewSet):
    """
    CRUD y operaciones especializadas para el Presupuesto de Mano de Obra por Obra.

    Filtros soportados en listado:
    - Por proyecto: ?project=1 o ?project_id=1
    - Por subcategoría: ?subcategory=1 o ?subcategory_id=1
    - Por contratista: ?contractor=Albañil
    - Búsqueda: ?search=muro
    - Ordenamiento: ?ordering=subcategory__name,name o ?ordering=-unit_cost
    """
    queryset = LaborBudgetItem.objects.with_relations()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'detail', 'contractor_name', 'subcategory__name', 'project__name']
    ordering_fields = ['subcategory__name', 'name', 'unit_cost', 'quantity']
    ordering = ['subcategory__name', 'name']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return LaborBudgetItemWriteSerializer
        return LaborBudgetItemReadSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        project_id = self.request.query_params.get('project') or self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.for_project(project_id)

        subcategory_id = self.request.query_params.get('subcategory') or self.request.query_params.get('subcategory_id')
        if subcategory_id:
            queryset = queryset.for_subcategory(subcategory_id)

        contractor = self.request.query_params.get('contractor')
        if contractor:
            queryset = queryset.for_contractor(contractor)

        return queryset

    # -------------------------------------------------------------------
    # ENDPOINTS DE CREACIÓN ESPECÍFICA (Delega a LaborBudgetService)
    # -------------------------------------------------------------------

    @action(detail=False, methods=['post'], url_path='from-catalog')
    def from_catalog(self, request):
        """
        Crea una línea de presupuesto en obra desde una tarea del catálogo maestro.
        Endpoint: POST /api/labor/budget/from-catalog/
        """
        serializer = FromLaborCatalogActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        item = LaborBudgetService.create_from_catalog(
            project=validated_data['project'],
            catalog_item=validated_data['catalog_item'],
            quantity=validated_data['quantity'],
            cost_override=validated_data.get('cost_override'),
            contractor_name=validated_data.get('contractor_name', ''),
            detail=validated_data.get('detail', ''),
            subcategory=validated_data.get('subcategory'),
        )

        return Response(LaborBudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='custom')
    def custom(self, request):
        """
        Crea una línea de presupuesto AD-HOC/PERSONALIZADA directamente en obra (sin catálogo).
        Endpoint: POST /api/labor/budget/custom/
        """
        serializer = CustomLaborBudgetItemActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        item = LaborBudgetService.create_custom_item(
            project=validated_data['project'],
            subcategory=validated_data['subcategory'],
            name=validated_data['name'],
            unit=validated_data['unit'],
            quantity=validated_data['quantity'],
            unit_cost=validated_data['unit_cost'],
            contractor_name=validated_data.get('contractor_name', ''),
            detail=validated_data.get('detail', ''),
        )

        return Response(LaborBudgetItemReadSerializer(item).data, status=status.HTTP_201_CREATED)

    # -------------------------------------------------------------------
    # ENDPOINTS DE AGRUPACIÓN Y MÉTRICAS (Delega a LaborBudgetMetricsService)
    # -------------------------------------------------------------------

    @action(detail=False, methods=['get'], url_path='by-project')
    def by_project(self, request):
        """
        Retorna los ítems de mano de obra de un proyecto agrupados por subcategoría/etapa,
        con subtotales en Bs, USD y $/m² y totales generales.
        Endpoint: GET /api/labor/budget/by-project/?project_id=1
        """
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"detail": "El parámetro 'project_id' o 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = LaborBudgetMetricsService.get_project_budget_grouped_by_subcategory(int(project_id))
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
        Retorna el resumen de métricas clave de mano de obra de un proyecto (Total Bs, USD, $/m2).
        Endpoint: GET /api/labor/budget/summary/?project_id=1
        """
        project_id = request.query_params.get('project') or request.query_params.get('project_id')
        if not project_id:
            return Response(
                {"detail": "El parámetro 'project_id' o 'project' es requerido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = LaborBudgetMetricsService.get_project_budget_summary(int(project_id))
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
