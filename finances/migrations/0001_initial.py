from django.db import migrations


class Migration(migrations.Migration):
    """
    Migration initiale vide pour finances.
    Sert de point d'entrée pour les migrations suivantes.
    """
    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        # Pas d'opérations, simplement un marqueur initial
    ]