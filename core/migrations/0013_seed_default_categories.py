from django.db import migrations


DEFAULT_CATEGORIES = (
    ('materials', 'Materiales', True),
    ('labor', 'Mano de Obra', True),
    ('operating', 'Gastos Operativos', False),
    ('administrative', 'Gastos Administrativos', False),
)


def seed_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')

    for code, default_name, is_active in DEFAULT_CATEGORIES:
        if Category.objects.filter(code=code).exists():
            continue

        candidate_name = default_name
        counter = 2
        while Category.objects.filter(name=candidate_name).exists():
            candidate_name = f'{default_name} ({counter})'
            counter += 1

        Category.objects.create(
            code=code,
            name=candidate_name,
            is_active=is_active,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_category_code_and_is_active'),
    ]

    operations = [
        migrations.RunPython(seed_default_categories, migrations.RunPython.noop),
    ]
