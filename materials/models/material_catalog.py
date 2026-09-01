from django.db import models
from core.models import Subcategory
from .conversion_spec import MaterialConversionSpec


class MaterialCatalogItem(MaterialConversionSpec):
    """
    Ítem maestro del catálogo de materiales, reutilizable entre obras.
    No pertenece a ninguna obra en particular: es la plantilla maestra que luego
    se copia (snapshot) hacia MaterialBudgetItem cuando se arma un presupuesto.
    """
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.PROTECT,
        related_name='material_catalog_items',
        verbose_name="Subcategoría"
    )
    name = models.CharField(max_length=255, verbose_name="Nombre")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        db_table = 'materials_catalog_item'
        verbose_name = "Ítem de Catálogo de Materiales"
        verbose_name_plural = "Ítems de Catálogo de Materiales"
        ordering = ['subcategory__name', 'name']
        indexes = [
            models.Index(fields=['subcategory', 'is_active'], name='mat_cat_subcat_active_idx'),
            models.Index(fields=['is_active'], name='mat_cat_is_active_idx'),
            models.Index(fields=['name'], name='mat_cat_name_idx'),
        ]

    def __str__(self):
        factor_str = f" (1 {self.unit_purchase.abbreviation} = {self.conversion_factor} {self.unit_measure.abbreviation})" if self.conversion_factor else ""
        return f"{self.name}{factor_str}"
