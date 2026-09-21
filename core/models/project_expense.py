import uuid
from decimal import Decimal
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.text import get_valid_filename
from .timestamped_model import TimeStampedModel
from .project import Project
from .subcategory import Subcategory


def project_expense_receipt_path(instance: 'ProjectExpense', filename: str) -> str:
    """
    Ruta para facturas, recibos y comprobantes de compras reales de obra.
    Ejemplo: projects/1/expenses/2026/a1b2c3d4_factura_1234.pdf
    """
    clean_name = get_valid_filename(filename)
    unique_prefix = uuid.uuid4().hex[:10]
    unique_filename = f"{unique_prefix}_{clean_name}"
    year_folder = instance.expense_date.strftime('%Y') if instance.expense_date else 'general'
    return f"projects/{instance.project_id}/expenses/{year_folder}/{unique_filename}"


class ExpenseCategoryType(models.TextChoices):
    MATERIALS = 'materials', 'Materiales'
    LABOR = 'labor', 'Mano de Obra'
    OPERATING = 'operating', 'Gastos Operativos'
    ADMINISTRATIVE = 'administrative', 'Costos Administrativos'
    OTHER = 'other', 'Otros Gastos'


class PaymentStatus(models.TextChoices):
    PAID = 'paid', 'Pagado'
    IN_PROCESS = 'in_process', 'En proceso'
    PENDING = 'pending', 'Por cobrar'


class ProjectExpense(TimeStampedModel):
    """
    Registro individual de compra, desembolso o pago real ejecutado en una obra.
    Sirve como base para el historial de compras y la posterior Rendición de Fondos.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='expenses',
        verbose_name="Obra / Proyecto"
    )
    category_type = models.CharField(
        max_length=30,
        choices=ExpenseCategoryType.choices,
        default=ExpenseCategoryType.MATERIALS,
        verbose_name="Tipo de Categoría",
        db_index=True
    )
    subcategory = models.ForeignKey(
        Subcategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses',
        verbose_name="Subcategoría / Etapa",
        help_text="Ej: Acero Corrugado, Hormigón Premezclado, Estructuras"
    )
    item_name = models.CharField(
        max_length=255,
        verbose_name="Descripción del Ítem",
        help_text="Ej: Barra de acero corrugado 3/8\"x12m. (10mm²)"
    )
    unit_name = models.CharField(
        max_length=50,
        default='Pza',
        verbose_name="Unidad",
        help_text="Ej: Barra, Rollo, m³, Kg, Gbl"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('1.00'),
        verbose_name="Cantidad"
    )
    unit_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precio Unitario (Bs)"
    )
    total_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Precio Total (Bs)"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PAID,
        verbose_name="Estado de Pago",
        db_index=True
    )
    expense_date = models.DateField(
        verbose_name="Fecha de Compra / Pago",
        db_index=True
    )
    payment_method = models.CharField(
        max_length=100,
        blank=True,
        default='AL CONTADO',
        verbose_name="Forma de Pago / Modalidad",
        help_text="Ej: AL CONTADO, PAGADO CON FAR, TRANSFERENCIA BANCARIA"
    )
    supplier_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Proveedor / Empresa / Contratista"
    )
    details = models.TextField(
        blank=True,
        default='',
        verbose_name="Detalle / Observaciones",
        help_text="Ej: Se pagó con factura pero será devuelto el precio del mismo"
    )
    rendicion_number = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name="N° de Rendición de Fondos",
        help_text="Ej: Nr° 04 o Rendición 01",
        db_index=True
    )

    # Respaldo físico (Factura / Recibo / Comprobante)
    receipt_file = models.FileField(
        upload_to=project_expense_receipt_path,
        null=True,
        blank=True,
        verbose_name="Factura / Comprobante adjunto"
    )
    receipt_number = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name="N° de Factura o Recibo"
    )
    receipt_file_name = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Nombre original del comprobante"
    )
    receipt_file_size = models.PositiveIntegerField(
        default=0,
        verbose_name="Tamaño en bytes"
    )

    class Meta:
        db_table = 'core_project_expense'
        verbose_name = "Gasto Real de Obra"
        verbose_name_plural = "Gastos Reales de Obra"
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['project', '-expense_date'], name='core_pexp_proj_date_idx'),
            models.Index(fields=['project', 'category_type'], name='core_pexp_proj_cat_idx'),
            models.Index(fields=['project', 'payment_status'], name='core_pexp_proj_stat_idx'),
            models.Index(fields=['project', 'rendicion_number'], name='core_pexp_proj_rend_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.item_name} - Bs {self.total_price} ({self.get_payment_status_display()})"

    def save(self, *args, **kwargs):
        # Auto-calcular total_price si no se especificó directamente
        if self.unit_price and self.quantity and not self.total_price:
            self.total_price = (self.quantity * self.unit_price).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Elimina el comprobante físico del almacenamiento."""
        if self.receipt_file and self.receipt_file.storage.exists(self.receipt_file.name):
            self.receipt_file.delete(save=False)
        super().delete(*args, **kwargs)


@receiver(post_delete, sender=ProjectExpense)
def auto_delete_receipt_file(sender, instance, **kwargs):
    if instance.receipt_file and instance.receipt_file.storage.exists(instance.receipt_file.name):
        instance.receipt_file.delete(save=False)
