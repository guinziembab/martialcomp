# Generated migration for adding practitioner field to EventParticipant

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0031_add_streaming_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventparticipant',
            name='practitioner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='event_participations',
                to='competitions.practitioner',
                verbose_name='Pratiquant'
            ),
        ),
        migrations.AddField(
            model_name='eventparticipant',
            name='role',
            field=models.CharField(
                blank=True,
                default='participant',
                max_length=30,
                verbose_name='Rôle'
            ),
        ),
    ]
