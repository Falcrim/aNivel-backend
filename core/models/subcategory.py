from django.db import models
from .category import Category
from .timestamped_model import TimeStampedModel


class Subcategory(TimeStampedModel):
    """Clasificación de segundo nivel dentro de una categoría.
    Ej: Categoría 'Materiales' -> Subcategorías 'Cementos', 'Fierros'."""
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='subcategories',
        verbose_name="Categoría"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre")

    class Meta:
        db_table = 'core_subcategory'
        constraints = [
            models.UniqueConstraint(fields=['category', 'name'], name='unique_subcategory_per_category')
        ]
        verbose_name = "Subcategoría"
        verbose_name_plural = "Subcategorías"
        ordering = ['category__name', 'name']

    def __str__(self):
        return f"{self.category.name} / {self.name}"