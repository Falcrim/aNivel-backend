from decimal import Decimal
from typing import Optional, Dict, Any
from .base_strategy import (
    BaseBudgetStrategy,
    ZERO,
    ONE,
    money,
)


class LaborBudgetStrategy(BaseBudgetStrategy):
    """
    Estrategia de cálculo y validación para partidas de Mano de Obra y Cuadrillas.
    Calcula cómputo métrico pactado, costo por unidad de avance y ratios en tiempo real
    de costo total en USD y costo por metro cuadrado ($/m²).
    """

    def calculate(self, item: Any, project: Optional[Any] = None) -> Dict[str, Any]:
        unit_price = item.unit_price or ZERO

        # En mano de obra, la cantidad efectiva es el cómputo métrico asignado o cantidad de compra
        quantity_purchase = next(
            (q for q in (item.quantity_obra, item.quantity_purchase) if q is not None),
            ONE,
        )

        estimated_cost = money(quantity_purchase * unit_price)

        cost_usd, cost_per_m2_usd = self.compute_usd_metrics(
            estimated_cost, project or getattr(item, 'project', None)
        )

        return {
            'quantity_purchase': quantity_purchase,
            'estimated_cost': estimated_cost,
            'weight_total': None,
            'cost_usd': cost_usd,
            'cost_per_m2_usd': cost_per_m2_usd,
        }

    def validate(self, item: Any) -> Dict[str, str]:
        errors = {}

        qty = item.quantity_obra if item.quantity_obra is not None else item.quantity_purchase
        if qty is None:
            errors['quantity_obra'] = "La cantidad o cómputo métrico de la tarea es obligatoria."
        elif qty < ZERO:
            errors['quantity_obra'] = "La cantidad no puede ser negativa."

        if item.unit_price is None or item.unit_price < ZERO:
            errors['unit_price'] = "La tarifa pactada o costo unitario no puede ser negativa ni nula."

        return errors
