from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('multitenant', '0004_remove_tenant_logo_remove_tenant_primary_color_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayPerUseFeature',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('description', models.TextField(verbose_name='Description')),
                ('price_per_unit', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix par unité')),
                ('unit_label', models.CharField(max_length=50, verbose_name="Libellé de l'unité")),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
            ],
            options={
                'verbose_name': "Fonctionnalité à l'usage",
                'verbose_name_plural': "Fonctionnalités à l'usage",
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='PromotionCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True, verbose_name='Code')),
                ('description', models.TextField(verbose_name='Description')),
                ('discount_type', models.CharField(choices=[('percentage', 'Pourcentage de réduction'), ('fixed', 'Montant fixe de réduction'), ('free_months', 'Mois gratuits')], max_length=20, verbose_name='Type de réduction')),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Valeur de la réduction')),
                ('valid_from', models.DateTimeField(verbose_name='Valide à partir de')),
                ('valid_until', models.DateTimeField(verbose_name="Valide jusqu'à")),
                ('max_uses', models.PositiveIntegerField(blank=True, null=True, verbose_name="Nombre max d'utilisations")),
                ('current_uses', models.PositiveIntegerField(default=0, verbose_name='Utilisations actuelles')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
            ],
            options={
                'verbose_name': 'Code promotionnel',
                'verbose_name_plural': 'Codes promotionnels',
                'ordering': ['-valid_until'],
            },
        ),
        migrations.CreateModel(
            name='SubscriptionTier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('description', models.TextField(verbose_name='Description')),
                ('price_monthly', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix mensuel')),
                ('price_annually', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix annuel')),
                ('max_users', models.PositiveIntegerField(verbose_name="Nombre max d'utilisateurs")),
                ('max_competitions', models.PositiveIntegerField(verbose_name='Nombre max de compétitions')),
                ('max_storage_gb', models.PositiveIntegerField(verbose_name='Stockage max (GB)')),
                ('features', models.JSONField(default=dict, verbose_name='Fonctionnalités')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
            ],
            options={
                'verbose_name': "Niveau d'abonnement",
                'verbose_name_plural': "Niveaux d'abonnement",
                'ordering': ['price_monthly'],
            },
        ),
        # Suppression du modèle TenantSubscription car il existe déjà depuis la migration 0003
        migrations.CreateModel(
            name='FeatureUsage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Quantité')),
                ('usage_date', models.DateTimeField(verbose_name="Date d'utilisation")),
                ('billed', models.BooleanField(default=False, verbose_name='Facturé')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Date de modification')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='usages', to='multitenant.payperusefeature')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_usages', to='multitenant.tenant')),
            ],
            options={
                'verbose_name': 'Utilisation de fonctionnalité',
                'verbose_name_plural': 'Utilisations de fonctionnalités',
                'ordering': ['-usage_date'],
            },
        ),
        # Ajouter une relation vers le modèle TenantSubscription existant dans SubscriptionTier
        migrations.AddField(
            model_name='subscriptiontier',
            name='subscriptions',
            field=models.ManyToManyField(
                related_name='subscription_tiers',
                to='multitenant.tenantsubscription',
                verbose_name='Abonnements associés'
            ),
        ),
    ]