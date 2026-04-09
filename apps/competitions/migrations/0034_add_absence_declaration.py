# -*- coding: utf-8 -*-
# Generated migration for AbsenceDeclaration model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0033_broadcast_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='AbsenceDeclaration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('declaration_type', models.CharField(
                    choices=[
                        ('absence', 'Absence'),
                        ('late', 'Retard'),
                        ('early_leave', 'Départ anticipé'),
                    ],
                    default='absence',
                    max_length=20,
                    verbose_name='Type de déclaration'
                )),
                ('date', models.DateField(verbose_name='Date')),
                ('date_end', models.DateField(blank=True, null=True, verbose_name='Date de fin')),
                ('reason', models.TextField(blank=True, verbose_name='Commentaire')),
                ('reason_category', models.CharField(
                    blank=True,
                    choices=[
                        ('health', 'Santé/Maladie'),
                        ('school', 'École/Travail'),
                        ('family', 'Famille'),
                        ('vacation', 'Vacances'),
                        ('other', 'Autre'),
                    ],
                    max_length=20,
                    null=True,
                    verbose_name='Catégorie de raison'
                )),
                ('declared_at', models.DateTimeField(auto_now_add=True, verbose_name='Déclaré le')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'En attente'),
                        ('acknowledged', 'Pris en compte'),
                        ('rejected', 'Refusé'),
                    ],
                    default='pending',
                    max_length=20,
                    verbose_name='Statut'
                )),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True, verbose_name='Validé le')),
                ('instructor_note', models.TextField(blank=True, verbose_name="Note de l'instructeur")),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('acknowledged_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='acknowledged_absences',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Validé par'
                )),
                ('declared_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='declared_absences',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Déclaré par'
                )),
                ('practitioner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='absence_declarations',
                    to='competitions.practitioner',
                    verbose_name='Pratiquant'
                )),
                ('training_slot', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='absence_declarations',
                    to='competitions.trainingslot',
                    verbose_name="Créneau d'entraînement"
                )),
            ],
            options={
                'verbose_name': "Déclaration d'absence",
                'verbose_name_plural': "Déclarations d'absence",
                'ordering': ['-date', '-declared_at'],
            },
        ),
        migrations.AddIndex(
            model_name='absencedeclaration',
            index=models.Index(fields=['practitioner', 'date'], name='comp_absence_pract_date_idx'),
        ),
        migrations.AddIndex(
            model_name='absencedeclaration',
            index=models.Index(fields=['status', 'date'], name='comp_absence_status_date_idx'),
        ),
    ]
