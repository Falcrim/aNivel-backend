from decimal import Decimal
from functools import cached_property
from django.db import models
from django.core.exceptions import ValidationError
from .timestamped_model import TimeStampedModel
from .project import Project
from .category import Category
from .subcategory import Subcategory
from .unit_of_measure import UnitOfMeasure
from .purchase_unit import PurchaseUnit
from .supplier import Supplier
from .construction_stage import ConstructionStage
from core.strategies.registry import BudgetStrategyRegistry


class BudgetCategoryType(models.TextChoices):
    MATERIALS = 'materials', 'Materiales de Construcción'
    LABOR = 'labor', 'Mano de Obra y Cuadrillas'
    OPERATING = 'operating', 'Gastos Operativos (G.O.)'
    ADMINISTRATIVE = 'administrative', 'Gastos Administrativos / Utilidad'


class BudgetItemQuerySet(models.QuerySet):
    """QuerySet optimizado para consultas analíticas y particionadas de presupuesto."""

    def for_project(self, project_id):
        return self.filter(project_id=project_id)

    def for_category(self, category_type):
        return self.filter(category_type=category_type)

    def for_stage(self, stage_id):
        return self.filter(stage_id=stage_id)

    def for_subcategory(self, subcategory_id):
        return self.filter(subcategory_id=subcategory_id)

    def with_relations(self):
        return self.select_related(
            'project',
            'stage',
            'subcategory',
            'subcategory__category',
            'supplier',
            'unit_measure',
            'unit_purchase',
        )


class BudgetItem(TimeStampedModel):
    """
    Modelo canónico unificado de partida de presupuesto de obra.
    Aplica Domain-Driven Design (DDD) y delega sus cálculos y validaciones
    a la familia de estrategias (`BaseBudgetStrategy`) según su `category_type`.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='budget_items',
        verbose_name="Proyecto / Obra"
    )
    category_type = models.CharField(
        max_length=30,
        choices=BudgetCategoryType.choices,
        default=BudgetCategoryType.MATERIALS,
        verbose_name="Categoría de Presupuesto"
    )
    stage = models.ForeignKey(
        ConstructionStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budget_items',
        verbose_name="Etapa Constructiva",
        help_text="Fase de la obra (Obra Gruesa, Obra Gris, Obra Fina, etc.)."
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='unified_budget_items',
        verbose_name="Subcategoría",
        help_text="Agrupador para organización y totales en el presupuesto."
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='budget_items',
        verbose_name="Proveedor o Contratista Sugerido"
    )
    name = models.CharField(max_length=255, verbose_name="Nombre de la partida / Insumo")
    detail = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Detalle / Especificación técnica puntual"
    )
    is_global = models.BooleanField(
        default=False,
        verbose_name="¿Es ítem global?",
        help_text="Marcar si es una partida en paquete o compra cerrada sin cómputo métrico."
    )
    apply_ceil = models.BooleanField(
        default=True,
        verbose_name="Redondeo hacia arriba (ceil)",
        help_text="Si está activo, redondea la cantidad comercial requerida al entero superior más cercano."
    )
    unit_measure = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Unidad de medida técnica (en obra)"
    )
    quantity_obra = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Cantidad requerida en obra (Cómputo neto)"
    )
    unit_purchase = models.ForeignKey(
        PurchaseUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        verbose_name="Unidad de compra comercial"
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name="Factor de conversión"
    )
    waste_pct = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=Decimal('0.0000'),
        verbose_name="Merma / Desperdicio (%)",
        help_text="Porcentaje de desperdicio estimado (ej: 0.1000 para 10%)."
    )
    quantity_purchase = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        verbose_name="Cantidad a comprar / contratar"
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precio o tarifa unitaria (Bs)"
    )
    weight_per_purchase_unit = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Peso por unidad comercial (kg)"
    )
    contractor_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Contratista / Cuadrilla asignada"
    )
    percentage_applied = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Porcentaje aplicado (%)",
        help_text="Porcentaje para gastos operativos o utilidad de obra (ej: 0.15 para 15%)."
    )
    target_base_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Base de costo para porcentaje (Bs)"
    )
    notes = models.TextField(blank=True, verbose_name="Notas de campo / observaciones")
    catalog_reference_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="ID de catálogo de origen"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Orden visual")

    objects = BudgetItemQuerySet.as_manager()

    class Meta:
        db_table = 'core_budget_item'
        verbose_name = "Partida de Presupuesto Unificada"
        verbose_name_plural = "Partidas de Presupuesto Unificadas"
        ordering = ['stage__order', 'subcategory__name', 'order', 'name']
        indexes = [
            models.Index(fields=['project', 'category_type'], name='core_bud_proj_cat_idx'),
            models.Index(fields=['project', 'stage'], name='core_bud_proj_stage_idx'),
            models.Index(fields=['project', 'subcategory'], name='core_bud_proj_subcat_idx'),
            models.Index(fields=['project', 'supplier'], name='core_bud_proj_supp_idx'),
        ]

    def __str__(self):
        return f"[{self.get_category_type_display()}] {self.name} ({self.project.name})"

    @property
    def strategy(self):
        """Resuelve dinámicamente la estrategia de cálculo para este ítem."""
        return BudgetStrategyRegistry.get_strategy(self.category_type)

    @cached_property
    def calculated_metrics(self):
        """
        Retorna el paquete de métricas computadas por la estrategia activa.
        Memoizado por instancia para evitar recálculos redundantes (4x) al serializar.
        """
        return self.strategy.calculate(self, getattr(self, 'project', None))

    @property
    def estimated_cost(self) -> Decimal:
        """Costo total estimado en Bolivianos."""
        return self.calculated_metrics['estimated_cost']

    @property
    def weight_total(self):
        """Peso total estimado en kg (solo materiales)."""
        return self.calculated_metrics['weight_total']

    @property
    def cost_usd(self) -> Decimal:
        """Costo total convertido a USD según tipo de cambio de la obra."""
        return self.calculated_metrics['cost_usd']

    @property
    def cost_per_m2_usd(self) -> Decimal:
        """Costo unitario en USD por metro cuadrado construido."""
        return self.calculated_metrics['cost_per_m2_usd']

    def clean(self):
        super().clean()
        errors = self.strategy.validate(self)
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        # Invalidar caché memoizada si se modifican atributos antes de persistir
        self.__dict__.pop('calculated_metrics', None)

        # Auto-cálculo de cantidad de compra para materiales estándar
        if not self.is_global and self.category_type == BudgetCategoryType.MATERIALS:
            calc = self.strategy.calculate(self, getattr(self, 'project', None))
            self.quantity_purchase = calc['quantity_purchase']
        elif self.category_type == BudgetCategoryType.LABOR and self.quantity_obra is not None:
            self.quantity_purchase = self.quantity_obra

        self.full_clean()
        super().save(*args, **kwargs)
