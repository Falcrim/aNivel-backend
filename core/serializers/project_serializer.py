from rest_framework import serializers
from core.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'status',
            'status_display',
            'built_area',
            'exchange_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['status_display', 'created_at', 'updated_at']