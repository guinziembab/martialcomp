# Generated migration for tenant payment models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('multitenant', '0002_add_customization_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TenantPayment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Montant')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('description', models.CharField(help_text='Description du paiement', max_length=255, verbose_name='Description')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('completed', 'Complété'), ('failed', 'Échoué'), ('refunded', 'Remboursé'), ('cancelled', 'Annulé')], default='pending', max_length=20, verbose_name='Statut')),
                ('payment_method', models.CharField(choices=[('card', 'Carte bancaire'), ('bank_transfer', 'Virement bancaire'), ('paypal', 'PayPal'), ('mobile_money', 'Mobile Money'), ('other', 'Autre')], max_length=20, verbose_name='Méthode de paiement')),
                ('provider', models.CharField(help_text='Ex: stripe, paystack, etc.', max_length=50, verbose_name='Fournisseur de paiement')),
                ('provider_payment_id', models.CharField(help_text='ID du paiement chez le fournisseur', max_length=255, unique=True, verbose_name='ID de paiement du fournisseur')),
                ('provider_metadata', models.JSONField(blank=True, default=dict, verbose_name='Métadonnées du fournisseur')),
                ('subscription_period_start', models.DateTimeField(blank=True, null=True, verbose_name='Début de la période')),
                ('subscription_period_end', models.DateTimeField(blank=True, null=True, verbose_name='Fin de la période')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('invoice_id', models.CharField(blank=True, help_text='Référence de la facture associée', max_length=100, verbose_name='Numéro de facture')),
                ('payment_date', models.DateTimeField(blank=True, null=True, verbose_name='Date du paiement')),
                ('failure_reason', models.TextField(blank=True, help_text="Détails en cas d'échec du paiement", verbose_name="Raison de l'échec")),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_payments', to=settings.AUTH_USER_MODEL, verbose_name='Créé par')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='multitenant.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Paiement tenant',
                'verbose_name_plural': 'Paiements tenant',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['tenant', 'status'], name='multitenant_paymen_tenant__d1db2a_idx'),
                    models.Index(fields=['provider_payment_id'], name='multitenant_paymen_provide_1e7856_idx'),
                    models.Index(fields=['created_at'], name='multitenant_paymen_created_0e9e65_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='TenantSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('plan', models.CharField(choices=[('essentials', 'Dojo Essentials'), ('masters', "Master's Circle"), ('champion', 'Grand Champion Suite'), ('trial', 'Essai Gratuit')], max_length=50, verbose_name="Plan d'abonnement")),
                ('status', models.CharField(choices=[('active', 'Actif'), ('cancelled', 'Annulé'), ('expired', 'Expiré'), ('suspended', 'Suspendu')], default='active', max_length=20, verbose_name='Statut')),
                ('start_date', models.DateTimeField(verbose_name='Date de début')),
                ('end_date', models.DateTimeField(verbose_name='Date de fin')),
                ('cancelled_at', models.DateTimeField(blank=True, null=True, verbose_name="Date d'annulation")),
                ('next_billing_date', models.DateTimeField(blank=True, null=True, verbose_name='Prochaine date de facturation')),
                ('subscription_id', models.CharField(help_text="ID de l'abonnement chez le fournisseur", max_length=255, unique=True, verbose_name="ID d'abonnement")),
                ('payment_provider', models.CharField(max_length=50, verbose_name='Fournisseur de paiement')),
                ('provider_metadata', models.JSONField(blank=True, default=dict, verbose_name='Métadonnées du fournisseur')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('tenant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to='multitenant.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Abonnement tenant',
                'verbose_name_plural': 'Abonnements tenant',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('type', models.CharField(choices=[('card', 'Carte bancaire'), ('bank_account', 'Compte bancaire'), ('paypal', 'PayPal'), ('mobile_money', 'Mobile Money')], max_length=20, verbose_name='Type')),
                ('is_default', models.BooleanField(default=False, verbose_name='Méthode par défaut')),
                ('display_name', models.CharField(help_text='Ex: Visa se terminant par 4242', max_length=100, verbose_name="Nom d'affichage")),
                ('provider_method_id', models.CharField(max_length=255, unique=True, verbose_name='ID de la méthode chez le fournisseur')),
                ('provider', models.CharField(max_length=50, verbose_name='Fournisseur')),
                ('provider_metadata', models.JSONField(blank=True, default=dict, verbose_name='Métadonnées du fournisseur')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_methods', to='multitenant.tenant', verbose_name='Tenant')),
            ],
            options={
                'verbose_name': 'Méthode de paiement',
                'verbose_name_plural': 'Méthodes de paiement',
                'ordering': ['-is_default', '-created_at'],
                'unique_together': {('tenant', 'is_default')},
            },
        ),
    ]