from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.project import Project
from inventory.services.location_service import LocationService


@receiver(post_save, sender=Project)
def auto_create_or_update_project_location(sender, instance: Project, created: bool, **kwargs):
    """
    Señal que crea o actualiza automáticamente una Locación vinculada
    cuando se crea o modifica una Obra (Project).
    """
    if created:
        LocationService.get_or_create_project_location(instance)
    else:
        LocationService.update_project_location(instance)
