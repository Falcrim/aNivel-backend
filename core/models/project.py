from django.db import models


class Project(models.Model):
    """Una obra/proyecto de construcción concreto."""
    name = models.CharField(max_length=255)
    # a futuro: cliente, dirección, fecha de inicio, estado, etc.

    def __str__(self):
        return self.name