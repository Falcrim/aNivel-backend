from decimal import Decimal
from typing import Dict, Any, List
from django.db.models import Sum, Count, F, Q, DecimalField
from django.db.models.functions import Coalesce
from django.core.exceptions import ObjectDoesNotExist

from core.models import Project
from materials.models import MaterialBudgetItem
from materials.serializers.material_budget_serializer import MaterialBudgetItemReadSerializer


class MaterialBudgetMetricsService:
    """
    Servicio especializado en cálculos agregados, reportería y estructuración
    de datos de presupuesto de materiales por proyecto.
    """

    @classmethod
    def get_project_budget_summary(cls, project_id: int) -> Dict[str, Any]:
        """
        Retorna un resumen de métricas clave del presupuesto de un proyecto,
        calculado de forma optimizada mediante una única consulta SQL de agregación.
        """
        qs = MaterialBudgetItem.objects.filter(project_id=project_id)

        metrics = qs.aggregate(
            total_cost=Coalesce(
                Sum(
                    F('quantity_purchase') * F('price_per_purchase_unit'),
                    output_field=DecimalField(max_digits=15, decimal_places=2)
                ),
                Decimal('0.00')
            ),
            total_weight=Coalesce(
                Sum(
                    F('quantity_purchase') * Coalesce(F('weight_per_purchase_unit'), Decimal('0.0000')),
                    output_field=DecimalField(max_digits=15, decimal_places=4)
                ),
                Decimal('0.00')
            ),
            total_items=Count('id'),
            normal_items_count=Count('id', filter=Q(is_global=False)),
            global_items_count=Count('id', filter=Q(is_global=True)),
            from_catalog_count=Count('id', filter=Q(catalog_item__isnull=False)),
            custom_items_count=Count('id', filter=Q(catalog_item__isnull=True)),
        )

        return {
            'project_id': int(project_id),
            'total_materials_cost': metrics['total_cost'],
            'total_materials_weight_kg': metrics['total_weight'],
            'total_items': metrics['total_items'],
            'normal_items_count': metrics['normal_items_count'],
            'global_items_count': metrics['global_items_count'],
            'from_catalog_count': metrics['from_catalog_count'],
            'custom_items_count': metrics['custom_items_count'],
        }

    @classmethod
    def get_project_budget_grouped_by_subcategory(cls, project_id: int) -> Dict[str, Any]:
        """
        Retorna los ítems de presupuesto de un proyecto organizados por subcategoría,
        con subtotales y serialización optimizada (sin consultas N+1).
        """
        project = Project.objects.get(id=project_id)
        items: List[MaterialBudgetItem] = list(
            MaterialBudgetItem.objects.with_relations().for_project(project_id)
        )

        grouped_data: Dict[int, Dict[str, Any]] = {}
        total_project_cost = Decimal('0.00')
        total_project_weight = Decimal('0.00')

        for item in items:
            subcat_id = item.subcategory_id
            if subcat_id not in grouped_data:
                grouped_data[subcat_id] = {
                    'subcategory_id': item.subcategory.id,
                    'subcategory_name': item.subcategory.name,
                    'subtotal_cost': Decimal('0.00'),
                    'subtotal_weight': Decimal('0.00'),
                    'items_count': 0,
                    'items': []
                }

            cost = item.estimated_cost or Decimal('0.00')
            weight = item.weight_total or Decimal('0.00')

            grouped_data[subcat_id]['subtotal_cost'] += cost
            grouped_data[subcat_id]['subtotal_weight'] += weight
            grouped_data[subcat_id]['items_count'] += 1
            grouped_data[subcat_id]['items'].append(MaterialBudgetItemReadSerializer(item).data)

            total_project_cost += cost
            total_project_weight += weight

        return {
            'project_id': project.id,
            'project_name': project.name,
            'total_materials_cost': total_project_cost,
            'total_materials_weight_kg': total_project_weight,
            'subcategories_count': len(grouped_data),
            'total_items_count': len(items),
            'groups': list(grouped_data.values())
        }
