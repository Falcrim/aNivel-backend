from django.db import models
from django.utils.text import slugify
from .timestamped_model import TimeStampedModel


def infer_category_code(name: str) -> str:
    """Infiere el código interno canónico a partir del nombre de la categoría."""
    low = (name or '').lower()
    if 'material' in low:
        return 'materials'
    if 'mano' in low or 'obra' in low:
        return 'labor'
    if 'operativ' in low:
        return 'operating'
    if 'admin' in low:
        return 'administrative'
    return slugify(name) or 'category'


class Category(TimeStampedModel):
    """Categoría de primer nivel: Materiales, Mano de Obra, Gastos Operativos, Gastos Administrativos."""
    code = models.CharField(max_length=50, unique=True, verbose_name="Código interno")
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    is_active = models.BooleanField(default=True, verbose_name="Módulo activo")

    class Meta:
        db_table = 'core_category'
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.code:
            base_code = infer_category_code(self.name)
            candidate = base_code
            counter = 2
            while Category.objects.filter(code=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base_code}-{counter}"
                counter += 1
            self.code = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
