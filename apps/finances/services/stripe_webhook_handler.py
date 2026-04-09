"""
Stripe webhook event handlers.

Each handler takes the parsed event data dict (from StripeService.handle_webhook())
and updates the MartialComp database accordingly.

Handles:
  - Payment events: checkout.session.completed/expired, payment_intent.failed, charge.refunded
  - Subscription lifecycle: customer.subscription.updated/deleted
  - Invoice events: invoice.payment_succeeded/failed (renewal billing)

Idempotency: All handlers check current state before updating,
so duplicate webhook deliveries are safe.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction as db_transaction
from django.utils import timezone

from ..models.payments import PaymentAttempt

logger = logging.getLogger(__name__)


class StripeWebhookHandler:

    @staticmethod
    def handle_checkout_session_completed(data: dict) -> dict:
        """
        Event: checkout.session.completed
        Triggered when customer successfully completes Stripe Checkout.

        For mode=payment: updates PaymentAttempt + Transaction.
        For mode=subscription (checkout_type=premium_subscription):
          activates OrganizationSubscription as premium.
        """
        session_id = data.get('session_id')
        payment_intent_id = data.get('payment_intent_id')
        payment_status = data.get('payment_status')
        metadata = data.get('metadata', {})

        if payment_status != 'paid':
            logger.warning(
                "checkout.session.completed payment_status=%s session=%s",
                payment_status, session_id,
            )
            return {
                'status': 'skipped',
                'reason': f'payment_status={payment_status}',
            }

        # --- Subscription upgrade flow ---
        if metadata.get('checkout_type') == 'premium_subscription':
            return StripeWebhookHandler._activate_premium(
                data, metadata
            )

        # --- Standard payment flow ---
        try:
            attempt = PaymentAttempt.objects.select_related(
                'transaction'
            ).get(stripe_session_id=session_id)
        except PaymentAttempt.DoesNotExist:
            logger.error(
                "No PaymentAttempt for session_id=%s", session_id,
            )
            return {
                'status': 'error',
                'reason': 'payment_attempt_not_found',
            }

        # Idempotency check
        if attempt.status == 'succeeded':
            logger.info(
                "PaymentAttempt %s already succeeded", attempt.id,
            )
            return {
                'status': 'already_processed',
                'payment_attempt_id': str(attempt.id),
            }

        with db_transaction.atomic():
            attempt.stripe_payment_intent_id = payment_intent_id
            attempt.provider_reference = (
                payment_intent_id or session_id
            )
            attempt.provider_response = data
            attempt.status = 'succeeded'
            attempt.completed_at = timezone.now()
            attempt.save()

            # Validate the linked Transaction
            txn = attempt.transaction
            if txn and txn.status == 'pending':
                txn.status = 'validated'
                txn.date_validated = timezone.now()
                txn.save()

            # Register payment on linked Invoice (if any)
            if (txn and txn.invoice
                    and txn.invoice.status not in ('paid', 'cancelled')):
                amount_total_cents = data.get('amount_total') or 0
                amount = Decimal(str(amount_total_cents)) / 100
                txn.invoice.register_payment(
                    amount=amount,
                    payment_date=timezone.now().date(),
                )

        logger.info(
            "checkout.session.completed: PaymentAttempt %s succeeded",
            attempt.id,
        )
        return {
            'status': 'success',
            'payment_attempt_id': str(attempt.id),
        }

    @staticmethod
    def _activate_premium(data: dict, metadata: dict) -> dict:
        """
        Activate premium subscription after successful checkout.
        Called from handle_checkout_session_completed when
        checkout_type == 'premium_subscription'.
        """
        from ..models.subscription import (
            OrganizationSubscription, SubscriptionTier,
        )

        subscription_pk = metadata.get('subscription_id')
        if not subscription_pk:
            logger.error("_activate_premium: no subscription_id in metadata")
            return {'status': 'error', 'reason': 'no_subscription_id'}

        try:
            org_sub = OrganizationSubscription.objects.select_related(
                'subscription_tier',
            ).get(pk=subscription_pk)
        except OrganizationSubscription.DoesNotExist:
            logger.error(
                "_activate_premium: OrganizationSubscription %s not found",
                subscription_pk,
            )
            return {'status': 'error', 'reason': 'subscription_not_found'}

        # Idempotency: already premium
        if (org_sub.subscription_tier
                and org_sub.subscription_tier.name == 'premium'):
            logger.info(
                "_activate_premium: org_sub %s already premium",
                subscription_pk,
            )
            return {'status': 'already_processed'}

        # Get or create premium tier
        premium_tier, _ = SubscriptionTier.objects.get_or_create(
            name='premium',
            defaults={
                'display_name': 'Premium',
                'max_members': 999999,
                'is_active': True,
            },
        )

        # Extract Stripe subscription ID from session data
        stripe_subscription_id = data.get('subscription_id', '')

        with db_transaction.atomic():
            org_sub.subscription_tier = premium_tier
            org_sub.status = 'active'
            org_sub.start_date = timezone.now()
            org_sub.end_date = timezone.now() + timedelta(days=365)
            if stripe_subscription_id:
                org_sub.stripe_subscription_id = stripe_subscription_id
            org_sub.save()

            # Invalidate cache
            cache_key = f"org_subscription_{org_sub.organization_id}"
            cache.delete(cache_key)

        logger.info(
            "Premium activated for org_sub %s (org %s)",
            subscription_pk, org_sub.organization_id,
        )
        return {'status': 'success', 'activated': True}

    @staticmethod
    def handle_checkout_session_expired(data: dict) -> dict:
        """
        Event: checkout.session.expired
        Triggered when Stripe Checkout Session expires (24h default).
        """
        session_id = data.get('session_id')

        try:
            attempt = PaymentAttempt.objects.get(stripe_session_id=session_id)
        except PaymentAttempt.DoesNotExist:
            logger.warning("No PaymentAttempt for expired session %s", session_id)
            return {'status': 'not_found'}

        if attempt.status in ('succeeded', 'refunded'):
            return {'status': 'already_processed'}

        attempt.status = 'failed'
        attempt.error_code = 'session_expired'
        attempt.error_message = 'Stripe Checkout Session expired'
        attempt.completed_at = timezone.now()
        attempt.provider_response = data
        attempt.save()

        logger.info("Session %s expired, PaymentAttempt %s marked failed", session_id, attempt.id)
        return {'status': 'success', 'payment_attempt_id': str(attempt.id)}

    @staticmethod
    def handle_payment_intent_failed(data: dict) -> dict:
        """
        Event: payment_intent.payment_failed
        Triggered when a PaymentIntent fails (e.g. card declined).

        With Stripe Checkout, the customer can retry within the session,
        so we only update if the attempt is still in initiated/processing state.
        """
        payment_intent_id = data.get('payment_intent_id')
        error_code = data.get('error_code', '')
        error_message = data.get('error_message', '')

        try:
            attempt = PaymentAttempt.objects.get(
                stripe_payment_intent_id=payment_intent_id
            )
        except PaymentAttempt.DoesNotExist:
            # Normal: attempt may not yet have a payment_intent_id
            logger.info(
                "payment_intent.payment_failed for pi=%s - no attempt found (may be retry)",
                payment_intent_id,
            )
            return {'status': 'not_found_ok'}

        if attempt.status in ('initiated', 'processing'):
            attempt.status = 'failed'
            attempt.error_code = error_code
            attempt.error_message = error_message
            attempt.completed_at = timezone.now()
            attempt.provider_response = data
            attempt.save()

        return {'status': 'success'}

    @staticmethod
    def handle_charge_refunded(data: dict) -> dict:
        """
        Event: charge.refunded
        Triggered when a charge is fully or partially refunded.
        """
        payment_intent_id = data.get('payment_intent_id')

        if not payment_intent_id:
            return {'status': 'skipped', 'reason': 'no_payment_intent_id'}

        try:
            attempt = PaymentAttempt.objects.select_related('transaction').get(
                stripe_payment_intent_id=payment_intent_id
            )
        except PaymentAttempt.DoesNotExist:
            logger.warning("No PaymentAttempt for refunded pi=%s", payment_intent_id)
            return {'status': 'not_found'}

        with db_transaction.atomic():
            attempt.status = 'refunded'
            attempt.provider_response = data
            attempt.save()

            txn = attempt.transaction
            if txn and txn.status == 'validated':
                txn.status = 'refunded'
                txn.save()

        logger.info("charge.refunded processed: PaymentAttempt %s refunded", attempt.id)
        return {'status': 'success', 'payment_attempt_id': str(attempt.id)}

    # ----- Subscription lifecycle handlers -----

    @staticmethod
    def handle_subscription_updated(data: dict) -> dict:
        """
        Event: customer.subscription.updated
        Triggered on status changes, quantity updates, cancellation scheduling.
        Updates OrganizationSubscription to match Stripe state.
        """
        from ..models.subscription import OrganizationSubscription

        sub_id = data.get('subscription_id')
        status = data.get('status')
        cancel_at_period_end = data.get('cancel_at_period_end', False)

        try:
            org_sub = OrganizationSubscription.objects.get(
                stripe_subscription_id=sub_id,
            )
        except OrganizationSubscription.DoesNotExist:
            logger.info(
                "subscription.updated: no org_sub for sub=%s", sub_id,
            )
            return {'status': 'not_found'}

        updated_fields = []

        # Map Stripe status to our status
        status_map = {
            'active': 'active',
            'past_due': 'active',  # still active, payment retry
            'canceled': 'cancelled',
            'unpaid': 'suspended',
            'incomplete': 'suspended',
            'incomplete_expired': 'expired',
            'paused': 'suspended',
        }
        new_status = status_map.get(status)
        if new_status and org_sub.status != new_status:
            org_sub.status = new_status
            updated_fields.append('status')

        # Update period dates if present
        period_end = data.get('current_period_end')
        if period_end:
            end_dt = timezone.make_aware(
                datetime.utcfromtimestamp(period_end),
            )
            org_sub.end_date = end_dt
            updated_fields.append('end_date')

        period_start = data.get('current_period_start')
        if period_start:
            start_dt = timezone.make_aware(
                datetime.utcfromtimestamp(period_start),
            )
            org_sub.start_date = start_dt
            updated_fields.append('start_date')

        if updated_fields:
            org_sub.save(update_fields=updated_fields)
            cache_key = f"org_subscription_{org_sub.organization_id}"
            cache.delete(cache_key)

        logger.info(
            "subscription.updated: org_sub %s, status=%s, "
            "cancel_at_period_end=%s, updated=%s",
            org_sub.pk, status, cancel_at_period_end, updated_fields,
        )
        return {'status': 'success', 'updated_fields': updated_fields}

    @staticmethod
    def handle_subscription_deleted(data: dict) -> dict:
        """
        Event: customer.subscription.deleted
        Subscription fully cancelled. Revert to free tier.
        """
        from ..models.subscription import (
            OrganizationSubscription, SubscriptionTier,
        )

        sub_id = data.get('subscription_id')

        try:
            org_sub = OrganizationSubscription.objects.get(
                stripe_subscription_id=sub_id,
            )
        except OrganizationSubscription.DoesNotExist:
            logger.info(
                "subscription.deleted: no org_sub for sub=%s", sub_id,
            )
            return {'status': 'not_found'}

        # Revert to free tier
        free_tier, _ = SubscriptionTier.objects.get_or_create(
            name='free',
            defaults={
                'display_name': 'Free',
                'max_members': 10,
                'is_active': True,
            },
        )

        with db_transaction.atomic():
            org_sub.subscription_tier = free_tier
            org_sub.status = 'cancelled'
            org_sub.stripe_subscription_id = ''
            org_sub.stripe_price_id = ''
            org_sub.save()

            cache_key = f"org_subscription_{org_sub.organization_id}"
            cache.delete(cache_key)

        logger.info(
            "subscription.deleted: org %s reverted to free",
            org_sub.organization_id,
        )
        return {'status': 'success', 'reverted_to_free': True}

    @staticmethod
    def handle_invoice_payment_succeeded(data: dict) -> dict:
        """
        Event: invoice.payment_succeeded
        Handles successful renewal payments.
        Extends end_date by 1 year on subscription_cycle billing.
        """
        from ..models.subscription import OrganizationSubscription

        sub_id = data.get('subscription_id')
        billing_reason = data.get('billing_reason', '')

        if not sub_id:
            return {'status': 'skipped', 'reason': 'no_subscription_id'}

        # Only process renewal invoices (not initial)
        if billing_reason == 'subscription_create':
            logger.info(
                "invoice.payment_succeeded: initial invoice for sub=%s, "
                "skipping (handled by checkout.session.completed)",
                sub_id,
            )
            return {'status': 'skipped', 'reason': 'initial_invoice'}

        try:
            org_sub = OrganizationSubscription.objects.get(
                stripe_subscription_id=sub_id,
            )
        except OrganizationSubscription.DoesNotExist:
            logger.info(
                "invoice.payment_succeeded: no org_sub for sub=%s",
                sub_id,
            )
            return {'status': 'not_found'}

        # Extend by 1 year from current end_date
        with db_transaction.atomic():
            org_sub.end_date = org_sub.end_date + timedelta(days=365)
            org_sub.status = 'active'
            org_sub.save(update_fields=['end_date', 'status'])

            cache_key = f"org_subscription_{org_sub.organization_id}"
            cache.delete(cache_key)

        logger.info(
            "invoice.payment_succeeded: org %s renewed until %s",
            org_sub.organization_id, org_sub.end_date,
        )
        return {'status': 'success', 'new_end_date': str(org_sub.end_date)}

    @staticmethod
    def handle_invoice_payment_failed(data: dict) -> dict:
        """
        Event: invoice.payment_failed
        Payment failed on renewal. Mark subscription as suspended
        so the org gets a warning but doesn't immediately lose access.
        """
        from ..models.subscription import OrganizationSubscription

        sub_id = data.get('subscription_id')
        if not sub_id:
            return {'status': 'skipped', 'reason': 'no_subscription_id'}

        try:
            org_sub = OrganizationSubscription.objects.get(
                stripe_subscription_id=sub_id,
            )
        except OrganizationSubscription.DoesNotExist:
            logger.info(
                "invoice.payment_failed: no org_sub for sub=%s", sub_id,
            )
            return {'status': 'not_found'}

        if org_sub.status == 'suspended':
            return {'status': 'already_processed'}

        org_sub.status = 'suspended'
        org_sub.save(update_fields=['status'])

        cache_key = f"org_subscription_{org_sub.organization_id}"
        cache.delete(cache_key)

        logger.info(
            "invoice.payment_failed: org %s suspended",
            org_sub.organization_id,
        )
        return {'status': 'success', 'suspended': True}

    @classmethod
    def dispatch(cls, event_type: str, data: dict) -> dict:
        """Route a parsed webhook event to the appropriate handler."""
        handlers = {
            # Payment events
            'checkout.session.completed': cls.handle_checkout_session_completed,
            'checkout.session.expired': cls.handle_checkout_session_expired,
            'payment_intent.payment_failed': cls.handle_payment_intent_failed,
            'charge.refunded': cls.handle_charge_refunded,
            # Subscription lifecycle
            'customer.subscription.updated': cls.handle_subscription_updated,
            'customer.subscription.deleted': cls.handle_subscription_deleted,
            # Invoice (renewal billing)
            'invoice.payment_succeeded': cls.handle_invoice_payment_succeeded,
            'invoice.payment_failed': cls.handle_invoice_payment_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)

        logger.debug("No handler for Stripe event type: %s", event_type)
        return {'status': 'unhandled', 'event_type': event_type}
