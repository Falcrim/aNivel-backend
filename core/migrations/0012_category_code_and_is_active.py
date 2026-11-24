from django.db import migrations, models
from django.utils.text import slugify


def populate_category_codes(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    used_codes = set()

    for cat in Category.objects.all().order_by('id'):
        low = (cat.name or '').lower()
        if 'material' in low:
            base_code = 'materials'
            is_active = True
        elif 'mano' in low or 'obra' in low:
            base_code = 'labor'
            is_active = True
        elif 'operativ' in low:
            base_code = 'operating'
            is_active = False
        elif 'admin' in low:
            base_code = 'administrative'
            is_active = False
        else:
            base_code = slugify(cat.name) or f'cat-{cat.id}'
            is_active = True

        candidate = base_code
        counter = 2
        while candidate in used_codes:
            candidate = f'{base_code}-{counter}'
            counter += 1

        used_codes.add(candidate)
        cat.code = candidate
        cat.is_active = is_active
        cat.save(update_fields=['code', 'is_active'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_remove_projectdocument_core_pdoc_proj_type_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='code',
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                verbose_name='Código interno',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(
                default=True,
                verbose_name='Módulo activo',
            ),
        ),
        migrations.RunPython(populate_category_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='category',
            name='code',
            field=models.CharField(
                max_length=50,
                unique=True,
                verbose_name='Código interno',
            ),
        ),
    ]
