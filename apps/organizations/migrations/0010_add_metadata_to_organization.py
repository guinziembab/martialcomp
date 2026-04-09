# Generated migration to add metadata field to Organization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0009_migrate_existing_affiliations'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='metadata',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Stocke le contenu personnalisé du site public',
                verbose_name='Métadonnées du site'
            ),
        ),
    ]
