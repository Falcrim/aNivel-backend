import os
import uuid
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import get_valid_filename
from .timestamped_model import TimeStampedModel
from .project import Project
from .subcategory import Subcategory


def project_document_upload_path(instance: 'ProjectDocument', filename: str) -> str:
    """
    Genera una ruta limpia, estructurada y única para el archivo dentro de media/.
    Ejemplo: projects/1/documents/2026/a1b2c3d4_cotizacion_fierro.pdf
    """
    clean_name = get_valid_filename(filename)
    unique_prefix = uuid.uuid4().hex[:10]
    unique_filename = f"{unique_prefix}_{clean_name}"
    year_folder = instance.created_at.strftime('%Y') if instance.created_at else 'uploads'
    return f"projects/{instance.project_id}/documents/{year_folder}/{unique_filename}"


class DocumentType(models.TextChoices):
    QUOTATION = 'quotation', 'Cotización / Proforma'
    TECHNICAL_SHEET = 'technical_sheet', 'Ficha Técnica'
    BLUEPRINT = 'blueprint', 'Plano / Especificación'
    OTHER = 'other', 'Otro Respaldo'


class ProjectDocument(TimeStampedModel):
    """
    Documentos, cotizaciones y comprobantes adjuntos a una obra/proyecto específico.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Obra / Proyecto"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Título o Concepto",
        help_text="Ej: Cotización Fierro Corrugado 1/2 - Las Lomas"
    )
    document_type = models.CharField(
        max_length=30,
        choices=DocumentType.choices,
        default=DocumentType.QUOTATION,
        verbose_name="Tipo de documento",
        db_index=True
    )
    file = models.FileField(
        upload_to=project_document_upload_path,
        verbose_name="Archivo adjunto"
    )
    file_name = models.CharField(
        max_length=255,
        verbose_name="Nombre original del archivo"
    )
    file_size = models.PositiveIntegerField(
        default=0,
        verbose_name="Tamaño en bytes"
    )
    file_extension = models.CharField(
        max_length=15,
        blank=True,
        default='',
        verbose_name="Extensión"
    )
    supplier_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Proveedor / Empresa"
    )
    quoted_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto cotizado"
    )
    currency = models.CharField(
        max_length=3,
        choices=[('BOB', 'Bolivianos (Bs)'), ('USD', 'Dólares ($)')],
        default='BOB',
        verbose_name="Moneda"
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name="Subcategoría vinculada"
    )
    notes = models.TextField(
        blank=True,
        default='',
        verbose_name="Notas u observaciones"
    )

    class Meta:
        db_table = 'core_project_document'
        verbose_name = "Documento de Obra"
        verbose_name_plural = "Documentos de Obra"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'document_type'], name='core_pdoc_proj_type_idx'),
            models.Index(fields=['project', '-created_at'], name='core_pdoc_proj_date_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_document_type_display()}) - {self.project.name}"

    def delete(self, *args, **kwargs):
        """Elimina el archivo físico del disco al eliminar la instancia."""
        if self.file and self.file.storage.exists(self.file.name):
            self.file.delete(save=False)
        super().delete(*args, **kwargs)


@receiver(post_delete, sender=ProjectDocument)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Asegura la eliminación del archivo del almacenamiento en caso de
    eliminaciones en cascada o masivas.
    """
    if instance.file and instance.file.storage.exists(instance.file.name):
        instance.file.delete(save=False)
