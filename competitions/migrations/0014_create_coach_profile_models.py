# Generated migration for coach profile models
# Run this with: python manage.py makemigrations competitions

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0013_alter_club_country_alter_club_tenant'),
        ('grades', '0001_initial'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        # Add multi-discipline support to Practitioner
        migrations.AddField(
            model_name='practitioner',
            name='primary_discipline',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='primary_practitioners',
                to='competitions.discipline',
                verbose_name='Discipline principale'
            ),
        ),
        migrations.AddField(
            model_name='practitioner',
            name='secondary_disciplines',
            field=models.ManyToManyField(
                blank=True,
                related_name='secondary_practitioners',
                to='competitions.discipline',
                verbose_name='Disciplines secondaires'
            ),
        ),
        migrations.AddField(
            model_name='practitioner',
            name='is_coach',
            field=models.BooleanField(
                default=False,
                help_text='Indique si le pratiquant est également coach',
                verbose_name='Est coach'
            ),
        ),
        migrations.AddField(
            model_name='practitioner',
            name='coaching_start_date',
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="Date de début d'enseignement"
            ),
        ),
        
        # Create CoachProfile model
        migrations.CreateModel(
            name='CoachProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_type', models.CharField(
                    choices=[
                        ('traditional', 'Traditionaliste Éclectique'),
                        ('innovative', 'Innovateur Synthétique'),
                        ('researcher', 'Chercheur Perpétuel'),
                        ('pragmatic', 'Expert Pragmatique')
                    ],
                    default='traditional',
                    help_text='Approche pédagogique dominante du coach',
                    max_length=20,
                    verbose_name='Type de profil'
                )),
                ('years_teaching', models.PositiveIntegerField(default=0, verbose_name="Années d'enseignement")),
                ('teaching_philosophy', models.TextField(blank=True, help_text='Description de votre approche pédagogique', verbose_name="Philosophie d'enseignement")),
                ('visibility_settings', models.JSONField(default=dict, help_text='Configuration de ce qui est visible publiquement', verbose_name='Paramètres de visibilité')),
                ('available_for_seminars', models.BooleanField(default=True, verbose_name='Disponible pour séminaires')),
                ('available_for_private_lessons', models.BooleanField(default=True, verbose_name='Disponible pour cours privés')),
                ('available_for_online_coaching', models.BooleanField(default=False, verbose_name='Disponible pour coaching en ligne')),
                ('hourly_rate_range', models.CharField(blank=True, help_text='Ex: 50-80€', max_length=50, verbose_name='Fourchette tarifaire horaire')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('practitioner', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='coach_profile', to='competitions.practitioner', verbose_name='Pratiquant')),
                ('primary_teaching_place', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='primary_coaches', to='competitions.club', verbose_name="Lieu d'enseignement principal")),
            ],
            options={
                'verbose_name': 'Profil coach',
                'verbose_name_plural': 'Profils coaches',
            },
        ),
        
        # Create DisciplineExpertise model
        migrations.CreateModel(
            name='DisciplineExpertise',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(
                    choices=[
                        ('beginner', 'Débutant'),
                        ('intermediate', 'Intermédiaire'),
                        ('advanced', 'Avancé'),
                        ('expert', 'Expert'),
                        ('master', 'Maître')
                    ],
                    default='advanced',
                    max_length=20,
                    verbose_name="Niveau d'expertise"
                )),
                ('years_experience', models.PositiveIntegerField(default=0, verbose_name="Années d'expérience")),
                ('years_teaching', models.PositiveIntegerField(default=0, verbose_name="Années d'enseignement")),
                ('is_primary', models.BooleanField(default=False, verbose_name='Discipline principale')),
                ('current_grade', models.CharField(blank=True, max_length=100, verbose_name='Grade actuel')),
                ('teaching_certification', models.CharField(blank=True, max_length=200, verbose_name="Certification d'enseignement")),
                ('public_description', models.TextField(blank=True, help_text='Décrivez votre expertise dans cette discipline', verbose_name='Description publique')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('coach_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discipline_expertises', to='competitions.coachprofile', verbose_name='Profil coach')),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competitions.discipline', verbose_name='Discipline')),
                ('federation', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.federation', verbose_name='Fédération affiliée')),
            ],
            options={
                'verbose_name': 'Expertise disciplinaire',
                'verbose_name_plural': 'Expertises disciplinaires',
                'unique_together': {('coach_profile', 'discipline')},
            },
        ),
        
        # Create TeachingSchedule model
        migrations.CreateModel(
            name='TeachingSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_of_week', models.IntegerField(
                    choices=[
                        (0, 'Lundi'),
                        (1, 'Mardi'),
                        (2, 'Mercredi'),
                        (3, 'Jeudi'),
                        (4, 'Vendredi'),
                        (5, 'Samedi'),
                        (6, 'Dimanche')
                    ],
                    verbose_name='Jour de la semaine'
                )),
                ('start_time', models.TimeField(verbose_name='Heure de début')),
                ('end_time', models.TimeField(verbose_name='Heure de fin')),
                ('level', models.CharField(blank=True, max_length=50, verbose_name='Niveau du cours')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('club', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competitions.club', verbose_name='Club')),
                ('coach_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teaching_schedules', to='competitions.coachprofile', verbose_name='Profil coach')),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competitions.discipline', verbose_name='Discipline')),
            ],
            options={
                'verbose_name': "Planning d'enseignement",
                'verbose_name_plural': "Plannings d'enseignement",
                'ordering': ['day_of_week', 'start_time'],
            },
        ),
        
        # Create CoachAchievement model
        migrations.CreateModel(
            name='CoachAchievement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('achievement_type', models.CharField(
                    choices=[
                        ('certification', 'Certification'),
                        ('competition', 'Compétition'),
                        ('teaching', 'Enseignement'),
                        ('publication', 'Publication'),
                        ('seminar', 'Séminaire'),
                        ('other', 'Autre')
                    ],
                    max_length=20,
                    verbose_name='Type de réalisation'
                )),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('date', models.DateField(blank=True, null=True, verbose_name='Date')),
                ('issuing_organization', models.CharField(blank=True, max_length=200, verbose_name='Organisation émettrice')),
                ('document', models.FileField(blank=True, null=True, upload_to='coach_achievements/', verbose_name='Document')),
                ('is_public', models.BooleanField(default=True, verbose_name='Visible publiquement')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('coach_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='achievements', to='competitions.coachprofile', verbose_name='Profil coach')),
                ('discipline', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='competitions.discipline', verbose_name='Discipline concernée')),
            ],
            options={
                'verbose_name': 'Réalisation',
                'verbose_name_plural': 'Réalisations',
                'ordering': ['-date'],
            },
        ),
        
        # Update UserProfile ROLE_CHOICES if needed
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(
                choices=[
                    ('spectator', 'Spectateur'),
                    ('participant', 'Participant'),
                    ('judge', 'Juge/Arbitre'),
                    ('coach', 'Coach / Enseignant'),
                    ('club_manager', 'Responsable de club'),
                    ('federation_admin', 'Administrateur de fédération'),
                ],
                default='spectator',
                max_length=20,
                verbose_name='Rôle'
            ),
        ),
    ]