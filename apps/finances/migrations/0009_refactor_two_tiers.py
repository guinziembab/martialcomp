"""
Migration: Refactor to 2-tier pricing model (Free / Premium).

Schema changes:
- Subscription.region: make nullable
- PricingRegion: add monthly_price_per_member field

Data changes:
- Create 2 new SubscriptionTier entries (free, premium)
- Deactivate old 3 tiers (dojo_essentials, masters_circle, grand_champion)
- Create 2 new PricingRegion entries (mature, emergent), deactivate old 6
- Migrate OrganizationSubscription: old tiers → new tiers
- Enable all FeatureFlags for all tiers
- Clear VolumeDiscount table
"""
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


def create_new_tiers_and_migrate(apps, schema_editor):
    SubscriptionTier = apps.get_model('finances', 'SubscriptionTier')
    PricingRegion = apps.get_model('finances', 'PricingRegion')
    OrganizationSubscription = apps.get_model('finances', 'OrganizationSubscription')
    FeatureFlag = apps.get_model('finances', 'FeatureFlag')
    VolumeDiscount = apps.get_model('finances', 'VolumeDiscount')

    # ---- 1. Create new SubscriptionTier entries ----
    free_tier, _ = SubscriptionTier.objects.get_or_create(
        name='free',
        defaults={
            'display_name': 'Gratuit',
            'description': 'Toutes les fonctionnalités, max 10 membres',
            'max_members': 10,
            'max_disciplines': 999,
            'max_clubs': 999,
            'max_storage_mb': 500,
            'monthly_price': Decimal('0.00'),
            'yearly_price': Decimal('0.00'),
            'is_active': True,
        }
    )

    premium_tier, _ = SubscriptionTier.objects.get_or_create(
        name='premium',
        defaults={
            'display_name': 'Premium',
            'description': 'Toutes les fonctionnalités, membres illimités',
            'max_members': 99999,
            'max_disciplines': 999,
            'max_clubs': 999,
            'max_storage_mb': 10000,
            'monthly_price': Decimal('0.99'),
            'yearly_price': Decimal('9.99'),
            'is_active': True,
        }
    )

    # ---- 2. Deactivate old tiers ----
    old_tier_names = ['dojo_essentials', 'masters_circle', 'grand_champion']
    SubscriptionTier.objects.filter(name__in=old_tier_names).update(is_active=False)

    # ---- 3. Migrate OrganizationSubscription to new tiers ----
    # dojo_essentials → free
    OrganizationSubscription.objects.filter(
        subscription_tier__name='dojo_essentials'
    ).update(subscription_tier=free_tier)

    # masters_circle, grand_champion → premium
    OrganizationSubscription.objects.filter(
        subscription_tier__name__in=['masters_circle', 'grand_champion']
    ).update(subscription_tier=premium_tier)

    # ---- 4. Create new PricingRegion entries ----
    # Use raw SQL to handle schema differences between environments
    # (some DBs have a 'code' column, others don't)
    from django.db import connection
    with connection.cursor() as cursor:
        # Check if 'code' column exists
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'finances_pricingregion' AND column_name = 'code'"
        )
        has_code_col = cursor.fetchone() is not None

        for name, code, base, monthly in [
            ('mature', 'MATURE', '9.99', '0.99'),
            ('emergent', 'EMERGENT', '4.99', '0.49'),
        ]:
            cursor.execute(
                "SELECT id FROM finances_pricingregion WHERE name = %s", [name]
            )
            if not cursor.fetchone():
                if has_code_col:
                    cursor.execute(
                        "INSERT INTO finances_pricingregion "
                        "(name, code, base_price_per_member, monthly_price_per_member, currency, is_active) "
                        "VALUES (%s, %s, %s, %s, 'EUR', true)",
                        [name, code, base, monthly]
                    )
                else:
                    cursor.execute(
                        "INSERT INTO finances_pricingregion "
                        "(name, base_price_per_member, monthly_price_per_member, currency, is_active) "
                        "VALUES (%s, %s, %s, 'EUR', true)",
                        [name, base, monthly]
                    )

    # Deactivate old regions
    old_regions = [
        'africa', 'southeast_asia', 'south_central_america',
        'eastern_europe', 'western_europe_north_america_oceania', 'middle_east',
    ]
    PricingRegion.objects.filter(name__in=old_regions).update(is_active=False)

    # ---- 5. Enable all FeatureFlags for all tiers ----
    FeatureFlag.objects.update(is_always_enabled=True)
    # Add new tiers to FeatureFlag M2M
    for flag in FeatureFlag.objects.all():
        flag.subscription_tiers.add(free_tier, premium_tier)

    # ---- 6. Clear VolumeDiscount (no longer used) ----
    VolumeDiscount.objects.all().delete()


def reverse_migration(apps, schema_editor):
    """Reverse: reactivate old tiers, deactivate new ones."""
    SubscriptionTier = apps.get_model('finances', 'SubscriptionTier')
    PricingRegion = apps.get_model('finances', 'PricingRegion')

    # Reactivate old tiers
    old_tier_names = ['dojo_essentials', 'masters_circle', 'grand_champion']
    SubscriptionTier.objects.filter(name__in=old_tier_names).update(is_active=True)

    # Deactivate new tiers
    SubscriptionTier.objects.filter(name__in=['free', 'premium']).update(is_active=False)

    # Reactivate old regions
    old_regions = [
        'africa', 'southeast_asia', 'south_central_america',
        'eastern_europe', 'western_europe_north_america_oceania', 'middle_east',
    ]
    PricingRegion.objects.filter(name__in=old_regions).update(is_active=True)
    PricingRegion.objects.filter(name__in=['mature', 'emergent']).update(is_active=False)


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0008_stripe_fields'),
    ]

    operations = [
        # Schema: make Subscription.region nullable
        migrations.AlterField(
            model_name='subscription',
            name='region',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='finances.pricingregion',
            ),
        ),
        # Schema: add monthly_price_per_member to PricingRegion
        migrations.AddField(
            model_name='pricingregion',
            name='monthly_price_per_member',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Prix mensuel par membre',
                max_digits=6,
            ),
        ),
        # Data: create new tiers, migrate subscriptions, etc.
        migrations.RunPython(create_new_tiers_and_migrate, reverse_migration),
    ]
