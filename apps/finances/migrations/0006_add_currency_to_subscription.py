# -*- coding: utf-8 -*-
"""
Migration pour ajouter les champs multi-devise au modèle Subscription.

Phase 2 du support multi-devise MartialComp.

Cette migration crée également les tables manquantes pour le module Subscription
si elles n'existent pas (PricingRegion, VolumeDiscount, Subscription, etc.)

Créé: Janvier 2025
"""

from decimal import Decimal
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


def table_exists(schema_editor, table_name):
    """Vérifie si une table existe dans la base de données."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)",
            [table_name]
        )
        return cursor.fetchone()[0]


def create_missing_tables(apps, schema_editor):
    """Crée les tables manquantes pour le module Subscription."""
    # Liste des tables et leurs définitions
    tables_to_check = [
        'finances_pricingregion',
        'finances_volumediscount',
        'finances_subscriptiontier',
        'finances_subscription',
        'finances_subscriptionpayment',
        'finances_featureflag',
        'finances_organizationsubscription',
        'finances_featureusagelog',
    ]

    created_tables = []
    for table in tables_to_check:
        if not table_exists(schema_editor, table):
            created_tables.append(table)

    if created_tables:
        print(f"\n  [!] Tables manquantes detectees: {', '.join(created_tables)}")
        print("  -> Ces tables seront creees par cette migration")
    else:
        print("\n  [OK] Toutes les tables Subscription existent deja")


def set_default_currency(apps, schema_editor):
    """
    Configure EUR comme devise par défaut pour les souscriptions existantes.
    """
    if not table_exists(schema_editor, 'finances_subscription'):
        print("  [!] Table finances_subscription n'existe pas, skip")
        return

    Subscription = apps.get_model('finances', 'Subscription')
    Currency = apps.get_model('finances', 'Currency')

    try:
        eur = Currency.objects.get(code='EUR')
        count = Subscription.objects.count()
        if count > 0:
            from decimal import Decimal
            Subscription.objects.filter(currency__isnull=True).update(
                currency=eur,
                exchange_rate_used=Decimal('1.0')
            )
            for sub in Subscription.objects.filter(total_amount_eur__isnull=True):
                sub.total_amount_eur = sub.total_amount
                sub.save(update_fields=['total_amount_eur'])
            print(f"  [OK] {count} souscriptions mises a jour avec EUR")
        else:
            print("  [OK] Aucune souscription existante a mettre a jour")
    except Currency.DoesNotExist:
        print("  [!] Currency EUR non trouvee, migration de donnees ignoree")


def reverse_currency(apps, schema_editor):
    """Reverse migration - rien à faire"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0005_add_currency_models'),
        ('organizations', '0011_add_organization_video_links'),
    ]

    operations = [
        # Vérifier les tables manquantes
        migrations.RunPython(create_missing_tables, migrations.RunPython.noop),

        # Créer PricingRegion si elle n'existe pas
        migrations.CreateModel(
            name='PricingRegion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom de la région')),
                ('code', models.CharField(max_length=10, unique=True, verbose_name='Code région')),
                ('base_price_per_member', models.DecimalField(decimal_places=2, max_digits=6, verbose_name='Prix par membre')),
                ('currency', models.CharField(default='EUR', max_length=3, verbose_name='Devise')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
            ],
            options={
                'verbose_name': 'Région tarifaire',
                'verbose_name_plural': 'Régions tarifaires',
            },
        ),

        # Créer VolumeDiscount si elle n'existe pas
        migrations.CreateModel(
            name='VolumeDiscount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_members', models.IntegerField(verbose_name='Nombre minimum de membres')),
                ('max_members', models.IntegerField(blank=True, null=True, verbose_name='Nombre maximum de membres')),
                ('discount_percentage', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Pourcentage de réduction')),
            ],
            options={
                'verbose_name': 'Réduction volume',
                'verbose_name_plural': 'Réductions volume',
                'ordering': ['min_members'],
            },
        ),

        # Créer SubscriptionTier
        migrations.CreateModel(
            name='SubscriptionTier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(choices=[('dojo_essentials', 'Dojo Essentials'), ('masters_circle', "Master's Circle"), ('grand_champion', 'Grand Champion Suite')], max_length=50, unique=True, verbose_name='Nom du package')),
                ('display_name', models.CharField(max_length=100, verbose_name="Nom d'affichage")),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('max_members', models.IntegerField(default=100, verbose_name='Nombre maximum de membres')),
                ('max_disciplines', models.IntegerField(default=2, verbose_name='Nombre maximum de disciplines')),
                ('max_clubs', models.IntegerField(default=1, verbose_name='Nombre maximum de clubs')),
                ('max_storage_mb', models.IntegerField(default=100, verbose_name='Stockage maximum (MB)')),
                ('monthly_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=6, verbose_name='Prix mensuel')),
                ('yearly_price', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=8, verbose_name='Prix annuel')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
            ],
            options={
                'verbose_name': "Niveau d'abonnement",
                'verbose_name_plural': "Niveaux d'abonnement",
                'ordering': ['monthly_price'],
            },
        ),

        # Créer Subscription avec les champs multi-devise intégrés
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('member_count', models.IntegerField(help_text='Nombre de membres facturés', validators=[django.core.validators.MinValueValidator(1)])),
                ('base_price_per_member', models.DecimalField(decimal_places=2, max_digits=6)),
                ('volume_discount_percentage', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('final_price_per_member', models.DecimalField(decimal_places=2, max_digits=6)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('billing_cycle', models.CharField(choices=[('ANNUAL', 'Annuel'), ('MONTHLY', 'Mensuel')], default='ANNUAL', max_length=20)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('EXPIRED', 'Expirée'), ('CANCELLED', 'Annulée'), ('PENDING', 'En attente'), ('TRIAL', 'Essai')], default='PENDING', max_length=20)),
                ('payment_method', models.CharField(choices=[('CARD', 'Carte bancaire'), ('WIRE_TRANSFER', 'Virement'), ('SEPA', 'Prélèvement SEPA'), ('WALLET', 'Portefeuille')], max_length=20)),
                ('is_first_payment', models.BooleanField(default=True, help_text='Premier paiement pour calculer les commissions')),
                ('installment_count', models.IntegerField(default=1, help_text='Nombre de versements')),
                ('installment_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                # Champs multi-devise Phase 2
                ('currency', models.ForeignKey(default='EUR', help_text='Devise utilisée pour cette souscription', on_delete=django.db.models.deletion.PROTECT, to='finances.currency', verbose_name='Devise')),
                ('total_amount_eur', models.DecimalField(blank=True, decimal_places=2, help_text='Montant converti en EUR pour consolidation comptable', max_digits=10, null=True, verbose_name='Montant total (EUR)')),
                ('exchange_rate_used', models.DecimalField(blank=True, decimal_places=8, help_text='Taux de change au moment de la transaction', max_digits=18, null=True, verbose_name='Taux de change utilisé')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='organizations.organization')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finances.pricingregion')),
            ],
            options={
                'verbose_name': 'Souscription',
                'verbose_name_plural': 'Souscriptions',
                'ordering': ['-created_at'],
            },
        ),

        # Créer SubscriptionPayment
        migrations.CreateModel(
            name='SubscriptionPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('installment_number', models.IntegerField(default=1)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('PENDING', 'En attente'), ('COMPLETED', 'Complété'), ('FAILED', 'Échoué'), ('REFUNDED', 'Remboursé')], default='PENDING', max_length=20)),
                ('payment_reference', models.CharField(blank=True, max_length=100)),
                ('payment_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='finances.subscription')),
            ],
            options={
                'verbose_name': 'Paiement souscription',
                'verbose_name_plural': 'Paiements souscription',
                'ordering': ['subscription', 'installment_number'],
            },
        ),

        # Créer FeatureFlag
        migrations.CreateModel(
            name='FeatureFlag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nom de la fonctionnalité')),
                ('display_name', models.CharField(max_length=150, verbose_name="Nom d'affichage")),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('module', models.CharField(choices=[('core', 'Core'), ('practitioner_management', 'Gestion Pratiquants'), ('organization_management', 'Gestion Organisations'), ('disciplines_training', 'Disciplines & Formation'), ('competitions', 'Compétitions'), ('scoring_system', 'Système de Notation'), ('combat_system', 'Système de Combat'), ('financial', 'Financier'), ('ecommerce', 'E-commerce'), ('communications', 'Communications'), ('documents_ged', 'Documents & GED'), ('family_management', 'Gestion Familiale'), ('events_planning', 'Événements & Planning'), ('qr_mobile', 'QR Code & Mobile'), ('analytics_reporting', 'Analytics & Reporting')], max_length=50, verbose_name='Module')),
                ('complexity', models.CharField(choices=[('basic', 'Basique'), ('intermediate', 'Intermédiaire'), ('advanced', 'Avancé'), ('critical', 'Critique')], default='basic', max_length=20, verbose_name='Complexité')),
                ('view_names', models.TextField(blank=True, help_text='Noms des vues séparés par des virgules', verbose_name='Noms des vues')),
                ('url_patterns', models.TextField(blank=True, help_text="Patterns d'URLs séparés par des virgules", verbose_name="Patterns d'URLs")),
                ('model_names', models.TextField(blank=True, help_text='Noms des modèles séparés par des virgules', verbose_name='Noms des modèles')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('is_always_enabled', models.BooleanField(default=False, help_text='Fonctionnalité critique qui ne peut pas être désactivée', verbose_name='Toujours activé')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
                ('subscription_tiers', models.ManyToManyField(help_text="Niveaux d'abonnement qui ont accès à cette fonctionnalité", to='finances.subscriptiontier', verbose_name="Niveaux d'abonnement")),
            ],
            options={
                'verbose_name': 'Feature Flag',
                'verbose_name_plural': 'Feature Flags',
                'ordering': ['module', 'name'],
            },
        ),

        # Créer OrganizationSubscription
        migrations.CreateModel(
            name='OrganizationSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(verbose_name='Date de début')),
                ('end_date', models.DateTimeField(verbose_name='Date de fin')),
                ('trial_end_date', models.DateTimeField(blank=True, null=True, verbose_name="Fin de la période d'essai")),
                ('status', models.CharField(choices=[('active', 'Actif'), ('trial', "Période d'essai"), ('expired', 'Expiré'), ('suspended', 'Suspendu'), ('cancelled', 'Annulé')], default='trial', max_length=20, verbose_name='Statut')),
                ('current_members_count', models.IntegerField(default=0, verbose_name='Nombre de membres actuels')),
                ('current_disciplines_count', models.IntegerField(default=0, verbose_name='Nombre de disciplines actuelles')),
                ('current_clubs_count', models.IntegerField(default=1, verbose_name='Nombre de clubs actuels')),
                ('current_storage_mb', models.IntegerField(default=0, verbose_name='Stockage utilisé (MB)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
                ('organization', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feature_subscription', to='competitions.club')),
                ('subscription_tier', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finances.subscriptiontier', verbose_name="Niveau d'abonnement")),
            ],
            options={
                'verbose_name': 'Abonnement organisation',
                'verbose_name_plural': 'Abonnements organisations',
            },
        ),

        # Créer FeatureUsageLog
        migrations.CreateModel(
            name='FeatureUsageLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('view_name', models.CharField(max_length=100, verbose_name='Nom de la vue')),
                ('url_path', models.CharField(max_length=255, verbose_name="Chemin de l'URL")),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Horodatage')),
                ('session_key', models.CharField(blank=True, max_length=40, null=True, verbose_name='Clé de session')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='Adresse IP')),
                ('feature_flag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finances.featureflag')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='feature_usage_logs', to='competitions.club')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'verbose_name': "Log d'utilisation de fonctionnalité",
                'verbose_name_plural': "Logs d'utilisation de fonctionnalités",
            },
        ),

        # Index pour FeatureUsageLog
        migrations.AddIndex(
            model_name='featureusagelog',
            index=models.Index(fields=['organization', 'timestamp'], name='finances_fe_organiz_4c0f8e_idx'),
        ),
        migrations.AddIndex(
            model_name='featureusagelog',
            index=models.Index(fields=['feature_flag', 'timestamp'], name='finances_fe_feature_a7d1b3_idx'),
        ),
    ]
