from django.db import models
from .timestamped_model import TimeStampedModel


class Project(TimeStampedModel):
    """Una obra/proyecto de construcción concreto."""
    name = models.CharField(max_length=255, verbose_name="Nombre")
    # a futuro: cliente, dirección, fecha de inicio, estado, etc.

    class Meta:
        db_table = 'core_project'
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['name']

    def __str__(self):
        return self.name