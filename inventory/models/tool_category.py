from django.db import models
from core.models.timestamped_model import TimeStampedModel


class ToolCategory(TimeStampedModel):
    """
    Categoría para clasificar herramientas y equipos (ej: Manuales, Eléctricas, Maquinaria, Topografía).
    """
    name = models.CharField(max_length=100, unique=True, db_index=True, verbose_name="Nombre de la categoría")
    description = models.TextField(null=True, blank=True, verbose_name="Descripción")

    class Meta:
        db_table = 'inventory_tool_category'
        verbose_name = "Categoría de Herramienta"
        verbose_name_plural = "Categorías de Herramientas"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name
