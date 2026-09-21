from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from core.models import Project, Subcategory, UnitOfMeasure, TimeStampedModel
from .labor_catalog import LaborCatalogItem


class LaborBudgetItemQuerySet(models.QuerySet):
    """QuerySet personalizado para consultas optimizadas y expresivas de mano de obra."""

    def for_project(self, project_id):
        """Filtra ítems de un proyecto específico."""
        return self.filter(project_id=project_id)

    def for_subcategory(self, subcategory_id):
        """Filtra ítems de una subcategoría específica."""
        return self.filter(subcategory_id=subcategory_id)

    def for_contractor(self, contractor_name):
        """Filtra ítems asignados a un contratista específico."""
        return self.filter(contractor_name__iexact=contractor_name)

    def with_relations(self):
        """Pre-carga todas las relaciones ForeignKey para evitar consultas N+1."""
        return self.select_related(
            'project',
            'subcategory',
            'subcategory__category',
            'unit',
            'catalog_item',
            'catalog_item__subcategory',
            'catalog_item__subcategory__category',
            'catalog_item__unit',
        )


class LaborBudgetItem(TimeStampedModel):
    """
    Línea de presupuesto de Mano de Obra para un proyecto/obra concreta.

    Actúa como un SNAPSHOT independiente del catálogo maestro:
    permite negociar o ajustar la tarifa pactada con el contratista
    sin alterar el catálogo maestro.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='labor_budget_items',
        verbose_name="Proyecto"
    )
    catalog_item = models.ForeignKey(
        LaborCatalogItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='budget_instances',
        verbose_name="Ítem de catálogo origen",
        help_text="Referencia histórica al catálogo maestro."
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.PROTECT,
        related_name='labor_budget_items',
        verbose_name="Subcategoría / Etapa",
        help_text="Etapa constructiva de la obra (Obra Gris, Fina, Eléctrica, etc.)."
    )
    contractor_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Contratista / Especialidad",
        help_text="Nombre del contratista o cuadrilla asignada (ej: Contratista Obra Gris)."
    )
    name = models.CharField(max_length=255, verbose_name="Nombre de la tarea")
    detail = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Detalle / Alcance específico",
        help_text="Especificación puntual para esta obra (ej: arranca desde viga de fundación)."
    )
    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name="Unidad de medida",
        help_text="Unidad en la que se cuantifica la labor (m2, ml, punto, pza, Gbl, etc.)."
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Cantidad / Cómputo",
        help_text="Metrado neto ejecutado o contratado."
    )
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Costo Unitario (Bs)",
        help_text="Tarifa pactada en Bolivianos por cada unidad."
    )

    objects = LaborBudgetItemQuerySet.as_manager()

    class Meta:
        db_table = 'labor_budget_item'
        verbose_name = "Ítem de Presupuesto de Mano de Obra"
        verbose_name_plural = "Ítems de Presupuesto de Mano de Obra"
        ordering = ['project', 'subcategory__name', 'name']
        indexes = [
            models.Index(fields=['project', 'subcategory'], name='labor_bud_proj_subcat_idx'),
            models.Index(fields=['project', 'contractor_name'], name='labor_bud_proj_cont_idx'),
            models.Index(fields=['project', 'catalog_item'], name='labor_bud_proj_cat_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=0),
                name='check_labor_bud_quantity_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(unit_cost__gte=0),
                name='check_labor_bud_cost_non_negative'
            ),
        ]

    # -------------------------------------------------------------------
    # VALIDACIONES DE NEGOCIO
    # -------------------------------------------------------------------
    def clean(self):
        super().clean()
        errors = {}

        if self.quantity is None:
            errors['quantity'] = "La cantidad es requerida."
        elif self.quantity < 0:
            errors['quantity'] = "La cantidad no puede ser negativa."

        if self.unit_cost is None:
            errors['unit_cost'] = "El costo unitario es requerido."
        elif self.unit_cost < 0:
            errors['unit_cost'] = "El costo unitario no puede ser negativo."

        if self.subcategory_id and hasattr(self.subcategory, 'category'):
            if self.subcategory.category.name != 'Mano de Obra':
                errors['subcategory'] = (
                    f"La subcategoría '{self.subcategory.name}' pertenece a "
                    f"'{self.subcategory.category.name}', no a 'Mano de Obra'."
                )

        if errors:
            raise ValidationError(errors)

    @property
    def estimated_cost(self) -> Decimal:
        """Costo total calculado de la línea: Cantidad * Costo Unitario."""
        if self.quantity is None or self.unit_cost is None:
            return Decimal('0.00')
        return (self.quantity * self.unit_cost).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------------------------------------------------
    # FACTORY METHODS (PUNTOS ÚNICOS ATÓMICOS)
    # -------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def from_catalog(cls, *, project, catalog_item, quantity,
                      cost_override=None, detail="", contractor_name="",
                      subcategory=None):
        """
        Crea una línea de mano de obra en obra a partir de un ítem de catálogo.
        """
        effective_cost = (
            cost_override
            if cost_override is not None
            else catalog_item.suggested_cost
        )
        if effective_cost is None:
            effective_cost = Decimal('0.00')

        return cls.objects.create(
            project=project,
            catalog_item=catalog_item,
            subcategory=subcategory or catalog_item.subcategory,
            contractor_name=contractor_name or catalog_item.contractor_type,
            name=catalog_item.name,
            detail=detail or catalog_item.detail,
            unit=catalog_item.unit,
            quantity=quantity,
            unit_cost=effective_cost,
        )

    @classmethod
    @transaction.atomic
    def create_custom(cls, *, project, subcategory, name, unit,
                      quantity, unit_cost, contractor_name="", detail=""):
        """
        Crea una línea de presupuesto personalizada (Ad-hoc) que no proviene del catálogo maestro.
        """
        return cls.objects.create(
            project=project,
            catalog_item=None,
            subcategory=subcategory,
            contractor_name=contractor_name,
            name=name,
            detail=detail,
            unit=unit,
            quantity=quantity,
            unit_cost=unit_cost,
        )

    def __str__(self):
        return f"{self.name} — {self.project.name} ({self.quantity} {self.unit.abbreviation} x Bs {self.unit_cost})"
