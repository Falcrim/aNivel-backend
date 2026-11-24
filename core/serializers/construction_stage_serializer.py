from rest_framework import serializers
from core.models import ConstructionStage


class ConstructionStageSerializer(serializers.ModelSerializer):
    """Serializer para CRUD de Etapas Constructivas Dinámicas."""

    class Meta:
        model = ConstructionStage
        fields = [
            'id',
            'name',
            'description',
            'order',
            'color',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
