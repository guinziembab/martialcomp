# Generated migration for is_completed field on CompetitionCategory

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0022_add_aire_combat_kiosque'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitioncategory',
            name='is_completed',
            field=models.BooleanField(
                default=False,
                help_text='Indique si tous les passages de cette catégorie sont terminés',
                verbose_name='Catégorie terminée'
            ),
        ),
    ]
