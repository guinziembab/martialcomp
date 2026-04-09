# Generated migration for DisciplineAccessLog
# PHASE 3 SECURITY: Journal des acces par discipline

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0001_initial'),
        ('organizations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DisciplineAccessLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('view', 'Consultation'), ('edit', 'Modification'), ('create', 'Creation'), ('delete', 'Suppression'), ('export', 'Export'), ('api_access', 'Acces API')], max_length=20, verbose_name='Action')),
                ('allowed', models.BooleanField(help_text="Indique si l'acces a ete autorise ou refuse", verbose_name='Autorise')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Horodatage')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('user_agent', models.TextField(blank=True, default='', verbose_name='User Agent')),
                ('resource_type', models.CharField(blank=True, default='', help_text='Ex: Grade, Practitioner, Competition', max_length=100, verbose_name='Type de ressource')),
                ('resource_id', models.PositiveIntegerField(blank=True, null=True, verbose_name='ID de la ressource')),
                ('details', models.JSONField(blank=True, default=dict, help_text='Informations supplementaires en JSON', verbose_name='Details')),
                ('discipline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_logs', to='competitions.discipline', verbose_name='Discipline')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='discipline_access_logs', to='organizations.organization', verbose_name='Organisation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='discipline_access_logs', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Journal acces discipline',
                'verbose_name_plural': 'Journaux acces disciplines',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='disciplineaccesslog',
            index=models.Index(fields=['-timestamp'], name='core_discip_timesta_4a5bc6_idx'),
        ),
        migrations.AddIndex(
            model_name='disciplineaccesslog',
            index=models.Index(fields=['user', '-timestamp'], name='core_discip_user_id_af2ce1_idx'),
        ),
        migrations.AddIndex(
            model_name='disciplineaccesslog',
            index=models.Index(fields=['discipline', '-timestamp'], name='core_discip_discipl_ee9e9c_idx'),
        ),
        migrations.AddIndex(
            model_name='disciplineaccesslog',
            index=models.Index(fields=['allowed', '-timestamp'], name='core_discip_allowed_93fc82_idx'),
        ),
        migrations.AddIndex(
            model_name='disciplineaccesslog',
            index=models.Index(fields=['action', '-timestamp'], name='core_discip_action_ba5d03_idx'),
        ),
    ]
