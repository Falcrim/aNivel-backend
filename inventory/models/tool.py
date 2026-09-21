from django.db import models
from core.models.timestamped_model import TimeStampedModel
from .location import Location
from .tool_category import ToolCategory


class ToolStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Disponible en Almacén'
    IN_USE = 'IN_USE', 'En Uso / En Obra'
    MAINTENANCE = 'MAINTENANCE', 'En Mantenimiento / Reparación'
    DAMAGED = 'DAMAGED', 'Dañada / Fuera de Servicio'
    LOST = 'LOST', 'Extraviada / De Baja'


class Tool(TimeStampedModel):
    """
    Herramienta, maquinaria o equipo de trabajo registrado en el inventario.
    """
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código de activo / inventario"
    )
    name = models.CharField(max_length=255, db_index=True, verbose_name="Nombre")
    category = models.ForeignKey(
        ToolCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tools',
        verbose_name="Categoría",
        db_index=True
    )
    detail = models.TextField(null=True, blank=True, verbose_name="Detalle / Especificación")
    brand = models.CharField(max_length=100, null=True, blank=True, verbose_name="Marca")
    model_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="Modelo")
    serial_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="Número de serie")
    
    current_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='tools_currently_here',
        verbose_name="Ubicación actual",
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=ToolStatus.choices,
        default=ToolStatus.AVAILABLE,
        db_index=True,
        verbose_name="Estado operativo"
    )
    
    purchase_date = models.DateField(null=True, blank=True, verbose_name="Fecha de compra")
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio de compra"
    )
    is_active = models.BooleanField(default=True, db_index=True, verbose_name="Activa")

    class Meta:
        db_table = 'inventory_tool'
        verbose_name = "Herramienta / Maquinaria"
        verbose_name_plural = "Herramientas y Maquinarias"
        ordering = ['name']
        indexes = [
            models.Index(fields=['current_location', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['code', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"[{self.code}] {self.name}"
