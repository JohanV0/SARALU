from django.db import migrations


CATEGORIAS = [
    'PASTELES_DE_SABORES',
    'CUPCAKES',
    'GALLETAS',
    'POSTRES_INDIVIDUALES',
    'TARTAS',
    'PAVLOVAS',
    'BROWNIES',
]


def crear_categorias(apps, schema_editor):
    Categoria = apps.get_model('reposteria', 'Categoria')
    for code in CATEGORIAS:
        Categoria.objects.get_or_create(
            categoria=code,
            defaults={'imagen_principal': 'img/logo.png'}
        )


def borrar_categorias(apps, schema_editor):
    Categoria = apps.get_model('reposteria', 'Categoria')
    Categoria.objects.filter(categoria__in=CATEGORIAS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('reposteria', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(crear_categorias, borrar_categorias),
    ]