from decimal import Decimal
from typing import Optional, Dict, Any
from .base_strategy import (
    BaseBudgetStrategy,
    ZERO,
    ONE,
    money,
)


class OperatingBudgetStrategy(BaseBudgetStrategy):
    """
    Estrategia de cálculo y validación para Gastos Operativos (G.O.).
    Soporta partidas directas (ej: alquiler de maquinaria, fletes de obra, servicios)
    o cómputos paramétricos porcentuales sobre una base de costo directo.
    """

    def calculate(self, item: Any, project: Optional[Any] = None) -> Dict[str, Any]:
        unit_price = item.unit_price or ZERO
        pct = item.percentage_applied or ZERO
        base = item.target_base_cost or ZERO

        # Modo A: Cálculo paramétrico porcentual (% sobre base de costo)
        # Nota de escala: percentage_applied se almacena en base decimal (ej: 0.15 para 15%)
        if pct > ZERO and base > ZERO:
            quantity_purchase = ONE
            estimated_cost = money(base * pct)
        else:
            # Modo B: Partida directa por unidad de servicio o global
            quantity_purchase = next(
                (q for q in (item.quantity_purchase, item.quantity_obra) if q is not None),
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

        if item.percentage_applied is not None and item.percentage_applied < ZERO:
            errors['percentage_applied'] = "El porcentaje no puede ser negativo."

        if item.target_base_cost is not None and item.target_base_cost < ZERO:
            errors['target_base_cost'] = "La base de costo no puede ser negativa."

        if item.unit_price is not None and item.unit_price < ZERO:
            errors['unit_price'] = "El precio o costo unitario no puede ser negativo."

        if item.quantity_purchase is not None and item.quantity_purchase < ZERO:
            errors['quantity_purchase'] = "La cantidad de compra no puede ser negativa."

        if item.quantity_obra is not None and item.quantity_obra < ZERO:
            errors['quantity_obra'] = "La cantidad en obra no puede ser negativa."

        return errors
