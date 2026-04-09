# Generated migration to add metadata field to Federation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0026_add_podium_entry_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='federation',
            name='metadata',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text='Stocke le contenu personnalisé du site public',
                verbose_name='Métadonnées du site'
            ),
        ),
    ]
