"""
Migration: Add Stripe-specific fields to PaymentAttempt.

Phase 1: Stripe Checkout Session Integration.
These indexed fields enable fast webhook lookup by session_id or payment_intent_id.
Safe for production: AddField with null=True on PostgreSQL is nearly instant.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0007_add_practitioner_to_transaction'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentattempt',
            name='stripe_session_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Stripe Checkout Session ID (cs_...)',
                max_length=255,
                null=True,
                verbose_name='ID de session Stripe',
            ),
        ),
        migrations.AddField(
            model_name='paymentattempt',
            name='stripe_payment_intent_id',
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text='Stripe PaymentIntent ID (pi_...)',
                max_length=255,
                null=True,
                verbose_name='ID PaymentIntent Stripe',
            ),
        ),
    ]
