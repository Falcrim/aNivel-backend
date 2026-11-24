from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, Any, Tuple

# Constantes numéricas de precisión financiera y cálculo
ZERO = Decimal('0')
ONE = Decimal('1.0000')
CENT = Decimal('0.01')
FOUR_DECIMALS = Decimal('0.0001')
DEFAULT_EXCHANGE_RATE = Decimal('6.9700')


def money(value: Decimal) -> Decimal:
    """Aplica redondeo comercial aritmético explícito (ROUND_HALF_UP) a 2 decimales."""
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


class BaseBudgetStrategy(ABC):
    """
    Estrategia base abstracta para el cálculo y validación de partidas presupuestarias.
    Encapsula lógica común de conversión cambiaria, métricas por m² de obra y constantes numéricas.
    """

    @abstractmethod
    def calculate(self, item: Any, project: Optional[Any] = None) -> Dict[str, Any]:
        """
        Ejecuta el cálculo específico de la partida y retorna un diccionario
        con los valores computados (quantity_purchase, estimated_cost, weight_total,
        cost_usd, cost_per_m2_usd).
        """
        pass

    @abstractmethod
    def validate(self, item: Any) -> Dict[str, str]:
        """
        Valida las invariantes y reglas de negocio del ítem antes de persistir.
        Retorna un diccionario de errores {campo: mensaje}.
        """
        pass

    @staticmethod
    def compute_usd_metrics(cost_bs: Decimal, proj: Optional[Any]) -> Tuple[Decimal, Decimal]:
        """
        Calcula las métricas en USD sin error de redondeo acumulado:
        - Divide primero con precisión completa y redondea al final con ROUND_HALF_UP.
        """
        if not proj:
            return ZERO, ZERO

        rate = getattr(proj, 'exchange_rate', None) or DEFAULT_EXCHANGE_RATE
        area = getattr(proj, 'built_area', None) or ZERO

        if rate <= ZERO:
            return ZERO, ZERO

        raw_usd = cost_bs / rate
        cost_usd = money(raw_usd)
        cost_per_m2_usd = money(raw_usd / area) if area > ZERO else ZERO

        return cost_usd, cost_per_m2_usd
