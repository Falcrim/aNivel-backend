from decimal import Decimal
from typing import Dict, Any, List
from django.db.models import Sum, Count, F, Q, DecimalField
from django.db.models.functions import Coalesce

from core.models import Project
from labor.models import LaborBudgetItem
from labor.serializers.labor_budget_serializer import LaborBudgetItemReadSerializer


class LaborBudgetMetricsService:
    """
    Servicio especializado en cálculos agregados, reportería y estructuración
    de datos de presupuesto de Mano de Obra por proyecto.
    """

    @classmethod
    def get_project_budget_summary(cls, project_id: int) -> Dict[str, Any]:
        """
        Retorna un resumen de métricas clave del presupuesto de mano de obra de un proyecto,
        incluyendo totales en Bs, USD y costos por metro cuadrado construido.
        """
        project = Project.objects.get(id=project_id)
        qs = LaborBudgetItem.objects.filter(project_id=project_id)

        metrics = qs.aggregate(
            total_cost=Coalesce(
                Sum(
                    F('quantity') * F('unit_cost'),
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                ),
                Decimal('0.00')
            ),
            total_items=Count('id'),
            from_catalog_count=Count('id', filter=Q(catalog_item__isnull=False)),
            custom_items_count=Count('id', filter=Q(catalog_item__isnull=True)),
        )

        total_cost_bs = metrics['total_cost']
        exchange_rate = project.exchange_rate if project.exchange_rate and project.exchange_rate > 0 else Decimal('6.97')
        built_area = project.built_area if project.built_area and project.built_area > 0 else Decimal('0.00')

        total_cost_usd = (total_cost_bs / exchange_rate).quantize(Decimal('0.01')) if exchange_rate > 0 else Decimal('0.00')
        cost_per_m2_bs = (total_cost_bs / built_area).quantize(Decimal('0.01')) if built_area > 0 else Decimal('0.00')
        cost_per_m2_usd = (total_cost_usd / built_area).quantize(Decimal('0.01')) if built_area > 0 else Decimal('0.00')

        return {
            'project_id': project.id,
            'project_name': project.name,
            'project_status': project.status,
            'project_status_display': project.get_status_display(),
            'built_area': built_area,
            'exchange_rate': exchange_rate,
            'total_labor_cost_bs': total_cost_bs,
            'total_labor_cost_usd': total_cost_usd,
            'cost_per_m2_bs': cost_per_m2_bs,
            'cost_per_m2_usd': cost_per_m2_usd,
            'total_items': metrics['total_items'],
            'from_catalog_count': metrics['from_catalog_count'],
            'custom_items_count': metrics['custom_items_count'],
        }

    @classmethod
    def get_project_budget_grouped_by_subcategory(cls, project_id: int) -> Dict[str, Any]:
        """
        Retorna los ítems de mano de obra organizados por subcategoría/etapa,
        con subtotales en Bs, USD, $/m² y serialización optimizada sin N+1.
        """
        project = Project.objects.get(id=project_id)
        items: List[LaborBudgetItem] = list(
            LaborBudgetItem.objects.with_relations().for_project(project_id)
        )

        exchange_rate = project.exchange_rate if project.exchange_rate and project.exchange_rate > 0 else Decimal('6.97')
        built_area = project.built_area if project.built_area and project.built_area > 0 else Decimal('0.00')

        grouped_data: Dict[int, Dict[str, Any]] = {}
        total_project_cost_bs = Decimal('0.00')

        for item in items:
            subcat_id = item.subcategory_id
            if subcat_id not in grouped_data:
                grouped_data[subcat_id] = {
                    'subcategory_id': item.subcategory.id,
                    'subcategory_name': item.subcategory.name,
                    'subtotal_cost_bs': Decimal('0.00'),
                    'subtotal_cost_usd': Decimal('0.00'),
                    'cost_per_m2_usd': Decimal('0.00'),
                    'items_count': 0,
                    'items': []
                }

            cost = item.estimated_cost or Decimal('0.00')
            grouped_data[subcat_id]['subtotal_cost_bs'] += cost
            grouped_data[subcat_id]['items_count'] += 1
            grouped_data[subcat_id]['items'].append(LaborBudgetItemReadSerializer(item).data)

            total_project_cost_bs += cost

        # Calcular conversiones de cada subcategoría
        for group in grouped_data.values():
            g_cost_bs = group['subtotal_cost_bs']
            g_cost_usd = (g_cost_bs / exchange_rate).quantize(Decimal('0.01')) if exchange_rate > 0 else Decimal('0.00')
            g_cost_m2 = (g_cost_usd / built_area).quantize(Decimal('0.01')) if built_area > 0 else Decimal('0.00')
            group['subtotal_cost_usd'] = g_cost_usd
            group['cost_per_m2_usd'] = g_cost_m2

        total_project_cost_usd = (total_project_cost_bs / exchange_rate).quantize(Decimal('0.01')) if exchange_rate > 0 else Decimal('0.00')
        total_cost_per_m2_usd = (total_project_cost_usd / built_area).quantize(Decimal('0.01')) if built_area > 0 else Decimal('0.00')

        return {
            'project_id': project.id,
            'project_name': project.name,
            'built_area': built_area,
            'exchange_rate': exchange_rate,
            'total_labor_cost_bs': total_project_cost_bs,
            'total_labor_cost_usd': total_project_cost_usd,
            'cost_per_m2_usd': total_cost_per_m2_usd,
            'subcategories_count': len(grouped_data),
            'total_items_count': len(items),
            'groups': list(grouped_data.values())
        }
