"""
Payment service for handling tenant subscriptions and payments
"""
from typing import Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import logging

from ..models import Tenant
from .base import PaymentProviderFactory, PaymentProviderError

logger = logging.getLogger(__name__)


class TenantPaymentService:
    """
    Service for managing tenant payments and subscriptions.
    Handles provider selection based on region and payment processing.
    """
    
    def __init__(self):
        self.provider_config = getattr(settings, 'PAYMENT_PROVIDERS', {})
        self.region_mapping = getattr(settings, 'PAYMENT_REGION_MAPPING', {
            'africa': 'paystack',
            'europe_west': 'stripe',
            'europe_east': 'stripe',
            'north_america': 'stripe',
            'south_america': 'mercadopago',
            'central_america': 'mercadopago',
            'asia_southeast': 'stripe',
            'asia_other': 'alipay',
            'middle_east': 'stripe',
            'oceania': 'stripe',
        })
    
    def get_provider_for_tenant(self, tenant: Tenant):
        """
        Get the appropriate payment provider for a tenant based on their region.
        
        Args:
            tenant: Tenant instance
            
        Returns:
            PaymentProvider instance
        """
        # Check if tenant has a specific provider override
        if tenant.payment_provider:
            provider_name = tenant.payment_provider
        else:
            # Use region-based mapping
            provider_name = self.region_mapping.get(tenant.continent, 'stripe')
        
        # Get provider configuration
        provider_config = self.provider_config.get(provider_name)
        if not provider_config:
            logger.error(f"No configuration found for payment provider: {provider_name}")
            # Fallback to Stripe if no config found
            provider_name = 'stripe'
            provider_config = self.provider_config.get('stripe', {})
        
        return PaymentProviderFactory.create_provider(provider_name, provider_config)
    
    def create_tenant_subscription(self, tenant: Tenant, plan: str) -> Dict[str, Any]:
        """
        Create a subscription for a tenant.
        
        Args:
            tenant: Tenant instance
            plan: Subscription plan identifier
            
        Returns:
            Subscription details
        """
        provider = self.get_provider_for_tenant(tenant)
        
        try:
            # Create or get customer
            if not tenant.payment_config.get('customer_id'):
                customer_id = provider.create_customer({
                    'email': tenant.owner.email,
                    'name': tenant.name,
                    'tenant_id': str(tenant.id),
                    'tenant_slug': tenant.slug,
                })
                
                # Save customer ID
                tenant.payment_config['customer_id'] = customer_id
                tenant.save(update_fields=['payment_config'])
            else:
                customer_id = tenant.payment_config['customer_id']
            
            # Create subscription
            subscription = provider.create_subscription(
                customer_id=customer_id,
                plan_id=plan,
                metadata={
                    'tenant_id': str(tenant.id),
                    'tenant_name': tenant.name,
                    'continent': tenant.continent,
                }
            )
            
            # Update tenant with subscription info
            tenant.payment_config['subscription_id'] = subscription['id']
            tenant.subscription_plan = plan
            tenant.subscription_start_date = timezone.now()
            tenant.subscription_status = subscription['status']
            
            # Set trial if applicable
            if tenant.is_trial:
                tenant.trial_end_date = timezone.now() + timezone.timedelta(days=30)
            
            tenant.save()
            
            return subscription
            
        except PaymentProviderError as e:
            logger.error(f"Error creating subscription for tenant {tenant.id}: {e}")
            raise
    
    def cancel_tenant_subscription(self, tenant: Tenant, immediate: bool = False) -> Dict[str, Any]:
        """
        Cancel a tenant's subscription.
        
        Args:
            tenant: Tenant instance
            immediate: Whether to cancel immediately or at period end
            
        Returns:
            Cancellation details
        """
        provider = self.get_provider_for_tenant(tenant)
        subscription_id = tenant.payment_config.get('subscription_id')
        
        if not subscription_id:
            raise PaymentProviderError("No active subscription found for tenant")
        
        try:
            result = provider.cancel_subscription(subscription_id, immediate=immediate)
            
            # Update tenant
            if immediate:
                tenant.subscription_status = 'cancelled'
                tenant.subscription_end_date = timezone.now()
            else:
                tenant.subscription_status = 'cancelling'
                # Keep existing end date
            
            tenant.save()
            
            return result
            
        except PaymentProviderError as e:
            logger.error(f"Error cancelling subscription for tenant {tenant.id}: {e}")
            raise
    
    def update_tenant_subscription(self, tenant: Tenant, new_plan: str) -> Dict[str, Any]:
        """
        Update a tenant's subscription plan.
        
        Args:
            tenant: Tenant instance
            new_plan: New plan identifier
            
        Returns:
            Updated subscription details
        """
        provider = self.get_provider_for_tenant(tenant)
        subscription_id = tenant.payment_config.get('subscription_id')
        
        if not subscription_id:
            # No existing subscription, create new one
            return self.create_tenant_subscription(tenant, new_plan)
        
        try:
            result = provider.update_subscription(
                subscription_id=subscription_id,
                plan_id=new_plan
            )
            
            # Update tenant
            tenant.subscription_plan = new_plan
            tenant.subscription_status = result.get('status', 'active')
            tenant.save()
            
            return result
            
        except PaymentProviderError as e:
            logger.error(f"Error updating subscription for tenant {tenant.id}: {e}")
            raise
    
    def process_one_time_payment(self, tenant: Tenant, amount: Decimal, 
                               currency: str, description: str) -> Dict[str, Any]:
        """
        Process a one-time payment for a tenant.
        
        Args:
            tenant: Tenant instance
            amount: Payment amount
            currency: ISO currency code
            description: Payment description
            
        Returns:
            Payment result
        """
        provider = self.get_provider_for_tenant(tenant)
        customer_id = tenant.payment_config.get('customer_id')
        
        if not customer_id:
            raise PaymentProviderError("No customer ID found for tenant")
        
        return provider.process_payment(
            amount=amount,
            currency=currency,
            customer_id=customer_id,
            description=description,
            metadata={
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
            }
        )
    
    def create_checkout_url(self, tenant: Tenant, plan: str) -> str:
        """
        Create a checkout URL for tenant to complete payment.
        
        Args:
            tenant: Tenant instance
            plan: Plan to subscribe to
            
        Returns:
            Checkout URL
        """
        provider = self.get_provider_for_tenant(tenant)
        
        items = [{
            'plan_id': plan,
            'quantity': 1,
        }]
        
        success_url = f"{settings.SITE_URL}/tenant/payment/success/"
        cancel_url = f"{settings.SITE_URL}/tenant/payment/cancel/"
        
        return provider.create_checkout_session(
            items=items,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'tenant_id': str(tenant.id),
                'tenant_name': tenant.name,
                'plan': plan,
            }
        )
    
    def get_customer_portal_url(self, tenant: Tenant) -> str:
        """
        Get customer portal URL for tenant to manage their subscription.
        
        Args:
            tenant: Tenant instance
            
        Returns:
            Portal URL
        """
        provider = self.get_provider_for_tenant(tenant)
        customer_id = tenant.payment_config.get('customer_id')
        
        if not customer_id:
            raise PaymentProviderError("No customer ID found for tenant")
        
        return_url = f"{settings.SITE_URL}/tenant/dashboard/"
        
        return provider.get_customer_portal_url(
            customer_id=customer_id,
            return_url=return_url
        )
    
    def handle_webhook(self, provider_name: str, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle webhook from payment provider.
        
        Args:
            provider_name: Name of the payment provider
            payload: Raw webhook payload
            signature: Webhook signature
            
        Returns:
            Processed webhook data
        """
        provider_config = self.provider_config.get(provider_name)
        if not provider_config:
            raise PaymentProviderError(f"Unknown provider: {provider_name}")
        
        provider = PaymentProviderFactory.create_provider(provider_name, provider_config)
        
        try:
            event = provider.handle_webhook(payload, signature)
            
            # Process the event based on type
            self._process_webhook_event(provider_name, event)
            
            return event
            
        except PaymentProviderError as e:
            logger.error(f"Error handling webhook from {provider_name}: {e}")
            raise
    
    def _process_webhook_event(self, provider_name: str, event: Dict[str, Any]):
        """
        Process webhook event and update tenant data accordingly.
        
        Args:
            provider_name: Name of the payment provider
            event: Processed event data
        """
        event_type = event.get('event_type')
        data = event.get('data', {})
        
        # Handle common event types
        if event_type in ['customer.subscription.updated', 'subscription_updated']:
            # Update subscription status
            subscription_id = data.get('subscription_id')
            if subscription_id:
                try:
                    tenant = Tenant.objects.get(
                        payment_config__subscription_id=subscription_id
                    )
                    tenant.subscription_status = data.get('status', 'active')
                    
                    if data.get('cancel_at_period_end'):
                        tenant.subscription_status = 'cancelling'
                    
                    tenant.save()
                    
                except Tenant.DoesNotExist:
                    logger.warning(f"No tenant found for subscription: {subscription_id}")
        
        elif event_type in ['invoice.payment_succeeded', 'payment_succeeded']:
            # Update payment received
            subscription_id = data.get('subscription_id')
            if subscription_id:
                try:
                    tenant = Tenant.objects.get(
                        payment_config__subscription_id=subscription_id
                    )
                    # Update last payment date
                    tenant.payment_config['last_payment_date'] = timezone.now().isoformat()
                    tenant.payment_config['last_payment_amount'] = data.get('amount_paid')
                    tenant.save()
                    
                except Tenant.DoesNotExist:
                    logger.warning(f"No tenant found for subscription: {subscription_id}")
        
        # Log unhandled events for debugging
        else:
            logger.info(f"Unhandled webhook event: {event_type} from {provider_name}")