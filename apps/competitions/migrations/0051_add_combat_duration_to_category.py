from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0050_categorysession_placateur_absence'),
    ]

    operations = [
        migrations.AddField(
            model_name='competitioncategory',
            name='combat_duration',
            field=models.PositiveSmallIntegerField(
                default=120,
                help_text='Durée en secondes (ex: 120 pour 2 minutes)',
                verbose_name='Durée du combat (secondes)'
            ),
        ),
        migrations.AddField(
            model_name='competitioncategory',
            name='combat_extra_time',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='Temps supplémentaire en cas d\'égalité (0 = pas de prolongation)',
                verbose_name='Extra-time (secondes)'
            ),
        ),
    ]
