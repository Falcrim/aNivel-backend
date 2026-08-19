from rest_framework import viewsets

from core.models import Project
from core.serializers.project_serializer import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer