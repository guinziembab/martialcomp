# Generated manually to handle missing tables - SQLite compatible

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('multitenant', '0006_alter_featureusage_id_alter_payperusefeature_id_and_more'),
    ]

    operations = [
        # Migration vide pour compatibilité SQLite
        # Le SQL PostgreSQL original ne fonctionne pas avec SQLite
        migrations.RunSQL(
            "SELECT 1;",  # Commande SQL simple qui fonctionne partout
            reverse_sql="SELECT 1;"
        )
    ]