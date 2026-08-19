from django.db import models

from .category import Category


class Subcategory(models.Model):
    """Clasificación de segundo nivel dentro de una categoría.
    Ej: Categoría 'Materiales' -> Subcategorías 'Cementos', 'Fierros'."""
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='subcategories')
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('category', 'name')
        verbose_name_plural = "subcategories"

    def __str__(self):
        return f"{self.category.name} / {self.name}"