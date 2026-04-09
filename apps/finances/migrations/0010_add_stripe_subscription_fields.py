"""
Migration: Add Stripe subscription fields to OrganizationSubscription.

Phase 3: Stripe recurring subscription integration.
- stripe_customer_id: Stripe Customer object ID (cus_...)
- stripe_subscription_id: Stripe Subscription object ID (sub_...)
- stripe_price_id: Stripe Price object ID (price_...)
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0009_refactor_two_tiers'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationsubscription',
            name='stripe_customer_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='cus_...',
                max_length=255,
                null=True,
                verbose_name='Stripe Customer ID',
            ),
        ),
        migrations.AddField(
            model_name='organizationsubscription',
            name='stripe_subscription_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='sub_...',
                max_length=255,
                null=True,
                verbose_name='Stripe Subscription ID',
            ),
        ),
        migrations.AddField(
            model_name='organizationsubscription',
            name='stripe_price_id',
            field=models.CharField(
                blank=True,
                help_text='price_...',
                max_length=255,
                null=True,
                verbose_name='Stripe Price ID',
            ),
        ),
    ]
