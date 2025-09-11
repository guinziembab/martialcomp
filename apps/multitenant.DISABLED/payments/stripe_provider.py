"""
Stripe payment provider implementation
"""
from typing import Dict, Any, Optional
from decimal import Decimal
import stripe
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging

from .base import PaymentProvider, PaymentProviderError, PaymentProviderFactory

logger = logging.getLogger(__name__)


class StripeProvider(PaymentProvider):
    """
    Stripe payment provider implementation using Stripe Connect.
    Handles both platform fees and tenant payouts.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Set Stripe API key
        stripe.api_key = self.config.get('secret_key')
        
    def validate_config(self) -> None:
        """Validate Stripe configuration"""
        required_keys = ['secret_key', 'publishable_key', 'webhook_secret']
        
        for key in required_keys:
            if key not in self.config:
                raise PaymentProviderError(f"Missing required config key: {key}")
        
        if not self.config['secret_key'].startswith(('sk_test_', 'sk_live_')):
            raise PaymentProviderError("Invalid Stripe secret key format")
    
    def create_customer(self, tenant_data: Dict[str, Any]) -> str:
        """
        Create a Stripe customer for a tenant.
        
        Args:
            tenant_data: Must include 'email', 'name', and optionally 'metadata'
            
        Returns:
            Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=tenant_data['email'],
                name=tenant_data['name'],
                metadata=tenant_data.get('metadata', {
                    'tenant_id': tenant_data.get('tenant_id'),
                    'tenant_slug': tenant_data.get('tenant_slug'),
                })
            )
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise PaymentProviderError(f"Failed to create customer: {str(e)}")
    
    def create_subscription(self, customer_id: str, plan_id: str,
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a Stripe subscription.
        
        Args:
            customer_id: Stripe customer ID
            plan_id: MartialComp plan ID to map to Stripe price ID
            metadata: Additional metadata for the subscription
            
        Returns:
            Subscription details
        """
        try:
            # Map internal plan ID to Stripe price ID
            price_id = self._get_stripe_price_id(plan_id)
            
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                metadata=metadata or {},
                # Add trial period if configured
                trial_period_days=self.config.get('trial_days', 0),
                # Enable tax calculation if configured
                automatic_tax={'enabled': self.config.get('automatic_tax', False)},
            )
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'items': [{
                    'price_id': item.price.id,
                    'quantity': item.quantity
                } for item in subscription.items.data]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise PaymentProviderError(f"Failed to create subscription: {str(e)}")
    
    def cancel_subscription(self, subscription_id: str,
                          immediate: bool = False) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            if immediate:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': subscription.canceled_at,
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            raise PaymentProviderError(f"Failed to cancel subscription: {str(e)}")
    
    def process_payment(self, amount: Decimal, currency: str,
                       customer_id: str, description: str = "",
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a one-time payment using Stripe PaymentIntent"""
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                customer=customer_id,
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True},
            )
            
            return {
                'id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'status': payment_intent.status,
                'amount': payment_intent.amount / 100,  # Convert back to major units
                'currency': payment_intent.currency,
                'requires_action': payment_intent.status == 'requires_action',
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing payment: {e}")
            raise PaymentProviderError(f"Failed to process payment: {str(e)}")
    
    def create_checkout_session(self, items: list, success_url: str,
                              cancel_url: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a Stripe Checkout session"""
        try:
            line_items = []
            for item in items:
                line_item = {
                    'price': self._get_stripe_price_id(item['plan_id']),
                    'quantity': item.get('quantity', 1),
                }
                line_items.append(line_item)
            
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=line_items,
                mode='subscription',  # or 'payment' for one-time
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata or {},
                # Enable tax collection if configured
                automatic_tax={'enabled': self.config.get('automatic_tax', False)},
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {e}")
            raise PaymentProviderError(f"Failed to create checkout session: {str(e)}")
    
    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.config['webhook_secret']
            )
            
            # Process different event types
            event_type = event['type']
            event_data = event['data']['object']
            
            result = {
                'event_type': event_type,
                'event_id': event['id'],
                'data': {}
            }
            
            if event_type == 'checkout.session.completed':
                result['data'] = {
                    'session_id': event_data['id'],
                    'customer_id': event_data['customer'],
                    'subscription_id': event_data.get('subscription'),
                    'metadata': event_data.get('metadata', {}),
                }
                
            elif event_type == 'customer.subscription.updated':
                result['data'] = {
                    'subscription_id': event_data['id'],
                    'customer_id': event_data['customer'],
                    'status': event_data['status'],
                    'cancel_at_period_end': event_data['cancel_at_period_end'],
                    'current_period_end': event_data['current_period_end'],
                }
                
            elif event_type == 'invoice.payment_succeeded':
                result['data'] = {
                    'invoice_id': event_data['id'],
                    'customer_id': event_data['customer'],
                    'subscription_id': event_data['subscription'],
                    'amount_paid': event_data['amount_paid'] / 100,
                    'currency': event_data['currency'],
                }
                
            elif event_type == 'payment_intent.succeeded':
                result['data'] = {
                    'payment_intent_id': event_data['id'],
                    'customer_id': event_data['customer'],
                    'amount': event_data['amount'] / 100,
                    'currency': event_data['currency'],
                    'metadata': event_data.get('metadata', {}),
                }
            
            return result
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise PaymentProviderError("Invalid webhook signature")
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            raise PaymentProviderError(f"Webhook processing error: {str(e)}")
    
    def get_customer_portal_url(self, customer_id: str, return_url: str) -> str:
        """Get Stripe customer portal URL"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url
            )
            return session.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {e}")
            raise PaymentProviderError(f"Failed to create portal session: {str(e)}")
    
    def update_subscription(self, subscription_id: str,
                          plan_id: Optional[str] = None,
                          quantity: Optional[int] = None) -> Dict[str, Any]:
        """Update a Stripe subscription"""
        try:
            update_params = {}
            
            if plan_id:
                price_id = self._get_stripe_price_id(plan_id)
                # Get subscription to find the item to update
                subscription = stripe.Subscription.retrieve(subscription_id)
                item_id = subscription.items.data[0].id
                
                update_params['items'] = [{
                    'id': item_id,
                    'price': price_id,
                }]
            
            if quantity is not None:
                if 'items' in update_params:
                    update_params['items'][0]['quantity'] = quantity
                else:
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    item_id = subscription.items.data[0].id
                    update_params['items'] = [{
                        'id': item_id,
                        'quantity': quantity,
                    }]
            
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                **update_params
            )
            
            return {
                'id': updated_subscription.id,
                'status': updated_subscription.status,
                'items': [{
                    'price_id': item.price.id,
                    'quantity': item.quantity
                } for item in updated_subscription.items.data]
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error updating subscription: {e}")
            raise PaymentProviderError(f"Failed to update subscription: {str(e)}")
    
    def _get_stripe_price_id(self, plan_id: str) -> str:
        """
        Map internal plan ID to Stripe price ID.
        This should be configured in settings or database.
        """
        # Example mapping - should be loaded from configuration
        price_mapping = self.config.get('price_mapping', {
            'essentials': 'price_essentials_eur',
            'masters': 'price_masters_eur',
            'champion': 'price_champion_eur',
        })
        
        if plan_id not in price_mapping:
            raise PaymentProviderError(f"Unknown plan ID: {plan_id}")
        
        return price_mapping[plan_id]


# Register Stripe provider
PaymentProviderFactory.register_provider('stripe', StripeProvider)