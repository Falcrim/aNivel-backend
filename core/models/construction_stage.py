from django.db import models
from .timestamped_model import TimeStampedModel


class ConstructionStage(TimeStampedModel):
    """
    Etapa constructiva dinámica (ej: Obra Bruta / Gruesa, Obra Fina, Instalaciones, Equipamiento).
    Permite a la constructora crear y clasificar etapas de avance para obras y partidas
    de presupuesto sin esquemas fijos en código.
    """
    name = models.CharField(max_length=120, unique=True, verbose_name="Nombre de la etapa")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción / Alcance")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")
    color = models.CharField(max_length=30, default="amber", verbose_name="Color temático")
    is_active = models.BooleanField(default=True, verbose_name="Activa")

    class Meta:
        db_table = 'core_construction_stage'
        verbose_name = "Etapa Constructiva"
        verbose_name_plural = "Etapas Constructivas"
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['order'], name='stage_order_idx'),
            models.Index(fields=['is_active'], name='stage_is_active_idx'),
        ]

    def __str__(self):
        return self.name
