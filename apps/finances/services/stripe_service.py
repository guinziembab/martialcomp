"""
Stripe payment service for MartialComp.

Phase 1: Checkout Sessions (one-time payments)
Phase 3: Subscription billing (per-seat recurring via pre-created Price IDs)

Ported and adapted from apps/multitenant.DISABLED/payments/stripe_provider.py.
Key differences from the multitenant version:
  - Reads API keys from django.conf.settings (not a per-tenant config dict)
  - Uses Stripe Checkout Sessions (hosted page) for PCI-DSS compliance
  - Integrated with apps/finances/ Transaction and PaymentAttempt models
  - Platform merchant model (no Stripe Connect)
"""
import logging
from typing import Optional

import stripe
from django.conf import settings

logger = logging.getLogger(__name__)


class StripeServiceError(Exception):
    """Raised when Stripe API calls fail."""
    pass


class StripeService:
    """
    Stateless service class for all Stripe interactions.

    All methods are @staticmethod to avoid instantiation overhead.
    The stripe SDK is configured at call time using settings values.

    Capabilities:
      - Checkout Sessions (one-time payments and subscriptions)
      - Customer management (get_or_create_customer)
      - Subscription management (update quantity, cancel)
      - Webhook event handling with signature verification
      - Refunds via PaymentIntent
      - Session retrieval for status verification
    """

    @staticmethod
    def _configure_stripe() -> None:
        """
        Set the Stripe API key from settings.
        Called at the start of every Stripe API call.
        """
        secret_key = getattr(settings, 'STRIPE_SECRET_KEY', '')
        if not secret_key:
            raise StripeServiceError(
                "STRIPE_SECRET_KEY is not configured. "
                "Add it to your environment variables."
            )
        if not secret_key.startswith(('sk_test_', 'sk_live_')):
            raise StripeServiceError(
                "STRIPE_SECRET_KEY has an invalid format. "
                "It must start with 'sk_test_' or 'sk_live_'."
            )
        stripe.api_key = secret_key
        stripe.api_version = getattr(settings, 'STRIPE_API_VERSION', '2023-10-16')

    @staticmethod
    def create_checkout_session(
        line_items: list,
        success_url: str,
        cancel_url: str,
        metadata: Optional[dict] = None,
        customer_email: Optional[str] = None,
        customer: Optional[str] = None,
        mode: str = 'payment',
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout Session (hosted payment page).

        Args:
            line_items: List of dicts. For mode='payment':
                - name (str), description (str, opt), amount_cents (int),
                  currency (str), quantity (int, default 1)
              For mode='subscription' with pre-created Prices:
                - price (str): Stripe Price ID (price_...)
                - quantity (int)
            success_url: Redirect URL after payment.
            cancel_url: Redirect URL if user cancels.
            metadata: Dict of string key-value pairs stored on the session.
            customer_email: Pre-fill the email on Stripe's checkout page.
            customer: Stripe Customer ID (cus_...). Required for subscriptions.
            mode: 'payment' for one-time, 'subscription' for recurring.

        Returns:
            stripe.checkout.Session. Use .url to redirect, .id to track.

        Raises:
            StripeServiceError on any Stripe API error.
        """
        StripeService._configure_stripe()

        stripe_line_items = []
        for item in line_items:
            if 'price' in item:
                # Pre-created Price ID (used for subscriptions)
                stripe_line_items.append({
                    'price': item['price'],
                    'quantity': item.get('quantity', 1),
                })
            else:
                # Inline price_data (used for one-time payments)
                line_item = {
                    'price_data': {
                        'currency': item['currency'].lower(),
                        'unit_amount': item['amount_cents'],
                        'product_data': {
                            'name': item['name'],
                        },
                    },
                    'quantity': item.get('quantity', 1),
                }
                if item.get('description'):
                    line_item['price_data']['product_data']['description'] = item['description']
                stripe_line_items.append(line_item)

        session_params = {
            'payment_method_types': ['card'],
            'line_items': stripe_line_items,
            'mode': mode,
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': metadata or {},
        }

        if customer:
            session_params['customer'] = customer
        elif customer_email:
            session_params['customer_email'] = customer_email

        try:
            session = stripe.checkout.Session.create(**session_params)
            logger.info(
                "Stripe checkout session created: %s, mode=%s",
                session.id, mode,
            )
            return session
        except stripe.error.StripeError as e:
            logger.error("Stripe error creating checkout session: %s", e)
            raise StripeServiceError(f"Failed to create checkout session: {e}")

    @staticmethod
    def retrieve_session(session_id: str) -> stripe.checkout.Session:
        """
        Retrieve a Stripe Checkout Session by its ID.

        Returns:
            stripe.checkout.Session with .payment_status, .payment_intent, .metadata
        """
        StripeService._configure_stripe()
        try:
            return stripe.checkout.Session.retrieve(session_id)
        except stripe.error.StripeError as e:
            logger.error("Stripe error retrieving session %s: %s", session_id, e)
            raise StripeServiceError(f"Failed to retrieve session: {e}")

    @staticmethod
    def handle_webhook(payload: bytes, sig_header: str) -> dict:
        """
        Verify Stripe webhook signature and parse the event.

        IMPORTANT: payload must be raw request.body (bytes), not parsed JSON.

        Args:
            payload: Raw request body bytes
            sig_header: Value of the 'Stripe-Signature' HTTP header

        Returns:
            Dict with 'event_type', 'event_id', 'data' keys.

        Raises:
            StripeServiceError on invalid signature.
        """
        StripeService._configure_stripe()

        webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        if not webhook_secret:
            raise StripeServiceError("STRIPE_WEBHOOK_SECRET is not configured.")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except stripe.error.SignatureVerificationError as e:
            logger.warning("Invalid Stripe webhook signature: %s", e)
            raise StripeServiceError("Invalid webhook signature")
        except Exception as e:
            logger.error("Error constructing Stripe event: %s", e)
            raise StripeServiceError(f"Webhook construction error: {e}")

        event_type = event['type']
        event_data = event['data']['object']

        result = {
            'event_type': event_type,
            'event_id': event['id'],
            'data': {},
        }

        if event_type == 'checkout.session.completed':
            result['data'] = {
                'session_id': event_data['id'],
                'payment_intent_id': event_data.get('payment_intent'),
                'subscription_id': event_data.get('subscription'),
                'customer_id': event_data.get('customer'),
                'payment_status': event_data.get('payment_status'),
                'customer_email': event_data.get('customer_email'),
                'amount_total': event_data.get('amount_total'),
                'currency': event_data.get('currency'),
                'mode': event_data.get('mode'),
                'metadata': event_data.get('metadata', {}),
            }
        elif event_type == 'checkout.session.expired':
            result['data'] = {
                'session_id': event_data['id'],
                'metadata': event_data.get('metadata', {}),
            }
        elif event_type == 'payment_intent.payment_failed':
            last_error = event_data.get('last_payment_error') or {}
            result['data'] = {
                'payment_intent_id': event_data['id'],
                'error_code': last_error.get('code', ''),
                'error_message': last_error.get('message', ''),
                'metadata': event_data.get('metadata', {}),
            }
        elif event_type == 'charge.refunded':
            result['data'] = {
                'payment_intent_id': event_data.get('payment_intent'),
                'amount_refunded': event_data.get('amount_refunded'),
                'currency': event_data.get('currency'),
            }
        elif event_type in (
            'customer.subscription.updated',
            'customer.subscription.deleted',
        ):
            result['data'] = {
                'subscription_id': event_data.get('id'),
                'customer_id': event_data.get('customer'),
                'status': event_data.get('status'),
                'current_period_start': event_data.get('current_period_start'),
                'current_period_end': event_data.get('current_period_end'),
                'cancel_at_period_end': event_data.get('cancel_at_period_end'),
                'items': [
                    {
                        'price_id': item.get('price', {}).get('id'),
                        'quantity': item.get('quantity'),
                    }
                    for item in event_data.get('items', {}).get('data', [])
                ],
                'metadata': event_data.get('metadata', {}),
            }
        elif event_type in (
            'invoice.payment_succeeded',
            'invoice.payment_failed',
        ):
            result['data'] = {
                'invoice_id': event_data.get('id'),
                'subscription_id': event_data.get('subscription'),
                'customer_id': event_data.get('customer'),
                'amount_paid': event_data.get('amount_paid'),
                'amount_due': event_data.get('amount_due'),
                'currency': event_data.get('currency'),
                'billing_reason': event_data.get('billing_reason'),
                'status': event_data.get('status'),
                'metadata': event_data.get('metadata', {}),
            }
        else:
            logger.info("Unhandled Stripe event type: %s (id=%s)", event_type, event['id'])

        return result

    @staticmethod
    def create_refund(
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        reason: str = 'requested_by_customer',
    ) -> stripe.Refund:
        """
        Create a Stripe refund for a PaymentIntent.

        Args:
            payment_intent_id: Stripe PaymentIntent ID (pi_...)
            amount_cents: Amount to refund in cents. None = full refund.
            reason: 'duplicate', 'fraudulent', or 'requested_by_customer'
        """
        StripeService._configure_stripe()

        params = {
            'payment_intent': payment_intent_id,
            'reason': reason,
        }
        if amount_cents is not None:
            params['amount'] = amount_cents

        try:
            refund = stripe.Refund.create(**params)
            logger.info(
                "Stripe refund created: %s for pi=%s, amount=%s",
                refund.id, payment_intent_id, amount_cents,
            )
            return refund
        except stripe.error.StripeError as e:
            logger.error("Stripe error creating refund for %s: %s", payment_intent_id, e)
            raise StripeServiceError(f"Failed to create refund: {e}")

    @staticmethod
    def get_payment_intent(payment_intent_id: str) -> stripe.PaymentIntent:
        """Retrieve a Stripe PaymentIntent by ID."""
        StripeService._configure_stripe()
        try:
            return stripe.PaymentIntent.retrieve(payment_intent_id)
        except stripe.error.StripeError as e:
            logger.error("Stripe error retrieving PaymentIntent %s: %s", payment_intent_id, e)
            raise StripeServiceError(f"Failed to retrieve PaymentIntent: {e}")

    # ----- Subscription helpers (Phase 3) -----

    @staticmethod
    def get_or_create_customer(
        email: str,
        name: Optional[str] = None,
        metadata: Optional[dict] = None,
        existing_customer_id: Optional[str] = None,
    ) -> stripe.Customer:
        """
        Get an existing Stripe Customer or create a new one.

        Args:
            email: Customer email address.
            name: Customer display name (e.g. organization name).
            metadata: Key-value metadata dict.
            existing_customer_id: If provided, retrieve this customer instead of creating.

        Returns:
            stripe.Customer object.
        """
        StripeService._configure_stripe()

        # If we already have a customer ID, retrieve it
        if existing_customer_id:
            try:
                customer = stripe.Customer.retrieve(existing_customer_id)
                if not customer.get('deleted'):
                    return customer
                logger.warning(
                    "Stripe customer %s was deleted, creating new one",
                    existing_customer_id,
                )
            except stripe.error.StripeError as e:
                logger.warning(
                    "Failed to retrieve customer %s: %s, creating new one",
                    existing_customer_id, e,
                )

        try:
            params = {'email': email}
            if name:
                params['name'] = name
            if metadata:
                params['metadata'] = metadata
            customer = stripe.Customer.create(**params)
            logger.info("Stripe customer created: %s for %s", customer.id, email)
            return customer
        except stripe.error.StripeError as e:
            logger.error("Stripe error creating customer: %s", e)
            raise StripeServiceError(f"Failed to create customer: {e}")

    @staticmethod
    def update_subscription_quantity(
        subscription_id: str,
        new_quantity: int,
    ) -> stripe.Subscription:
        """
        Update the per-seat quantity on an active Stripe subscription.
        Stripe will automatically prorate the charge.

        Args:
            subscription_id: Stripe Subscription ID (sub_...)
            new_quantity: New member count.

        Returns:
            Updated stripe.Subscription object.
        """
        StripeService._configure_stripe()

        if new_quantity < 1:
            new_quantity = 1

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            if not subscription or subscription.status not in ('active', 'trialing'):
                logger.warning(
                    "Cannot update quantity on subscription %s (status=%s)",
                    subscription_id, getattr(subscription, 'status', 'unknown'),
                )
                raise StripeServiceError(
                    f"Subscription {subscription_id} is not active"
                )

            # Update the first (and only) subscription item's quantity
            item_id = subscription['items']['data'][0]['id']
            updated = stripe.Subscription.modify(
                subscription_id,
                items=[{'id': item_id, 'quantity': new_quantity}],
                proration_behavior='create_prorations',
            )
            logger.info(
                "Subscription %s quantity updated to %d",
                subscription_id, new_quantity,
            )
            return updated
        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error updating subscription %s quantity: %s",
                subscription_id, e,
            )
            raise StripeServiceError(f"Failed to update subscription quantity: {e}")

    @staticmethod
    def cancel_subscription(
        subscription_id: str,
        at_period_end: bool = True,
    ) -> stripe.Subscription:
        """
        Cancel a Stripe subscription.

        Args:
            subscription_id: Stripe Subscription ID (sub_...)
            at_period_end: If True, cancel at the end of current billing period.
                           If False, cancel immediately.

        Returns:
            Updated stripe.Subscription object.
        """
        StripeService._configure_stripe()

        try:
            if at_period_end:
                updated = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
                logger.info(
                    "Subscription %s scheduled for cancellation at period end",
                    subscription_id,
                )
            else:
                updated = stripe.Subscription.cancel(subscription_id)
                logger.info("Subscription %s cancelled immediately", subscription_id)
            return updated
        except stripe.error.StripeError as e:
            logger.error(
                "Stripe error cancelling subscription %s: %s",
                subscription_id, e,
            )
            raise StripeServiceError(f"Failed to cancel subscription: {e}")
