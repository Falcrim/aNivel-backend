from decimal import Decimal
from django.db import models
from core.models import Subcategory, UnitOfMeasure, TimeStampedModel


class LaborCatalogItem(TimeStampedModel):
    """
    Ítem maestro del catálogo de tareas y actividades de Mano de Obra.
    Reutilizable entre proyectos/obras como plantilla con tarifa de referencia.
    """
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.PROTECT,
        related_name='labor_catalog_items',
        verbose_name="Subcategoría / Etapa"
    )
    name = models.CharField(max_length=255, verbose_name="Nombre de la tarea")
    detail = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Detalle técnico / Especificación",
        help_text="Especificaciones de colocación, herramientas incluidas, alcance."
    )
    unit = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name="Unidad de medida",
        help_text="Unidad en la que se cuantifica la labor (m2, ml, punto, pza, Gbl, etc.)."
    )
    suggested_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Costo sugerido (Bs)",
        help_text="Tarifa referencial de mercado en Bolivianos."
    )
    contractor_type = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Tipo de contratista sugerido",
        help_text="Ej: Albañilería, Plomería, Electricista, Marmolería."
    )
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = 'labor_catalog_item'
        verbose_name = "Ítem de Catálogo de Mano de Obra"
        verbose_name_plural = "Ítems de Catálogo de Mano de Obra"
        ordering = ['subcategory__name', 'name']
        indexes = [
            models.Index(fields=['subcategory', 'is_active'], name='labor_cat_subcat_active_idx'),
            models.Index(fields=['is_active'], name='labor_cat_is_active_idx'),
            models.Index(fields=['name'], name='labor_cat_name_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.unit.abbreviation} - Bs {self.suggested_cost})"
