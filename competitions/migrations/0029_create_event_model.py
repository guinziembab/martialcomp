# -*- coding: utf-8 -*-
# Generated manually for creating the Event model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0028_add_event_archive_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('description', models.TextField(verbose_name='Description')),
                ('event_type', models.CharField(choices=[('competition', 'Compétition'), ('training', 'Entraînement'), ('seminar', 'Séminaire'), ('exam', 'Examen'), ('meeting', 'Réunion'), ('social', 'Social'), ('other', 'Autre')], max_length=20, verbose_name="Type d'événement")),
                
                # Dates et heures
                ('start_date', models.DateField(verbose_name='Date de début')),
                ('end_date', models.DateField(verbose_name='Date de fin')),
                ('start_time', models.TimeField(blank=True, null=True, verbose_name='Heure de début')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='Heure de fin')),
                ('all_day', models.BooleanField(default=False, verbose_name='Toute la journée')),
                
                # Lieu
                ('location', models.CharField(blank=True, max_length=200, verbose_name='Lieu')),
                ('address', models.CharField(blank=True, max_length=300, verbose_name='Adresse')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='Ville')),
                ('postal_code', models.CharField(blank=True, max_length=20, verbose_name='Code postal')),
                
                # Paramètres
                ('visibility', models.CharField(choices=[('public', 'Public'), ('members', 'Membres uniquement'), ('private', 'Privé')], default='members', max_length=20, verbose_name='Visibilité')),
                ('is_public', models.BooleanField(default=False, verbose_name='Public')),
                ('max_participants', models.PositiveIntegerField(blank=True, null=True, verbose_name='Nombre max de participants')),
                ('registration_required', models.BooleanField(default=False, verbose_name='Inscription requise')),
                ('registration_deadline', models.DateTimeField(blank=True, null=True, verbose_name="Date limite d'inscription")),
                
                # Détails
                ('price', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Prix')),
                ('contact_email', models.EmailField(blank=True, verbose_name='Email de contact')),
                ('contact_phone', models.CharField(blank=True, max_length=20, verbose_name='Téléphone de contact')),
                
                # Attachements et média
                ('image', models.ImageField(blank=True, null=True, upload_to='events/', verbose_name='Image')),
                ('documents', models.JSONField(blank=True, default=list, verbose_name='Documents')),
                
                # Métadonnées
                ('is_cancelled', models.BooleanField(default=False, verbose_name='Annulé')),
                ('cancellation_reason', models.TextField(blank=True, verbose_name="Raison d'annulation")),
                ('is_archived', models.BooleanField(default=False, verbose_name='Archivé')),
                ('archived_at', models.DateTimeField(blank=True, null=True, verbose_name='Archivé le')),
                
                # Personnalisation
                ('color', models.CharField(default='#007bff', max_length=7, verbose_name='Couleur')),
                
                # Relations
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to='organizations.organization', verbose_name='Organisation')),
                ('contact_person', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organized_events', to=settings.AUTH_USER_MODEL, verbose_name='Personne de contact')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_events', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                
                # Horodatage
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
            ],
            options={
                'verbose_name': 'Événement',
                'verbose_name_plural': 'Événements',
                'ordering': ['-start_date', '-start_time'],
            },
        ),
        
        migrations.CreateModel(
            name='EventParticipant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registration_date', models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")),
                ('status', models.CharField(choices=[('registered', 'Inscrit'), ('confirmed', 'Confirmé'), ('cancelled', 'Annulé'), ('no_show', 'Absent')], default='registered', max_length=20, verbose_name='Statut')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('payment_status', models.CharField(choices=[('pending', 'En attente'), ('paid', 'Payé'), ('refunded', 'Remboursé')], default='pending', max_length=20, verbose_name='Statut de paiement')),
                
                # Relations
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='competitions.event', verbose_name='Événement')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_participations', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Participant à un événement',
                'verbose_name_plural': 'Participants aux événements',
                'unique_together': {('event', 'user')},
            },
        ),
    ]