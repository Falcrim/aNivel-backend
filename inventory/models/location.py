from django.db import models
from core.models.timestamped_model import TimeStampedModel


class LocationType(models.TextChoices):
    WAREHOUSE = 'WAREHOUSE', 'Almacén / Depósito Central'
    PROJECT = 'PROJECT', 'Frente de Obra'
    WORKSHOP = 'WORKSHOP', 'Taller de Mantenimiento'
    OTHER = 'OTHER', 'Otro'


class Location(TimeStampedModel):
    """
    Representa un sitio físico donde pueden encontrarse herramientas o materiales:
    almacenes fijos, depósitos, talleres o frentes de obra específicos.
    """
    name = models.CharField(max_length=255, verbose_name="Nombre de la locación")
    code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Código de locación"
    )
    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.WAREHOUSE,
        db_index=True,
        verbose_name="Tipo de locación"
    )
    project = models.ForeignKey(
        'core.Project',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_locations',
        verbose_name="Obra vinculada",
        db_index=True
    )
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name="Dirección / Ubicación")
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activa")

    class Meta:
        db_table = 'inventory_location'
        verbose_name = "Locación"
        verbose_name_plural = "Locaciones"
        ordering = ['name']
        indexes = [
            models.Index(fields=['location_type', 'is_active']),
            models.Index(fields=['project', 'is_active']),
        ]

    def __str__(self) -> str:
        if self.project:
            return f"{self.name} (Obra: {self.project.name})"
        return self.name
