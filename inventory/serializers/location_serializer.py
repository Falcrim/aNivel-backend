from rest_framework import serializers
from inventory.models.location import Location, LocationType
from core.models.project import Project


class LocationSerializer(serializers.ModelSerializer):
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True, default=None)
    tools_count = serializers.SerializerMethodField()

    def get_tools_count(self, obj) -> int:
        return obj.tools_currently_here.filter(is_active=True).count()

    class Meta:
        model = Location
        fields = [
            'id',
            'name',
            'code',
            'location_type',
            'location_type_display',
            'project',
            'project_name',
            'address',
            'is_active',
            'tools_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, attrs):
        project = attrs.get('project', getattr(self.instance, 'project', None))
        location_type = attrs.get('location_type', getattr(self.instance, 'location_type', LocationType.WAREHOUSE))

        # Si se vincula a una obra y el tipo es WAREHOUSE, sugerir o ajustar a PROJECT
        if project and location_type == LocationType.WAREHOUSE:
            attrs['location_type'] = LocationType.PROJECT

        return attrs
