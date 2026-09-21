from decimal import Decimal
from typing import Optional
from django.db import transaction
from core.models import Project, Subcategory, UnitOfMeasure
from labor.models import LaborBudgetItem, LaborCatalogItem


class LaborBudgetService:
    """
    Capa de servicio para la creación y operaciones de negocio sobre
    las líneas de presupuesto de mano de obra por obra.
    """

    @classmethod
    @transaction.atomic
    def create_from_catalog(
        cls,
        *,
        project: Project,
        catalog_item: LaborCatalogItem,
        quantity: Decimal,
        cost_override: Optional[Decimal] = None,
        contractor_name: str = "",
        detail: str = "",
        subcategory: Optional[Subcategory] = None,
    ) -> LaborBudgetItem:
        """
        Crea una línea de presupuesto en obra desde el catálogo maestro (Snapshot).
        """
        return LaborBudgetItem.from_catalog(
            project=project,
            catalog_item=catalog_item,
            quantity=quantity,
            cost_override=cost_override,
            contractor_name=contractor_name,
            detail=detail,
            subcategory=subcategory,
        )

    @classmethod
    @transaction.atomic
    def create_custom_item(
        cls,
        *,
        project: Project,
        subcategory: Subcategory,
        name: str,
        unit: UnitOfMeasure,
        quantity: Decimal,
        unit_cost: Decimal,
        contractor_name: str = "",
        detail: str = "",
    ) -> LaborBudgetItem:
        """
        Crea una línea de presupuesto personalizada (ad-hoc) directamente en la obra.
        """
        return LaborBudgetItem.create_custom(
            project=project,
            subcategory=subcategory,
            name=name,
            unit=unit,
            quantity=quantity,
            unit_cost=unit_cost,
            contractor_name=contractor_name,
            detail=detail,
        )
