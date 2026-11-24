import math
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any
from .base_strategy import (
    BaseBudgetStrategy,
    ZERO,
    ONE,
    FOUR_DECIMALS,
    money,
)


class MaterialBudgetStrategy(BaseBudgetStrategy):
    """
    Estrategia de cálculo y validación para partidas de Materiales de Construcción.
    Aplica merma comercial, factor de conversión métrico a comercial,
    redondeo configurable hacia arriba (ceil) y cómputo de peso acumulado.
    """

    def calculate(self, item: Any, project: Optional[Any] = None) -> Dict[str, Any]:
        unit_price = item.unit_price or ZERO
        quantity_purchase = ZERO

        if item.is_global:
            quantity_purchase = item.quantity_purchase if item.quantity_purchase is not None else ONE
        else:
            conv = item.conversion_factor
            if item.quantity_obra is not None and conv and conv > ZERO:
                waste = item.waste_pct if item.waste_pct is not None else ZERO
                cantidad_con_merma = item.quantity_obra * (ONE + waste)
                unidades = cantidad_con_merma / conv

                if getattr(item, 'apply_ceil', True):
                    quantity_purchase = Decimal(math.ceil(unidades))
                else:
                    quantity_purchase = unidades.quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)
            elif item.quantity_purchase is not None:
                quantity_purchase = item.quantity_purchase

        estimated_cost = money(quantity_purchase * unit_price)

        # Peso total estimado (kg)
        weight_total = None
        if item.weight_per_purchase_unit and quantity_purchase:
            weight_total = (quantity_purchase * item.weight_per_purchase_unit).quantize(
                FOUR_DECIMALS, rounding=ROUND_HALF_UP
            )

        cost_usd, cost_per_m2_usd = self.compute_usd_metrics(
            estimated_cost, project or getattr(item, 'project', None)
        )

        return {
            'quantity_purchase': quantity_purchase,
            'estimated_cost': estimated_cost,
            'weight_total': weight_total,
            'cost_usd': cost_usd,
            'cost_per_m2_usd': cost_per_m2_usd,
        }

    def validate(self, item: Any) -> Dict[str, str]:
        errors = {}

        if item.is_global:
            if item.quantity_obra is not None:
                errors['quantity_obra'] = "Un ítem global de materiales no debe definir cómputo de obra métrico."
            if item.quantity_purchase is None or item.quantity_purchase <= ZERO:
                errors['quantity_purchase'] = "Un ítem global requiere una cantidad de compra comercial mayor a 0."
        else:
            if item.quantity_obra is None:
                errors['quantity_obra'] = "La cantidad requerida en obra (cómputo métrico) es obligatoria."
            elif item.quantity_obra < ZERO:
                errors['quantity_obra'] = "La cantidad en obra no puede ser negativa."

            if not item.conversion_factor or item.conversion_factor <= ZERO:
                errors['conversion_factor'] = "El factor de conversión debe ser mayor a 0 para ítems estándar."

        if item.unit_price is None or item.unit_price < ZERO:
            errors['unit_price'] = "El precio unitario no puede ser negativo ni nulo."

        return errors
