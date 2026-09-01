from django.db import models
from core.models import UnitOfMeasure, PurchaseUnit, TimeStampedModel


class MaterialConversionSpec(TimeStampedModel):
    """
    Mixin abstracto con especificaciones técnicas, comerciales y de conversión.
    Compartido entre MaterialCatalogItem y MaterialBudgetItem.
    """
    unit_measure = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name="Unidad de medida",
        help_text="Unidad en la que se cuantifica la necesidad en obra (ej. ml, m2, m3, kg)."
    )
    unit_purchase = models.ForeignKey(
        PurchaseUnit,
        on_delete=models.PROTECT,
        related_name='+',
        verbose_name="Unidad de compra",
        help_text="Unidad comercial en la que se adquiere (ej. barra, bolsa, tubo, balde, Gbl)."
    )
    conversion_factor = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Factor de conversión",
        help_text="1 unidad_purchase = X unidad_measure. Ej: 1 barra = 12.00 ml. "
                  "Nulo permitido solo para ítems globales (is_global=True) en presupuesto."
    )
    weight_per_purchase_unit = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Peso por unidad de compra",
        help_text="Peso en kg de 1 unidad_purchase. Solo informativo/reportería "
                  "(ej. sumar toneladas de fierro), no afecta el cálculo de compra."
    )
    waste_pct = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0,
        verbose_name="Porcentaje de desperdicio",
        help_text="Desperdicio estimado (ej. 0.10 = 10%). En catálogo es el valor sugerido; "
                  "en presupuesto es el valor aplicable a la obra."
    )
    price_per_purchase_unit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Precio por unidad de compra",
        help_text="Costo o precio por unidad de compra (ej. Bs por barra/bolsa/balde). "
                  "En catálogo es referencial; en presupuesto es el precio de la obra."
    )

    class Meta:
        abstract = True
