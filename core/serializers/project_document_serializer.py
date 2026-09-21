import os
from rest_framework import serializers
from core.models import ProjectDocument, Project, Subcategory

ALLOWED_EXTENSIONS = {
    'pdf', 'xlsx', 'xls', 'csv', 'docx', 'doc',
    'png', 'jpg', 'jpeg', 'webp'
}
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


def format_file_size(size_in_bytes: int) -> str:
    """Convierte bytes a un formato legible (B, KB, MB, GB)."""
    if not size_in_bytes:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.1f} {unit}" if unit != 'B' else f"{size_in_bytes} B"
        size_in_bytes /= 1024
    return f"{size_in_bytes:.1f} TB"


class ProjectDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True, default='')
    file_url = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDocument
        fields = [
            'id',
            'project',
            'project_name',
            'title',
            'document_type',
            'document_type_display',
            'file',
            'file_url',
            'file_name',
            'file_size',
            'file_size_formatted',
            'file_extension',
            'supplier_name',
            'quoted_amount',
            'currency',
            'subcategory',
            'subcategory_name',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'file_name',
            'file_size',
            'file_size_formatted',
            'file_extension',
            'file_url',
            'document_type_display',
            'project_name',
            'subcategory_name',
            'created_at',
            'updated_at',
        ]

    def get_file_url(self, obj: ProjectDocument) -> str:
        if not obj.file:
            return ''
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_file_size_formatted(self, obj: ProjectDocument) -> str:
        return format_file_size(obj.file_size)

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("Debe proporcionar un archivo.")

        # Validar extensión
        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if ext not in ALLOWED_EXTENSIONS:
            allowed_list = ', '.join(sorted(ALLOWED_EXTENSIONS))
            raise serializers.ValidationError(
                f"Extensión .{ext} no permitida. Formatos válidos: {allowed_list}."
            )

        # Validar tamaño
        if value.size > MAX_FILE_SIZE_BYTES:
            raise serializers.ValidationError(
                f"El archivo supera el tamaño máximo permitido de 25 MB ({format_file_size(value.size)})."
            )

        return value

    def create(self, validated_data):
        uploaded_file = validated_data.get('file')
        if uploaded_file:
            orig_name = uploaded_file.name
            ext = os.path.splitext(orig_name)[1].lower().replace('.', '')
            validated_data['file_name'] = orig_name
            validated_data['file_size'] = uploaded_file.size
            validated_data['file_extension'] = ext
            if not validated_data.get('title'):
                validated_data['title'] = os.path.splitext(orig_name)[0]

        return super().create(validated_data)
