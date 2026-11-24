from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from core.models import Project, BudgetItem, BudgetCategoryType, ConstructionStage
from core.strategies.base_strategy import (
    BaseBudgetStrategy,
    ZERO,
    DEFAULT_EXCHANGE_RATE,
)


class BudgetCalculationService:
    """
    Servicio de dominio para cálculos analíticos, agregaciones financieras
    y estructuración jerárquica del presupuesto de obra.
    """

    @classmethod
    def get_project_budget_summary(cls, project_id: int) -> Dict[str, Any]:
        """Calcula el resumen financiero global y por familias de costo de una obra."""
        project = Project.objects.filter(id=project_id).first()
        if not project:
            return {}

        rate = project.exchange_rate or DEFAULT_EXCHANGE_RATE
        area = project.built_area or Decimal('0.00')

        items = BudgetItem.objects.filter(project_id=project_id).with_relations()

        total_bs = Decimal('0.00')
        total_weight = Decimal('0.0000')

        materials_bs = Decimal('0.00')
        materials_weight = Decimal('0.0000')
        labor_bs = Decimal('0.00')
        operating_bs = Decimal('0.00')
        admin_bs = Decimal('0.00')

        total_count = 0
        materials_count = 0
        labor_count = 0
        operating_count = 0
        admin_count = 0

        for item in items:
            total_count += 1
            cost = item.estimated_cost
            total_bs += cost

            if item.category_type == BudgetCategoryType.MATERIALS:
                materials_count += 1
                materials_bs += cost
                if item.weight_total:
                    materials_weight += item.weight_total
                    total_weight += item.weight_total
            elif item.category_type == BudgetCategoryType.LABOR:
                labor_count += 1
                labor_bs += cost
            elif item.category_type == BudgetCategoryType.OPERATING:
                operating_count += 1
                operating_bs += cost
            elif item.category_type == BudgetCategoryType.ADMINISTRATIVE:
                admin_count += 1
                admin_bs += cost

        total_usd, cost_per_m2_usd = BaseBudgetStrategy.compute_usd_metrics(total_bs, project)
        materials_usd, _ = BaseBudgetStrategy.compute_usd_metrics(materials_bs, project)
        labor_usd, labor_cost_per_m2_usd = BaseBudgetStrategy.compute_usd_metrics(labor_bs, project)
        operating_usd, _ = BaseBudgetStrategy.compute_usd_metrics(operating_bs, project)
        admin_usd, _ = BaseBudgetStrategy.compute_usd_metrics(admin_bs, project)

        return {
            'project_id': project.id,
            'project_name': project.name,
            'built_area': str(area),
            'exchange_rate': str(rate),
            'total_budget_bs': str(total_bs),
            'total_budget_usd': str(total_usd),
            'cost_per_m2_usd': str(cost_per_m2_usd),
            'total_weight_kg': str(total_weight),
            'total_items_count': total_count,
            'materials': {
                'total_cost_bs': str(materials_bs),
                'total_cost_usd': str(materials_usd),
                'total_weight_kg': str(materials_weight),
                'items_count': materials_count,
            },
            'labor': {
                'total_cost_bs': str(labor_bs),
                'total_cost_usd': str(labor_usd),
                'cost_per_m2_usd': str(labor_cost_per_m2_usd),
                'items_count': labor_count,
            },
            'operating': {
                'total_cost_bs': str(operating_bs),
                'total_cost_usd': str(operating_usd),
                'items_count': operating_count,
            },
            'administrative': {
                'total_cost_bs': str(admin_bs),
                'total_cost_usd': str(admin_usd),
                'items_count': admin_count,
            },
        }

    @classmethod
    def get_project_budget_grouped_by_subcategory(cls, project_id: int, category_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Agrupa el presupuesto por subcategoría para alimentar el acordeón frontend,
        calculando subtotales en Bs, $, peso y el resumen de unidades de compra comerciales.
        """
        project = Project.objects.filter(id=project_id).first()
        if not project:
            return []

        rate = project.exchange_rate or Decimal('6.9700')
        qs = BudgetItem.objects.filter(project_id=project_id).with_relations()
        if category_type:
            qs = qs.filter(category_type=category_type)

        # Agrupar en memoria por subcategoría preservando orden
        groups_map: Dict[Any, Dict[str, Any]] = {}

        for item in qs:
            subcat_id = item.subcategory_id or 0
            subcat_name = item.subcategory.name if item.subcategory else "Sin Subcategoría"

            if subcat_id not in groups_map:
                groups_map[subcat_id] = {
                    'subcategory_id': subcat_id if subcat_id != 0 else None,
                    'subcategory_name': subcat_name,
                    'category_name': item.subcategory.category.name if item.subcategory and item.subcategory.category else "General",
                    'items_count': 0,
                    'subtotal_cost_bs': Decimal('0.00'),
                    'subtotal_cost_usd': Decimal('0.00'),
                    'subtotal_weight_kg': Decimal('0.0000'),
                    'purchase_units_counter': {},
                    'items': [],
                }

            group = groups_map[subcat_id]
            cost = item.estimated_cost
            group['items_count'] += 1
            group['subtotal_cost_bs'] += cost
            if item.weight_total:
                group['subtotal_weight_kg'] += item.weight_total

            # Acumulador de unidades comerciales para el acordeón (ej: 30 barras, 10 bolsas)
            if item.unit_purchase and item.quantity_purchase and item.quantity_purchase > Decimal('0'):
                pu_name = item.unit_purchase.name
                current_qty = group['purchase_units_counter'].get(pu_name, Decimal('0'))
                group['purchase_units_counter'][pu_name] = current_qty + item.quantity_purchase

            group['items'].append(item)

        result = []
        for g in groups_map.values():
            if rate > ZERO:
                g['subtotal_cost_usd'], _ = BaseBudgetStrategy.compute_usd_metrics(g['subtotal_cost_bs'], project)

            # Formatear el resumen textual de unidades de compra comerciales
            units_summary = [
                f"{int(qty) if qty % 1 == 0 else round(qty, 2)} {name}"
                for name, qty in g['purchase_units_counter'].items()
            ]
            g['total_purchase_units_summary'] = ", ".join(units_summary) if units_summary else "N/A"

            # Conversión de tipos para serialización limpia
            g['subtotal_cost_bs'] = str(g['subtotal_cost_bs'])
            g['subtotal_cost_usd'] = str(g['subtotal_cost_usd'])
            g['subtotal_weight_kg'] = str(g['subtotal_weight_kg'])
            del g['purchase_units_counter']
            result.append(g)

        return result

    @classmethod
    def get_project_budget_grouped_by_stage(cls, project_id: int, category_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Agrupa el presupuesto en jerarquía de 2 niveles:
        Etapa Constructiva -> Subcategorías -> Partidas.
        Calcula subtotales en Bs, $, % de incidencia en la familia activa y costo por m2.
        """
        project = Project.objects.filter(id=project_id).first()
        if not project:
            return []

        rate = project.exchange_rate or Decimal('6.9700')
        qs = BudgetItem.objects.filter(project_id=project_id).with_relations()
        if category_type:
            qs = qs.filter(category_type=category_type.lower())

        # Calcular costo total de la familia activa para determinar porcentajes
        family_total_bs = Decimal('0.00')
        for item in qs:
            family_total_bs += item.estimated_cost

        # Cargar todas las etapas constructivas existentes ordenadas
        known_stages = list(ConstructionStage.objects.all().order_by('order', 'id'))
        stages_dict: Dict[Any, Dict[str, Any]] = {}

        for st in known_stages:
            stages_dict[st.id] = {
                'stage_id': st.id,
                'stage_name': st.name,
                'stage_color': st.color or 'amber',
                'stage_order': st.order,
                'items_count': 0,
                'subtotal_cost_bs': Decimal('0.00'),
                'subtotal_cost_usd': Decimal('0.00'),
                'percentage_of_family': '0.0%',
                'cost_per_m2_usd': '0.00',
                'subcategories_map': {},
            }

        # Entrada especial para ítems sin etapa asignada
        stages_dict[None] = {
            'stage_id': None,
            'stage_name': 'Partidas sin Etapa Asignada',
            'stage_color': 'slate',
            'stage_order': 999999,
            'items_count': 0,
            'subtotal_cost_bs': Decimal('0.00'),
            'subtotal_cost_usd': Decimal('0.00'),
            'percentage_of_family': '0.0%',
            'cost_per_m2_usd': '0.00',
            'subcategories_map': {},
        }

        from core.serializers.budget_item_serializer import BudgetItemReadSerializer

        for item in qs:
            st_id = item.stage_id
            if st_id not in stages_dict:
                st_name = item.stage.name if item.stage else 'Partidas sin Etapa Asignada'
                st_order = item.stage.order if item.stage else 999999
                st_color = item.stage.color if item.stage else 'slate'
                stages_dict[st_id] = {
                    'stage_id': st_id,
                    'stage_name': st_name,
                    'stage_color': st_color,
                    'stage_order': st_order,
                    'items_count': 0,
                    'subtotal_cost_bs': Decimal('0.00'),
                    'subtotal_cost_usd': Decimal('0.00'),
                    'percentage_of_family': '0.0%',
                    'cost_per_m2_usd': '0.00',
                    'subcategories_map': {},
                }

            stage_group = stages_dict[st_id]
            cost = item.estimated_cost
            stage_group['items_count'] += 1
            stage_group['subtotal_cost_bs'] += cost

            # Agrupar por subcategoría dentro de la etapa
            subcat_id = item.subcategory_id
            subcat_name = item.subcategory.name if item.subcategory else 'Sin Subcategoría'
            sub_map = stage_group['subcategories_map']

            if subcat_id not in sub_map:
                sub_map[subcat_id] = {
                    'subcategory_id': subcat_id,
                    'subcategory_name': subcat_name,
                    'items_count': 0,
                    'subtotal_cost_bs': Decimal('0.00'),
                    'subtotal_cost_usd': Decimal('0.00'),
                    'purchase_units_counter': {},
                    'items': [],
                }

            sub_group = sub_map[subcat_id]
            sub_group['items_count'] += 1
            sub_group['subtotal_cost_bs'] += cost

            if item.unit_purchase and item.quantity_purchase and item.quantity_purchase > Decimal('0'):
                pu_name = item.unit_purchase.name
                cur_qty = sub_group['purchase_units_counter'].get(pu_name, Decimal('0'))
                sub_group['purchase_units_counter'][pu_name] = cur_qty + item.quantity_purchase

            sub_group['items'].append(BudgetItemReadSerializer(item).data)

        # Formatear y calcular métricas derivadas
        result = []
        for stage_group in sorted(stages_dict.values(), key=lambda s: s['stage_order']):
            # Solo incluir grupos de etapa que tengan ítems registrados
            if stage_group['items_count'] == 0:
                continue

            stage_bs = stage_group['subtotal_cost_bs']
            stage_usd, cost_per_m2_usd = BaseBudgetStrategy.compute_usd_metrics(stage_bs, project)
            stage_group['subtotal_cost_usd'] = str(stage_usd)
            stage_group['cost_per_m2_usd'] = str(cost_per_m2_usd)

            if family_total_bs > ZERO:
                pct = (stage_bs / family_total_bs) * Decimal('100.0')
                stage_group['percentage_of_family'] = f"{pct.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"
            else:
                stage_group['percentage_of_family'] = "0.0%"

            stage_group['subtotal_cost_bs'] = str(stage_bs)

            # Formatear subcategorías dentro de la etapa
            subcategories_list = []
            for sub_group in stage_group['subcategories_map'].values():
                sub_bs = sub_group['subtotal_cost_bs']
                sub_usd, _ = BaseBudgetStrategy.compute_usd_metrics(sub_bs, project)
                sub_group['subtotal_cost_usd'] = str(sub_usd)
                sub_group['subtotal_cost_bs'] = str(sub_bs)

                units_summary = [
                    f"{int(qty) if qty % 1 == 0 else round(qty, 2)} {name}"
                    for name, qty in sub_group['purchase_units_counter'].items()
                ]
                sub_group['total_purchase_units_summary'] = ", ".join(units_summary) if units_summary else "N/A"
                del sub_group['purchase_units_counter']
                subcategories_list.append(sub_group)

            del stage_group['subcategories_map']
            stage_group['subcategories'] = subcategories_list
            result.append(stage_group)

        return result
