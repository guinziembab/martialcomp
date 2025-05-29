from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('finances', '0002_membershipfee'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('type', models.CharField(choices=[('cash', 'Espèces'), ('card', 'Carte bancaire'), ('transfer', 'Virement bancaire'), ('check', 'Chèque'), ('direct_debit', 'Prélèvement automatique'), ('paypal', 'PayPal'), ('stripe', 'Stripe'), ('other', 'Autre')], max_length=20, verbose_name='Type')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('fee_fixed', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Frais fixe')),
                ('fee_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Frais pourcentage (%)')),
                ('api_key', models.CharField(blank=True, max_length=255, verbose_name='Clé API (chiffrée)')),
                ('api_secret', models.CharField(blank=True, max_length=255, verbose_name='Secret API (chiffré)')),
                ('config', models.JSONField(blank=True, default=dict, verbose_name='Configuration')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('organization_id', models.CharField(blank=True, max_length=50, null=True, verbose_name="ID de l'organisation")),
                ('organization_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype', verbose_name="Type d'organisation")),
            ],
            options={
                'verbose_name': 'Méthode de paiement',
                'verbose_name_plural': 'Méthodes de paiement',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PaymentAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Montant')),
                ('fee_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Montant des frais')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('initiated_at', models.DateTimeField(auto_now_add=True, verbose_name="Date d'initiation")),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de mise à jour')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Date de complétion')),
                ('status', models.CharField(choices=[('initiated', 'Initiée'), ('processing', 'En cours'), ('succeeded', 'Réussie'), ('failed', 'Échouée'), ('cancelled', 'Annulée'), ('refunded', 'Remboursée')], default='initiated', max_length=20, verbose_name='Statut')),
                ('error_code', models.CharField(blank=True, max_length=50, verbose_name="Code d'erreur")),
                ('error_message', models.TextField(blank=True, verbose_name="Message d'erreur")),
                ('provider_reference', models.CharField(blank=True, max_length=255, verbose_name='Référence externe')),
                ('provider_response', models.JSONField(blank=True, default=dict, verbose_name='Réponse du fournisseur')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('user_agent', models.TextField(blank=True, verbose_name='User Agent')),
                ('payment_method', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finances.paymentmethod', verbose_name='Méthode de paiement')),
            ],
            options={
                'verbose_name': 'Tentative de paiement',
                'verbose_name_plural': 'Tentatives de paiement',
                'ordering': ['-initiated_at'],
            },
        ),
    ]