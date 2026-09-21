from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
    verbose_name = 'Inventario de Herramientas y Locaciones'

    def ready(self):
        import inventory.signals.project_signals  # noqa
