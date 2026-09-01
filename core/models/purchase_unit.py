from django.db import models
from .timestamped_model import TimeStampedModel


class PurchaseUnit(TimeStampedModel):
    """Unidad en la que se compra el material: tubo, rollo, bolsa, barra, galón, Gbl..."""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name="Abreviación")

    class Meta:
        db_table = 'core_purchase_unit'
        verbose_name = "Unidad de Compra"
        verbose_name_plural = "Unidades de Compra"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
