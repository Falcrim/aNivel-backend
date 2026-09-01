from decimal import Decimal
from typing import Optional
from django.db import transaction
from core.models import Project, Subcategory, UnitOfMeasure, PurchaseUnit
from materials.models import MaterialBudgetItem, MaterialCatalogItem


class MaterialBudgetService:
    """
    Capa de servicio para la creación y operaciones de negocio sobre
    las líneas de presupuesto de materiales por obra.
    """

    @classmethod
    @transaction.atomic
    def create_from_catalog(
        cls,
        *,
        project: Project,
        catalog_item: MaterialCatalogItem,
        quantity_obra: Decimal,
        detail: str = "",
        waste_pct: Optional[Decimal] = None,
        price_override: Optional[Decimal] = None,
        subcategory: Optional[Subcategory] = None,
    ) -> MaterialBudgetItem:
        """
        Crea una línea de presupuesto NORMAL a partir de un ítem del catálogo maestro.
        Calcula quantity_purchase con redondeo hacia arriba mediante save().
        """
        effective_price = (
            price_override
            if price_override is not None
            else catalog_item.price_per_purchase_unit
        )
        if effective_price is None:
            effective_price = Decimal('0.00')

        return MaterialBudgetItem.objects.create(
            project=project,
            catalog_item=catalog_item,
            subcategory=subcategory or catalog_item.subcategory,
            name=catalog_item.name,
            detail=detail,
            is_global=False,
            unit_measure=catalog_item.unit_measure,
            unit_purchase=catalog_item.unit_purchase,
            conversion_factor=catalog_item.conversion_factor,
            weight_per_purchase_unit=catalog_item.weight_per_purchase_unit,
            quantity_obra=quantity_obra,
            waste_pct=waste_pct if waste_pct is not None else catalog_item.waste_pct,
            price_per_purchase_unit=effective_price,
            quantity_purchase=Decimal('0'),  # recalculado automáticamente por save()
        )

    @classmethod
    @transaction.atomic
    def create_global_from_catalog(
        cls,
        *,
        project: Project,
        catalog_item: MaterialCatalogItem,
        quantity_purchase: Decimal,
        price_per_purchase_unit: Optional[Decimal] = None,
        detail: str = "",
        subcategory: Optional[Subcategory] = None,
    ) -> MaterialBudgetItem:
        """
        Crea una línea de presupuesto GLOBAL (paquete cerrado / compra preventiva)
        a partir de un ítem del catálogo.
        """
        effective_price = (
            price_per_purchase_unit
            if price_per_purchase_unit is not None
            else catalog_item.price_per_purchase_unit
        )
        if effective_price is None:
            effective_price = Decimal('0.00')

        return MaterialBudgetItem.objects.create(
            project=project,
            catalog_item=catalog_item,
            subcategory=subcategory or catalog_item.subcategory,
            name=catalog_item.name,
            detail=detail,
            is_global=True,
            unit_measure=catalog_item.unit_measure,
            unit_purchase=catalog_item.unit_purchase,
            conversion_factor=catalog_item.conversion_factor,
            weight_per_purchase_unit=catalog_item.weight_per_purchase_unit,
            quantity_obra=None,
            waste_pct=Decimal('0'),
            quantity_purchase=quantity_purchase,
            price_per_purchase_unit=effective_price,
        )

    @classmethod
    @transaction.atomic
    def create_custom_item(
        cls,
        *,
        project: Project,
        subcategory: Subcategory,
        name: str,
        unit_measure: UnitOfMeasure,
        unit_purchase: PurchaseUnit,
        price_per_purchase_unit: Decimal,
        is_global: bool = False,
        quantity_obra: Optional[Decimal] = None,
        quantity_purchase: Optional[Decimal] = None,
        conversion_factor: Optional[Decimal] = None,
        weight_per_purchase_unit: Optional[Decimal] = None,
        waste_pct: Decimal = Decimal('0'),
        detail: str = "",
    ) -> MaterialBudgetItem:
        """
        Crea una línea de presupuesto personalizada (ad-hoc) directamente en la obra,
        sin vinculación a un ítem previo del catálogo maestro.
        """
        return MaterialBudgetItem.objects.create(
            project=project,
            catalog_item=None,
            subcategory=subcategory,
            name=name,
            detail=detail,
            is_global=is_global,
            unit_measure=unit_measure,
            unit_purchase=unit_purchase,
            conversion_factor=conversion_factor,
            weight_per_purchase_unit=weight_per_purchase_unit,
            quantity_obra=quantity_obra,
            waste_pct=waste_pct,
            quantity_purchase=quantity_purchase if is_global else Decimal('0'),
            price_per_purchase_unit=price_per_purchase_unit,
        )
