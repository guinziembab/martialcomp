# Generated manually to add missing fields to EventOccurrence
# Migration: 0030_add_eventoccurrence_missing_fields

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0029_add_recurring_events'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # =======================================================================
        # CHAMPS MANQUANTS POUR EventOccurrence
        # =======================================================================

        migrations.AddField(
            model_name='eventoccurrence',
            name='override_max_participants',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name='Max participants (remplacement)',
            ),
        ),

        migrations.AddField(
            model_name='eventoccurrence',
            name='cancelled_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name='Annulé le',
            ),
        ),

        migrations.AddField(
            model_name='eventoccurrence',
            name='cancelled_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='cancelled_occurrences',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Annulé par',
            ),
        ),

        # =======================================================================
        # CHAMPS MANQUANTS POUR EventOccurrenceAttendance
        # =======================================================================

        migrations.AddField(
            model_name='eventoccurrenceattendance',
            name='checked_in_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='checked_in_attendances',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Pointé par',
            ),
        ),

        migrations.AddField(
            model_name='eventoccurrenceattendance',
            name='excuse_reason',
            field=models.TextField(
                blank=True,
                verbose_name="Raison d'excuse",
            ),
        ),
    ]
