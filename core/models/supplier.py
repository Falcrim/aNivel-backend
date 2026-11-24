import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import get_valid_filename
from .timestamped_model import TimeStampedModel


def supplier_photo_upload_path(instance: 'Supplier', filename: str) -> str:
    """
    Ruta estructurada para logos o fotos de proveedores:
    Ejemplo: suppliers/a1b2c3d4_logo_monterrey.png
    """
    clean_name = get_valid_filename(filename)
    unique_prefix = uuid.uuid4().hex[:10]
    return f"suppliers/{unique_prefix}_{clean_name}"


class SupplierType(models.TextChoices):
    MATERIAL = 'material', 'Proveedor de Materiales'
    LABOR = 'labor', 'Contratista de Mano de Obra'
    BOTH = 'both', 'Materiales y Mano de Obra'


class Supplier(TimeStampedModel):
    """
    Empresa proveedora de materiales o contratista de mano de obra.
    Entidad canónica de primer nivel reutilizable transversalmente en
    catálogos, cotizaciones, presupuestos y compras reales.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Nombre comercial / Razón social"
    )
    supplier_type = models.CharField(
        max_length=20,
        choices=SupplierType.choices,
        default=SupplierType.MATERIAL,
        db_index=True,
        verbose_name="Tipo de Proveedor"
    )
    contact_name = models.CharField(
        max_length=150,
        blank=True,
        default='',
        verbose_name="Persona de contacto"
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="Teléfono / WhatsApp"
    )
    email = models.EmailField(
        blank=True,
        default='',
        verbose_name="Correo electrónico"
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Dirección física"
    )
    photo = models.FileField(
        upload_to=supplier_photo_upload_path,
        null=True,
        blank=True,
        verbose_name="Logotipo / Fotografía"
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name="Notas / Términos comerciales"
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="Activo"
    )

    class Meta:
        db_table = 'core_supplier'
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ['name']
        indexes = [
            models.Index(fields=['supplier_type', 'is_active'], name='core_sup_type_active_idx'),
            models.Index(fields=['name'], name='core_sup_name_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_supplier_type_display()})"

    @property
    def photo_url(self) -> str | None:
        """Retorna la URL relativa del logotipo/fotografía si existe."""
        if self.photo and hasattr(self.photo, 'url'):
            try:
                return self.photo.url
            except ValueError:
                return None
        return None

    def delete(self, *args, **kwargs):
        """Elimina la foto física del almacenamiento al borrar la entidad."""
        if self.photo and self.photo.storage.exists(self.photo.name):
            self.photo.delete(save=False)
        super().delete(*args, **kwargs)


@receiver(post_delete, sender=Supplier)
def auto_delete_supplier_photo_on_delete(sender, instance, **kwargs):
    """Garantiza la eliminación física de la foto ante borrados masivos o cascada."""
    if instance.photo and instance.photo.storage.exists(instance.photo.name):
        instance.photo.delete(save=False)
