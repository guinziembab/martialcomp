# Generated manually for recurring events feature
# Migration: 0029_add_recurring_events

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0028_initial'),  # Ajuster selon la dernière migration existante
    ]

    operations = [
        # =========================================================================
        # CHAMPS DE RÉCURRENCE POUR LE MODÈLE EVENT
        # =========================================================================

        migrations.AddField(
            model_name='event',
            name='is_recurring',
            field=models.BooleanField(default=False, verbose_name='Événement récurrent'),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_frequency',
            field=models.CharField(
                blank=True,
                choices=[
                    ('daily', 'Quotidien'),
                    ('weekly', 'Hebdomadaire'),
                    ('biweekly', 'Toutes les 2 semaines'),
                    ('monthly', 'Mensuel'),
                    ('yearly', 'Annuel'),
                ],
                max_length=20,
                null=True,
                verbose_name='Fréquence de récurrence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_interval',
            field=models.PositiveSmallIntegerField(
                default=1,
                verbose_name='Intervalle de récurrence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_days',
            field=models.JSONField(
                blank=True,
                help_text='Jours de la semaine pour la récurrence hebdomadaire (ex: ["MO", "WE", "FR"])',
                null=True,
                verbose_name='Jours de récurrence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_day_of_month',
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name='Jour du mois',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_week_of_month',
            field=models.SmallIntegerField(
                blank=True,
                null=True,
                verbose_name='Semaine du mois',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_end_type',
            field=models.CharField(
                choices=[
                    ('never', 'Jamais'),
                    ('after', 'Après X occurrences'),
                    ('on_date', 'À une date précise'),
                ],
                default='never',
                max_length=20,
                verbose_name='Type de fin de récurrence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_end_after',
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Nombre d'occurrences",
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_end_date',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name='Date de fin de récurrence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='recurrence_rule',
            field=models.TextField(
                blank=True,
                help_text='Règle RRULE iCalendar générée automatiquement',
                verbose_name='Règle de récurrence (RRULE)',
            ),
        ),

        # =========================================================================
        # CHAMPS FORMAT EN LIGNE / VISIOCONFÉRENCE
        # =========================================================================

        migrations.AddField(
            model_name='event',
            name='event_format',
            field=models.CharField(
                choices=[
                    ('in_person', 'En présentiel'),
                    ('online', 'En ligne (visio)'),
                    ('hybrid', 'Hybride (présentiel + visio)'),
                ],
                default='in_person',
                max_length=20,
                verbose_name="Format de l'événement",
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='online_url',
            field=models.URLField(
                blank=True,
                max_length=500,
                verbose_name='URL de visioconférence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='online_platform',
            field=models.CharField(
                blank=True,
                max_length=50,
                verbose_name='Plateforme de visioconférence',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='online_meeting_id',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='ID de réunion',
            ),
        ),

        migrations.AddField(
            model_name='event',
            name='online_password',
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name='Mot de passe de la réunion',
            ),
        ),

        # =========================================================================
        # NOUVEAU MODÈLE: EventOccurrence
        # =========================================================================

        migrations.CreateModel(
            name='EventOccurrence',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('start_datetime', models.DateTimeField(verbose_name='Date/heure de début')),
                ('end_datetime', models.DateTimeField(verbose_name='Date/heure de fin')),
                ('status', models.CharField(
                    choices=[
                        ('planned', 'Planifié'),
                        ('confirmed', 'Confirmé'),
                        ('cancelled', 'Annulé'),
                        ('completed', 'Terminé'),
                        ('postponed', 'Reporté'),
                    ],
                    default='planned',
                    max_length=20,
                    verbose_name='Statut',
                )),
                ('is_exception', models.BooleanField(
                    default=False,
                    help_text='Indique si cette occurrence a été modifiée individuellement',
                    verbose_name='Exception',
                )),
                ('override_location', models.CharField(
                    blank=True,
                    max_length=255,
                    verbose_name='Lieu alternatif',
                )),
                ('override_online_url', models.URLField(
                    blank=True,
                    max_length=500,
                    verbose_name='URL visio alternative',
                )),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('cancellation_reason', models.TextField(blank=True, verbose_name="Raison de l'annulation")),
                ('attendees_count', models.PositiveIntegerField(
                    default=0,
                    verbose_name='Nombre de participants',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='occurrences',
                    to='competitions.event',
                    verbose_name='Événement parent',
                )),
            ],
            options={
                'verbose_name': "Occurrence d'événement",
                'verbose_name_plural': "Occurrences d'événements",
                'ordering': ['start_datetime'],
            },
        ),

        # =========================================================================
        # NOUVEAU MODÈLE: EventOccurrenceAttendance
        # =========================================================================

        migrations.CreateModel(
            name='EventOccurrenceAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('registered', 'Inscrit'),
                        ('present', 'Présent'),
                        ('absent', 'Absent'),
                        ('excused', 'Excusé'),
                        ('late', 'En retard'),
                    ],
                    default='registered',
                    max_length=20,
                    verbose_name='Statut de présence',
                )),
                ('check_in_time', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name="Heure d'arrivée",
                )),
                ('check_in_method', models.CharField(
                    blank=True,
                    choices=[
                        ('manual', 'Manuel'),
                        ('qr_code', 'QR Code'),
                        ('auto', 'Automatique'),
                    ],
                    max_length=20,
                    verbose_name='Méthode de pointage',
                )),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('occurrence', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendances',
                    to='competitions.eventoccurrence',
                    verbose_name='Occurrence',
                )),
                ('participant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='occurrence_attendances',
                    to='competitions.eventparticipant',
                    verbose_name='Participant',
                )),
            ],
            options={
                'verbose_name': 'Présence à une occurrence',
                'verbose_name_plural': 'Présences aux occurrences',
                'unique_together': {('occurrence', 'participant')},
            },
        ),

        # =========================================================================
        # INDEX POUR LES PERFORMANCES
        # =========================================================================

        migrations.AddIndex(
            model_name='eventoccurrence',
            index=models.Index(fields=['start_datetime'], name='event_occ_start_idx'),
        ),

        migrations.AddIndex(
            model_name='eventoccurrence',
            index=models.Index(fields=['status'], name='event_occ_status_idx'),
        ),

        migrations.AddIndex(
            model_name='eventoccurrence',
            index=models.Index(fields=['event', 'start_datetime'], name='event_occ_evt_start_idx'),
        ),
    ]
