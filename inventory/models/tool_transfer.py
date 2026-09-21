from django.db import models
from django.conf import settings
from core.models.timestamped_model import TimeStampedModel
from .location import Location
from .tool import Tool


class ToolTransfer(TimeStampedModel):
    """
    Registro inmutable de traslados/movimientos de herramientas y equipos
    entre almacenes, talleres y frentes de obra.
    """
    tool = models.ForeignKey(
        Tool,
        on_delete=models.CASCADE,
        related_name='transfers',
        verbose_name="Herramienta / Equipo",
        db_index=True
    )
    origin_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='transfers_out',
        verbose_name="Locación de origen",
        db_index=True
    )
    destination_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name='transfers_in',
        verbose_name="Locación de destino",
        db_index=True
    )
    transfer_date = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Fecha del traslado")
    responsible_person = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Responsable en terreno / Receptor"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_tool_transfers',
        verbose_name="Registrado por (Usuario del sistema)"
    )
    notes = models.TextField(null=True, blank=True, verbose_name="Observaciones / Motivo")

    class Meta:
        db_table = 'inventory_tool_transfer'
        verbose_name = "Traslado de Herramienta"
        verbose_name_plural = "Traslados de Herramientas"
        ordering = ['-transfer_date']
        indexes = [
            models.Index(fields=['tool', '-transfer_date']),
            models.Index(fields=['destination_location', '-transfer_date']),
        ]

    def __str__(self) -> str:
        return f"Traslado de {self.tool.code}: {self.origin_location.name} -> {self.destination_location.name}"
