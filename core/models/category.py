from django.db import models
from .timestamped_model import TimeStampedModel


class Category(TimeStampedModel):
    """Categoría de primer nivel: Materiales, Mano de Obra, Gastos Generales, etc."""
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")

    class Meta:
        db_table = 'core_category'
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def __str__(self):
        return self.name