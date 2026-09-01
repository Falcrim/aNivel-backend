from django.db import models


class TimeStampedModel(models.Model):
    """
    Modelo base abstracto que provee campos de auditoría temporal
    (created_at y updated_at) para rastrear creación y última modificación.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    class Meta:
        abstract = True
