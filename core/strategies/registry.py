from typing import Dict
from .base_strategy import BaseBudgetStrategy
from .material_strategy import MaterialBudgetStrategy
from .labor_strategy import LaborBudgetStrategy
from .operating_strategy import OperatingBudgetStrategy
from .admin_strategy import AdminBudgetStrategy


class BudgetStrategyRegistry:
    """
    Registro desacoplado y punto único de acceso para resolver
    la estrategia de cálculo correspondiente a cada categoría de presupuesto.
    """
    _strategies: Dict[str, BaseBudgetStrategy] = {
        'materials': MaterialBudgetStrategy(),
        'labor': LaborBudgetStrategy(),
        'operating': OperatingBudgetStrategy(),
        'administrative': AdminBudgetStrategy(),
    }

    @classmethod
    def get_strategy(cls, category_type: str) -> BaseBudgetStrategy:
        norm = (category_type or 'materials').lower()
        return cls._strategies.get(norm, cls._strategies['materials'])

    @classmethod
    def register(cls, category_type: str, strategy: BaseBudgetStrategy) -> None:
        """Permite registrar o sobrescribir estrategias."""
        cls._strategies[category_type.lower()] = strategy
