# Generated migration for broadcast models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0032_add_practitioner_to_eventparticipant'),
        ('organizations', '0014_add_organization_news_model'),
        ('grades', '0004_add_grade_alert_log_model'),
    ]

    operations = [
        # BroadcastGroup model
        migrations.CreateModel(
            name='BroadcastGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('name', models.CharField(max_length=100, verbose_name='Nom du groupe')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('icon', models.CharField(blank=True, default='users', max_length=50, verbose_name='Icône')),
                ('color', models.CharField(blank=True, default='#6366F1', max_length=7, verbose_name='Couleur')),
                ('target_type', models.CharField(
                    choices=[('criteria', 'Par critères'), ('manual', 'Sélection manuelle')],
                    default='criteria',
                    max_length=20,
                    verbose_name='Type de ciblage'
                )),
                ('age_category', models.CharField(
                    choices=[
                        ('enfants', 'Enfants (6-12 ans)'),
                        ('juniors', 'Juniors (13-17 ans)'),
                        ('adultes', 'Adultes (18+ ans)'),
                        ('all', 'Tous âges')
                    ],
                    default='all',
                    max_length=20,
                    verbose_name="Catégorie d'âge"
                )),
                ('min_age', models.PositiveSmallIntegerField(
                    blank=True,
                    help_text='Âge minimum personnalisé (remplace la catégorie)',
                    null=True,
                    verbose_name='Âge minimum'
                )),
                ('max_age', models.PositiveSmallIntegerField(
                    blank=True,
                    help_text='Âge maximum personnalisé (remplace la catégorie)',
                    null=True,
                    verbose_name='Âge maximum'
                )),
                ('gender_filter', models.CharField(
                    choices=[('male', 'Hommes'), ('female', 'Femmes'), ('all', 'Tous')],
                    default='all',
                    max_length=10,
                    verbose_name='Filtrer par genre'
                )),
                ('min_grade_level', models.PositiveSmallIntegerField(
                    blank=True,
                    null=True,
                    verbose_name='Niveau de grade minimum'
                )),
                ('max_grade_level', models.PositiveSmallIntegerField(
                    blank=True,
                    null=True,
                    verbose_name='Niveau de grade maximum'
                )),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mis à jour le')),
                ('created_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='created_broadcast_groups',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Créé par'
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='broadcast_groups',
                    to='organizations.organization',
                    verbose_name='Organisation'
                )),
                ('grades', models.ManyToManyField(
                    blank=True,
                    related_name='broadcast_groups',
                    to='grades.grade',
                    verbose_name='Grades spécifiques'
                )),
                ('members', models.ManyToManyField(
                    blank=True,
                    related_name='broadcast_groups',
                    to='competitions.practitioner',
                    verbose_name='Membres manuels'
                )),
            ],
            options={
                'verbose_name': 'Groupe de diffusion',
                'verbose_name_plural': 'Groupes de diffusion',
                'ordering': ['name'],
            },
        ),

        # BroadcastMessage model
        migrations.CreateModel(
            name='BroadcastMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('title', models.CharField(max_length=200, verbose_name='Titre')),
                ('content', models.TextField(verbose_name='Message')),
                ('priority', models.CharField(
                    choices=[
                        ('low', 'Faible'),
                        ('normal', 'Normal'),
                        ('high', 'Important'),
                        ('urgent', 'Urgent')
                    ],
                    default='normal',
                    max_length=20,
                    verbose_name='Priorité'
                )),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Envoyé le')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Expire le')),
                ('recipients_count', models.PositiveIntegerField(default=0, verbose_name='Nombre de destinataires')),
                ('read_count', models.PositiveIntegerField(default=0, verbose_name='Nombre de lectures')),
                ('group', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages',
                    to='competitions.broadcastgroup',
                    verbose_name='Groupe'
                )),
                ('sender', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sent_broadcasts',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Expéditeur'
                )),
            ],
            options={
                'verbose_name': 'Message de diffusion',
                'verbose_name_plural': 'Messages de diffusion',
                'ordering': ['-created_at'],
            },
        ),

        # BroadcastReceipt model
        migrations.CreateModel(
            name='BroadcastReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivered_at', models.DateTimeField(auto_now_add=True, verbose_name='Livré le')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Lu le')),
                ('broadcast', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='receipts',
                    to='competitions.broadcastmessage',
                    verbose_name='Message'
                )),
                ('practitioner', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='broadcast_receipts',
                    to='competitions.practitioner',
                    verbose_name='Pratiquant'
                )),
                ('notification', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='broadcast_receipt',
                    to='competitions.notification',
                    verbose_name='Notification'
                )),
            ],
            options={
                'verbose_name': 'Reçu de diffusion',
                'verbose_name_plural': 'Reçus de diffusion',
                'unique_together': {('broadcast', 'practitioner')},
            },
        ),

        # Indexes
        migrations.AddIndex(
            model_name='broadcastgroup',
            index=models.Index(fields=['organization', 'is_active'], name='competition_organiz_b8f1a3_idx'),
        ),
        migrations.AddIndex(
            model_name='broadcastgroup',
            index=models.Index(fields=['created_by'], name='competition_created_b8f1a4_idx'),
        ),
        migrations.AddIndex(
            model_name='broadcastmessage',
            index=models.Index(fields=['group', '-created_at'], name='competition_group_i_b8f1a5_idx'),
        ),
        migrations.AddIndex(
            model_name='broadcastmessage',
            index=models.Index(fields=['sender', '-created_at'], name='competition_sender__b8f1a6_idx'),
        ),
        migrations.AddIndex(
            model_name='broadcastmessage',
            index=models.Index(fields=['-sent_at'], name='competition_sent_at_b8f1a7_idx'),
        ),
        migrations.AddIndex(
            model_name='broadcastreceipt',
            index=models.Index(fields=['broadcast', 'read_at'], name='competition_broadca_b8f1a8_idx'),
        ),
        migrations.AddIndex(
            model_name='broadcastreceipt',
            index=models.Index(fields=['practitioner', '-delivered_at'], name='competition_practit_b8f1a9_idx'),
        ),
    ]
