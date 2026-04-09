from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competitions', '0037_competition_created_by'),
        ('organizations', '0014_add_organization_news_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='PractitionerTransfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('approved', 'Approuvé'), ('rejected', 'Rejeté'), ('cancelled', 'Annulé')], default='pending', max_length=20, verbose_name='Statut')),
                ('initiated_by', models.CharField(choices=[('manager', 'Responsable de club'), ('practitioner', 'Pratiquant')], default='manager', max_length=20, verbose_name='Initié par')),
                ('reason', models.TextField(blank=True, verbose_name='Motif')),
                ('response_message', models.TextField(blank=True, verbose_name='Message de réponse')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('processed_at', models.DateTimeField(blank=True, null=True, verbose_name='Traité le')),
                ('practitioner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='competitions.practitioner', verbose_name='Pratiquant')),
                ('source_organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='outgoing_transfers', to='organizations.organization', verbose_name="Club d'origine")),
                ('target_organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='incoming_transfers', to='organizations.organization', verbose_name='Club de destination')),
                ('requested_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transfer_requests', to=settings.AUTH_USER_MODEL, verbose_name='Demandé par')),
                ('processed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_transfers', to=settings.AUTH_USER_MODEL, verbose_name='Traité par')),
            ],
            options={
                'verbose_name': 'Transfert de pratiquant',
                'verbose_name_plural': 'Transferts de pratiquants',
                'ordering': ['-created_at'],
            },
        ),
    ]
