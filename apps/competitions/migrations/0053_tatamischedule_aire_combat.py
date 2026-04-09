from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0052_airecombat_couleur_interieur'),
    ]

    operations = [
        migrations.AddField(
            model_name='tatamischedule',
            name='aire_combat',
            field=models.OneToOneField(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='tatami_schedule',
                to='competitions.airecombat',
                verbose_name='Aire de combat'
            ),
        ),
    ]
