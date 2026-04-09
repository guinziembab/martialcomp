"""
Migration pour les features :
- CategorySession (workflow juge principal)
- PlacateurAssignment + CompetitorCallStatus
- Champs is_absent sur TechnicalPerformance
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0049_add_remaining_language_columns'),
    ]

    operations = [
        # ── CategorySession ──
        migrations.CreateModel(
            name='CategorySession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('pending', 'En attente'),
                        ('started', 'En cours'),
                        ('stopped', 'Notation terminée'),
                        ('validating', 'En vérification'),
                        ('validated', 'Validée'),
                        ('needs_revote', '2e tour requis'),
                        ('closed', 'Clôturée'),
                    ],
                    default='pending', max_length=20, verbose_name='Statut'
                )),
                ('round_number', models.PositiveSmallIntegerField(default=1, verbose_name='Numéro du tour')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Démarré le')),
                ('stopped_at', models.DateTimeField(blank=True, null=True, verbose_name='Arrêté le')),
                ('validated_at', models.DateTimeField(blank=True, null=True, verbose_name='Validé le')),
                ('closed_at', models.DateTimeField(blank=True, null=True, verbose_name='Clôturé le')),
                ('validation_result', models.CharField(
                    blank=True, max_length=20,
                    choices=[
                        ('ok', 'Validé — aucun conflit'),
                        ('tie', 'Égalité détectée — 2e tour requis'),
                        ('conflict', 'Conflit de position détecté'),
                    ],
                    verbose_name='Résultat'
                )),
                ('validation_notes', models.TextField(blank=True, verbose_name='Notes de validation')),
                ('category', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sessions',
                    to='competitions.competitioncategory'
                )),
                ('competition', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='category_sessions',
                    to='competitions.competition'
                )),
                ('head_judge', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='head_judge_sessions',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Juge principal'
                )),
                ('validated_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='validated_sessions',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Validé par'
                )),
            ],
            options={
                'verbose_name': 'Session de catégorie',
                'verbose_name_plural': 'Sessions de catégorie',
                'ordering': ['competition', 'category', 'round_number'],
                'unique_together': {('category', 'round_number')},
            },
        ),

        # ── PlacateurAccess (accès bénévole sans compte) ──
        migrations.CreateModel(
            name='PlacateurAccess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=100, verbose_name='Nom du placateur')),
                ('pin_code', models.CharField(max_length=6, verbose_name='Code PIN')),
                ('access_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('competition', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='placateur_accesses',
                    to='competitions.competition'
                )),
                ('categories', models.ManyToManyField(
                    blank=True,
                    related_name='placateur_accesses',
                    to='competitions.competitioncategory',
                    verbose_name='Catégories assignées'
                )),
            ],
            options={
                'verbose_name': 'Accès placateur',
                'verbose_name_plural': 'Accès placateurs',
                'ordering': ['competition', 'nom'],
            },
        ),

        # ── CompetitorCallStatus ──
        migrations.CreateModel(
            name='CompetitorCallStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[
                        ('waiting', 'En attente'),
                        ('called', 'Appelé'),
                        ('present', 'Présent'),
                        ('absent', 'Absent'),
                        ('passed', 'Passé'),
                    ],
                    default='waiting', max_length=20, verbose_name='Statut'
                )),
                ('call_order', models.PositiveSmallIntegerField(default=0, verbose_name='Ordre de passage')),
                ('called_at', models.DateTimeField(blank=True, null=True, verbose_name='Appelé à')),
                ('status_changed_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
                ('notes', models.CharField(blank=True, max_length=200, verbose_name='Notes')),
                ('performance', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='call_status',
                    to='competitions.technicalperformance'
                )),
                ('placateur_access', models.ForeignKey(
                    on_delete=django.db.models.deletion.SET_NULL,
                    null=True, blank=True,
                    related_name='call_statuses',
                    to='competitions.placateuraccess'
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='call_statuses',
                    to='competitions.categorysession'
                )),
            ],
            options={
                'verbose_name': "Statut d'appel compétiteur",
                'verbose_name_plural': "Statuts d'appel compétiteurs",
                'ordering': ['call_order'],
                'unique_together': {('session', 'performance')},
            },
        ),

        # ── Champs absence sur TechnicalPerformance ──
        migrations.AddField(
            model_name='technicalperformance',
            name='is_absent',
            field=models.BooleanField(default=False, verbose_name='Absent'),
        ),
        migrations.AddField(
            model_name='technicalperformance',
            name='absence_noted_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='noted_absences',
                to=settings.AUTH_USER_MODEL,
                verbose_name="Absence notée par"
            ),
        ),
        migrations.AddField(
            model_name='technicalperformance',
            name='absence_noted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Absence notée le'),
        ),
    ]
