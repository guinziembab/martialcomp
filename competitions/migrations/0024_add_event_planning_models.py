# Generated manually for event planning module

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0023_add_offline_profile_support'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPoll',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('status', models.CharField(choices=[('active', 'Actif'), ('closed', 'Clôturé'), ('finalized', 'Finalisé'), ('cancelled', 'Annulé')], default='active', max_length=20, verbose_name='Statut')),
                ('response_type', models.CharField(choices=[('yes_no', 'Oui/Non'), ('yes_maybe_no', 'Oui/Peut-être/Non'), ('availability', 'Disponibilité (matin/après-midi/soir)')], default='yes_maybe_no', max_length=20, verbose_name='Type de réponse')),
                ('allow_comments', models.BooleanField(default=True, verbose_name='Autoriser les commentaires')),
                ('allow_multiple_votes', models.BooleanField(default=False, verbose_name='Autoriser votes multiples')),
                ('show_participants', models.BooleanField(default=True, verbose_name='Afficher les participants')),
                ('show_vote_counts', models.BooleanField(default=True, verbose_name='Afficher les décomptes de votes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expire le')),
                ('finalized_at', models.DateTimeField(blank=True, null=True, verbose_name='Finalisé le')),
                ('settings', models.JSONField(blank=True, default=dict, verbose_name='Paramètres avancés')),
                ('event_type', models.CharField(blank=True, choices=[('competition', 'Compétition'), ('training', 'Entraînement'), ('seminar', 'Séminaire'), ('exam', 'Examen'), ('meeting', 'Réunion'), ('social', 'Social'), ('other', 'Autre')], max_length=20, null=True, verbose_name="Type d'événement")),
                ('share_url_code', models.CharField(blank=True, max_length=20, unique=True, verbose_name='Code URL de partage')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_polls', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('event', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='poll', to='competitions.event', verbose_name='Événement associé')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_polls', to='organizations.organization', verbose_name='Organisation')),
            ],
            options={
                'verbose_name': "Sondage d'événement",
                'verbose_name_plural': "Sondages d'événements",
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PollOption',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(verbose_name='Date')),
                ('start_time', models.TimeField(blank=True, null=True, verbose_name='Heure de début')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='Heure de fin')),
                ('all_day', models.BooleanField(default=False, verbose_name='Toute la journée')),
                ('order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')),
                ('is_selected', models.BooleanField(default=False, verbose_name='Sélectionnée')),
                ('location', models.CharField(blank=True, max_length=200, verbose_name='Lieu')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='options', to='competitions.eventpoll', verbose_name='Sondage')),
            ],
            options={
                'verbose_name': 'Option de sondage',
                'verbose_name_plural': 'Options de sondage',
                'ordering': ['date', 'start_time', 'order'],
                'unique_together': {('poll', 'date', 'start_time')},
            },
        ),
        migrations.CreateModel(
            name='PollResponse',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('response', models.CharField(choices=[('yes', 'Oui'), ('maybe', 'Peut-être'), ('no', 'Non')], max_length=10, verbose_name='Réponse')),
                ('comment', models.TextField(blank=True, verbose_name='Commentaire')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='Anonyme')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='competitions.polloption', verbose_name='Option')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='poll_responses', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Réponse au sondage',
                'verbose_name_plural': 'Réponses aux sondages',
                'ordering': ['-created_at'],
                'unique_together': {('option', 'user')},
            },
        ),
        migrations.CreateModel(
            name='EventReminder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('message', models.TextField(verbose_name='Message')),
                ('reminder_type', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('notification', 'Notification in-app'), ('all', 'Tous')], default='notification', max_length=20, verbose_name='Type de rappel')),
                ('time_before_event', models.DurationField(help_text="Durée avant l'événement pour envoyer le rappel (ex: 1 jour, 2 heures)", verbose_name="Temps avant l'événement")),
                ('send_at', models.DateTimeField(blank=True, help_text='Date et heure exactes pour envoyer le rappel (prioritaire sur "temps avant")', null=True, verbose_name='Envoyer à')),
                ('is_sent', models.BooleanField(default=False, verbose_name='Envoyé')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Envoyé le')),
                ('is_enabled', models.BooleanField(default=True, verbose_name='Activé')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('settings', models.JSONField(blank=True, default=dict, verbose_name='Paramètres avancés')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_reminders', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to='competitions.event', verbose_name='Événement')),
                ('recipients', models.ManyToManyField(blank=True, help_text='Destinataires spécifiques (vide = tous les participants)', related_name='event_reminders', to=settings.AUTH_USER_MODEL, verbose_name='Destinataires')),
            ],
            options={
                'verbose_name': "Rappel d'événement",
                'verbose_name_plural': "Rappels d'événements",
                'ordering': ['event', 'send_at'],
            },
        ),
        migrations.CreateModel(
            name='EventStatistics',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('total_participants', models.PositiveIntegerField(default=0, verbose_name='Nombre total de participants')),
                ('response_rate', models.FloatField(blank=True, null=True, verbose_name='Taux de réponse')),
                ('response_data', models.JSONField(default=dict, verbose_name='Données de réponse')),
                ('participation_data', models.JSONField(blank=True, default=dict, verbose_name='Données de participation')),
                ('first_response_at', models.DateTimeField(blank=True, null=True, verbose_name='Première réponse à')),
                ('last_response_at', models.DateTimeField(blank=True, null=True, verbose_name='Dernière réponse à')),
                ('median_response_time', models.DurationField(blank=True, null=True, verbose_name='Temps de réponse médian')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('event', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='statistics', to='competitions.event', verbose_name='Événement')),
                ('poll', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='statistics', to='competitions.eventpoll', verbose_name='Sondage')),
            ],
            options={
                'verbose_name': "Statistiques d'événement",
                'verbose_name_plural': "Statistiques d'événements",
            },
        ),
    ]