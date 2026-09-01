import math
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from core.models import Project, Subcategory
from .conversion_spec import MaterialConversionSpec
from .material_catalog import MaterialCatalogItem


class MaterialBudgetItemQuerySet(models.QuerySet):
    """QuerySet personalizado para consultas optimizadas y expresivas de presupuesto."""

    def for_project(self, project_id):
        """Filtra ítems de un proyecto específico."""
        return self.filter(project_id=project_id)

    def for_subcategory(self, subcategory_id):
        """Filtra ítems de una subcategoría específica."""
        return self.filter(subcategory_id=subcategory_id)

    def standard_items(self):
        """Filtra ítems normales (calculados con cómputo de obra)."""
        return self.filter(is_global=False)

    def global_items(self):
        """Filtra ítems globales (paquetes cerrados / compras preventivas)."""
        return self.filter(is_global=True)

    def with_relations(self):
        """Pre-carga todas las relaciones ForeignKey para evitar consultas N+1."""
        return self.select_related(
            'project',
            'subcategory',
            'subcategory__category',
            'unit_measure',
            'unit_purchase',
            'catalog_item',
            'catalog_item__subcategory',
            'catalog_item__subcategory__category',
            'catalog_item__unit_measure',
            'catalog_item__unit_purchase',
        )


class MaterialBudgetItem(MaterialConversionSpec):
    """
    Línea de presupuesto de materiales para una obra concreta.

    Es un SNAPSHOT del catálogo en el momento en que se agregó a la obra:
    todos los campos de conversión, peso, desperdicio y precio se heredan
    de MaterialConversionSpec y quedan editables de forma independiente.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='material_budget_items',
        verbose_name="Proyecto"
    )
    catalog_item = models.ForeignKey(
        MaterialCatalogItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='budget_instances',
        verbose_name="Ítem de catálogo origen",
        help_text="Referencia al ítem de catálogo de origen (solo trazabilidad, no se usa en cálculos)."
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.PROTECT,
        related_name='material_budget_items',
        verbose_name="Subcategoría",
        help_text="Subcategoría para organización y agrupación del presupuesto en obra."
    )

    name = models.CharField(max_length=255, verbose_name="Nombre")
    detail = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Detalle / Especificación",
        help_text="Marca, color, especificación puntual para esta obra."
    )

    # Ítem "Gbl": compra preventiva o paquete cerrado (ej. "Rodillos y Brochas").
    # No se calcula por cómputo de obra: el usuario ingresa directamente la cantidad
    # de compra y precio.
    is_global = models.BooleanField(
        default=False,
        verbose_name="¿Es ítem global?",
        help_text="Marcar si es una compra en paquete/global sin cómputo métrico."
    )

    # Cantidad requerida en obra, en unit_measure (ej. 120.00 ml).
    quantity_obra = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Cantidad requerida en obra",
        help_text="Cómputo neto requerido en obra (solo para ítems no globales)."
    )

    # Cantidad final a comprar, en unit_purchase.
    # - Ítem normal: calculada con redondeo hacia arriba (ceil).
    # - Ítem global: ingresada directamente por el usuario.
    quantity_purchase = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="Cantidad a comprar",
        help_text="Cantidad a comprar en unidad comercial. Calculada o ingresada directamente."
    )

    objects = MaterialBudgetItemQuerySet.as_manager()

    class Meta:
        db_table = 'materials_budget_item'
        verbose_name = "Ítem de Presupuesto de Materiales"
        verbose_name_plural = "Ítems de Presupuesto de Materiales"
        ordering = ['project', 'subcategory__name', 'name']
        indexes = [
            models.Index(fields=['project', 'subcategory'], name='mat_bud_proj_subcat_idx'),
            models.Index(fields=['project', 'is_global'], name='mat_bud_proj_global_idx'),
            models.Index(fields=['project', 'catalog_item'], name='mat_bud_proj_cat_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity_purchase__gte=0),
                name='check_mat_bud_quantity_purchase_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_obra__gte=0) | models.Q(quantity_obra__isnull=True),
                name='check_mat_bud_quantity_obra_non_negative'
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_purchase_unit__gte=0) | models.Q(price_per_purchase_unit__isnull=True),
                name='check_mat_bud_price_non_negative'
            ),
        ]

    # -------------------------------------------------------------------
    # VALIDACIÓN DE REGLAS DE NEGOCIO (Refactorizada y Limpia)
    # -------------------------------------------------------------------
    def clean(self):
        super().clean()
        errors = {}

        if self.is_global:
            self._validate_global_item(errors)
        else:
            self._validate_standard_item(errors)

        self._validate_pricing(errors)

        if errors:
            raise ValidationError(errors)

    def _validate_standard_item(self, errors):
        """Valida que un ítem normal cuente con factor de conversión y cómputo válidos."""
        if not self.conversion_factor or self.conversion_factor <= 0:
            errors['conversion_factor'] = "El factor de conversión es requerido y debe ser mayor a 0 cuando el ítem no es global."
        if self.quantity_obra is None:
            errors['quantity_obra'] = "La cantidad en obra (cómputo) es requerida cuando el ítem no es global."
        elif self.quantity_obra < 0:
            errors['quantity_obra'] = "La cantidad en obra no puede ser negativa."

    def _validate_global_item(self, errors):
        """Valida que un ítem global no incluya cómputo y tenga cantidad de compra válida."""
        if self.quantity_obra is not None:
            errors['quantity_obra'] = "Un ítem global no debe tener cómputo de obra (quantity_obra)."
        if self.quantity_purchase is None or self.quantity_purchase <= 0:
            errors['quantity_purchase'] = "Un ítem global requiere una cantidad de compra mayor a 0."

    def _validate_pricing(self, errors):
        """Valida que el precio unitario esté presente y sea válido."""
        if self.price_per_purchase_unit is None:
            errors['price_per_purchase_unit'] = "El precio por unidad de compra es requerido en el presupuesto."
        elif self.price_per_purchase_unit < 0:
            errors['price_per_purchase_unit'] = "El precio por unidad de compra no puede ser negativo."

    # -------------------------------------------------------------------
    # CÁLCULO DE CANTIDAD A COMPRAR (solo aplica a ítems no-globales)
    # Redondea siempre hacia arriba (ceil) porque no se compran fracciones
    # de una unidad comercial.
    # -------------------------------------------------------------------
    def calculate_quantity_purchase(self):
        if not self.conversion_factor or self.conversion_factor <= 0 or self.quantity_obra is None:
            return Decimal('0')

        waste = self.waste_pct if self.waste_pct is not None else Decimal('0')
        cantidad_neta = self.quantity_obra * (Decimal('1') + waste)
        unidades_necesarias = cantidad_neta / self.conversion_factor
        return Decimal(math.ceil(unidades_necesarias))

    @property
    def weight_total(self):
        """Peso total estimado en kg de esta línea, solo referencial."""
        if not self.weight_per_purchase_unit or not self.quantity_purchase:
            return None
        return self.quantity_purchase * self.weight_per_purchase_unit

    @property
    def estimated_cost(self):
        """Costo total estimado de la línea."""
        if self.quantity_purchase is None or self.price_per_purchase_unit is None:
            return Decimal('0.00')
        return self.quantity_purchase * self.price_per_purchase_unit

    # -------------------------------------------------------------------
    # save()
    # -------------------------------------------------------------------
    def save(self, *args, **kwargs):
        if not self.is_global:
            self.quantity_purchase = self.calculate_quantity_purchase()
        self.full_clean()
        super().save(*args, **kwargs)

    # -------------------------------------------------------------------
    # FACTORY METHODS (PUNTOS ÚNICOS DE CREACIÓN ATÓMICOS)
    # -------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def from_catalog(cls, *, project, catalog_item, quantity_obra,
                      detail="", waste_pct=None, price_override=None,
                      subcategory=None):
        """
        Crea una línea NORMAL a partir de un ítem de catálogo.
        Calcula quantity_purchase con redondeo hacia arriba.
        """
        effective_price = (
            price_override
            if price_override is not None
            else catalog_item.price_per_purchase_unit
        )
        if effective_price is None:
            effective_price = Decimal('0.00')

        return cls.objects.create(
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
            quantity_purchase=Decimal('0'),  # recalculado por save()
        )

    @classmethod
    @transaction.atomic
    def from_catalog_global(cls, *, project, catalog_item, quantity_purchase,
                             price_per_purchase_unit=None, detail="", subcategory=None):
        """
        Crea una línea GLOBAL a partir de un ítem de catálogo.
        No hay cómputo ni cálculo de conversión.
        """
        effective_price = (
            price_per_purchase_unit
            if price_per_purchase_unit is not None
            else catalog_item.price_per_purchase_unit
        )
        if effective_price is None:
            effective_price = Decimal('0.00')

        return cls.objects.create(
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
    def create_custom(cls, *, project, subcategory, name, unit_measure,
                      unit_purchase, price_per_purchase_unit, is_global=False,
                      quantity_obra=None, quantity_purchase=None,
                      conversion_factor=None, weight_per_purchase_unit=None,
                      waste_pct=Decimal('0'), detail=""):
        """
        Crea una línea de presupuesto personalizada (Ad-hoc) que no proviene
        del catálogo maestro.
        """
        return cls.objects.create(
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

    def __str__(self):
        return f"{self.name} — {self.project.name} ({self.quantity_purchase} {self.unit_purchase.abbreviation})"
