from decimal import Decimal
from django.db import models
from .timestamped_model import TimeStampedModel


class ProjectStatus(models.TextChoices):
    BUDGET = 'budget', 'En Presupuesto'
    ACTIVE = 'active', 'Activa'
    PAUSED = 'paused', 'Pausada'
    CANCELLED = 'cancelled', 'Cancelada'
    COMPLETED = 'completed', 'Finalizada'


class Project(TimeStampedModel):
    """Una obra/proyecto de construcción concreto."""
    name = models.CharField(max_length=255, verbose_name="Nombre")
    status = models.CharField(
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.BUDGET,
        verbose_name="Estado de la obra"
    )
    built_area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Superficie construida (m2)",
        help_text="Metros cuadrados totales construidos de la obra."
    )
    exchange_rate = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('6.9700'),
        verbose_name="Tipo de cambio (USD)",
        help_text="Tipo de cambio aplicable (Bs por USD)."
    )

    class Meta:
        db_table = 'core_project'
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['name']
        indexes = [
            models.Index(fields=['status'], name='core_proj_status_idx'),
            models.Index(fields=['name'], name='core_proj_name_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"