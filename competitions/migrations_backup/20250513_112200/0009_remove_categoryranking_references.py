# Generated manually to remove problematic CategoryRanking references

from django.db import migrations


class Migration(migrations.Migration):
    """
    Cette migration a pour but de supprimer toutes les références au modèle CategoryRanking
    qui causent des erreurs dans la séquence de migrations.
    """

    dependencies = [
        ('competitions', '0007_merge_20250513_1045'),
    ]

    operations = [
        # Vide intentionnellement - pour être appliqué avant la création correcte de CategoryRanking
    ]