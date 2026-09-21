from typing import Optional
from core.models.project import Project
from inventory.models.location import Location, LocationType


class LocationService:
    """
    Servicio de dominio para gestionar el ciclo de vida y sincronización de locaciones.
    """

    @staticmethod
    def get_or_create_project_location(project: Project) -> Location:
        """
        Garantiza que exista una locación de tipo PROJECT vinculada a la obra dada.
        """
        location, created = Location.objects.get_or_create(
            project=project,
            defaults={
                'name': f"Obra: {project.name}",
                'location_type': LocationType.PROJECT,
                'is_active': True,
            }
        )
        # Si ya existía pero el nombre cambió, sincronizar
        expected_name = f"Obra: {project.name}"
        if not created and location.name != expected_name:
            location.name = expected_name
            location.save(update_fields=['name', 'updated_at'])
            
        return location

    @staticmethod
    def update_project_location(project: Project) -> Optional[Location]:
        """
        Actualiza el nombre de la locación vinculada cuando el proyecto es modificado.
        """
        location = Location.objects.filter(project=project).first()
        if location:
            expected_name = f"Obra: {project.name}"
            if location.name != expected_name:
                location.name = expected_name
                location.save(update_fields=['name', 'updated_at'])
            return location
        else:
            return LocationService.get_or_create_project_location(project)
