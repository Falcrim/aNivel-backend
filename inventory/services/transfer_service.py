from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from inventory.models.tool import Tool, ToolStatus
from inventory.models.location import Location, LocationType
from inventory.models.tool_transfer import ToolTransfer

User = get_user_model()


class ToolTransferService:
    """
    Servicio de dominio para ejecutar traslados de herramientas entre locaciones
    de forma atómica, manteniendo la consistencia de inventario y estados operativos.
    """

    @staticmethod
    @transaction.atomic
    def execute_transfer(
        tool: Tool,
        destination_location: Location,
        responsible_person: Optional[str] = None,
        created_by: Optional[object] = None,
        notes: Optional[str] = None,
        override_status: Optional[str] = None
    ) -> ToolTransfer:
        """
        Traslada una herramienta desde su ubicación actual a una nueva ubicación,
        bloqueando la fila con select_for_update para evitar condiciones de carrera.
        """
        # Bloqueo pesimista para consistencia
        locked_tool = Tool.objects.select_for_update().get(pk=tool.pk)

        if not destination_location.is_active:
            raise ValidationError(f"La locación destino '{destination_location.name}' está inactiva.")

        if locked_tool.current_location_id == destination_location.pk:
            raise ValidationError(
                f"La herramienta ya se encuentra en '{destination_location.name}'. El destino debe ser diferente al origen."
            )

        origin_location = locked_tool.current_location

        # Determinar nuevo estado operativo según la locación de destino si no se sobreescribe
        if override_status:
            new_status = override_status
        elif locked_tool.is_active:
            if destination_location.location_type == LocationType.PROJECT:
                new_status = ToolStatus.IN_USE
            elif destination_location.location_type == LocationType.WORKSHOP:
                new_status = ToolStatus.MAINTENANCE
            elif destination_location.location_type == LocationType.WAREHOUSE:
                new_status = ToolStatus.AVAILABLE
            else:
                new_status = locked_tool.status
        else:
            # Si la herramienta está inactiva/archivada, mantiene su estado y sigue inactiva
            new_status = locked_tool.status

        locked_tool.current_location = destination_location
        locked_tool.status = new_status
        locked_tool.save(update_fields=['current_location', 'status', 'updated_at'])

        # Crear registro inmutable de transferencia
        transfer = ToolTransfer.objects.create(
            tool=locked_tool,
            origin_location=origin_location,
            destination_location=destination_location,
            responsible_person=responsible_person,
            created_by=created_by if (created_by and created_by.is_authenticated) else None,
            notes=notes
        )

        return transfer
