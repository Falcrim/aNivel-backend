from django.db import models
from .timestamped_model import TimeStampedModel


class UnitOfMeasure(TimeStampedModel):
    """Unidad en la que se mide la necesidad en obra: ml, m2, m3, kg, pza..."""
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre")
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name="Abreviación")

    class Meta:
        db_table = 'core_unit_of_measure'
        verbose_name = "Unidad de Medida"
        verbose_name_plural = "Unidades de Medida"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
