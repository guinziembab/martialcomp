"""
Tests for the payment system integration
"""
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, call
import json
from decimal import Decimal

from ..models import Tenant
from ..payments.base import PaymentProvider, PaymentProviderFactory, PaymentProviderError
from ..payments.stripe_provider import StripeProvider
from ..payments.service import TenantPaymentService


class MockPaymentProvider(PaymentProvider):
    """Mock payment provider for testing"""
    
    def validate_config(self):
        if 'test_key' not in self.config:
            raise PaymentProviderError("Missing test_key")
    
    def create_customer(self, tenant_data):
        return f"mock_customer_{tenant_data.get('email', 'test')}"
    
    def create_subscription(self, customer_id, plan_id, metadata=None):
        return {
            'id': f'mock_sub_{plan_id}',
            'status': 'active',
            'customer_id': customer_id,
        }
    
    def cancel_subscription(self, subscription_id, immediate=False):
        return {
            'id': subscription_id,
            'status': 'cancelled' if immediate else 'cancelling',
        }
    
    def process_payment(self, amount, currency, customer_id, description="", metadata=None):
        return {
            'id': f'mock_payment_{amount}',
            'status': 'succeeded',
            'amount': float(amount),
            'currency': currency,
        }
    
    def create_checkout_session(self, items, success_url, cancel_url, metadata=None):
        return f"https://mock-checkout.com/session/{items[0]['plan_id']}"
    
    def handle_webhook(self, payload, signature):
        data = json.loads(payload)
        return {
            'event_type': data.get('type'),
            'data': data.get('data', {}),
        }


class PaymentProviderFactoryTest(TestCase):
    """Test payment provider factory"""
    
    def setUp(self):
        # Register mock provider
        PaymentProviderFactory.register_provider('mock', MockPaymentProvider)
    
    def test_provider_registration(self):
        """Test registering and creating providers"""
        config = {'test_key': 'abc123'}
        provider = PaymentProviderFactory.create_provider('mock', config)
        
        self.assertIsInstance(provider, MockPaymentProvider)
        self.assertEqual(provider.config, config)
    
    def test_invalid_provider_class(self):
        """Test registering invalid provider class"""
        class InvalidProvider:
            pass
        
        with self.assertRaises(ValueError):
            PaymentProviderFactory.register_provider('invalid', InvalidProvider)
    
    def test_unknown_provider(self):
        """Test creating unknown provider"""
        with self.assertRaises(ValueError):
            PaymentProviderFactory.create_provider('unknown', {})


class StripeProviderTest(TestCase):
    """Test Stripe payment provider"""
    
    def setUp(self):
        self.config = {
            'secret_key': 'sk_test_123',
            'publishable_key': 'pk_test_123',
            'webhook_secret': 'whsec_123',
        }
        
        # Mock stripe module
        self.stripe_patcher = patch('multitenant.payments.stripe_provider.stripe')
        self.mock_stripe = self.stripe_patcher.start()
        
        self.provider = StripeProvider(self.config)
    
    def tearDown(self):
        self.stripe_patcher.stop()
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config should not raise
        provider = StripeProvider(self.config)
        
        # Missing key should raise
        with self.assertRaises(PaymentProviderError):
            StripeProvider({'secret_key': 'sk_test_123'})
        
        # Invalid key format should raise
        with self.assertRaises(PaymentProviderError):
            StripeProvider({
                'secret_key': 'invalid_key',
                'publishable_key': 'pk_test_123',
                'webhook_secret': 'whsec_123',
            })
    
    def test_create_customer(self):
        """Test creating a Stripe customer"""
        # Mock Stripe API
        mock_customer = MagicMock()
        mock_customer.id = 'cus_123'
        self.mock_stripe.Customer.create.return_value = mock_customer
        
        # Create customer
        tenant_data = {
            'email': 'test@example.com',
            'name': 'Test Club',
            'tenant_id': '123',
        }
        customer_id = self.provider.create_customer(tenant_data)
        
        # Verify API call
        self.mock_stripe.Customer.create.assert_called_once_with(
            email='test@example.com',
            name='Test Club',
            metadata={'tenant_id': '123', 'tenant_slug': None}
        )
        
        self.assertEqual(customer_id, 'cus_123')
    
    def test_create_subscription(self):
        """Test creating a subscription"""
        # Mock Stripe API
        mock_sub = MagicMock()
        mock_sub.id = 'sub_123'
        mock_sub.status = 'active'
        mock_sub.current_period_start = 1234567890
        mock_sub.current_period_end = 1234567890
        mock_sub.cancel_at_period_end = False
        mock_sub.items.data = []
        
        self.mock_stripe.Subscription.create.return_value = mock_sub
        
        # Mock price mapping
        self.provider.config['price_mapping'] = {
            'essentials': 'price_essentials_eur'
        }
        
        # Create subscription
        result = self.provider.create_subscription('cus_123', 'essentials')
        
        # Verify API call
        self.mock_stripe.Subscription.create.assert_called_once()
        
        # Verify result
        self.assertEqual(result['id'], 'sub_123')
        self.assertEqual(result['status'], 'active')
    
    def test_webhook_handling(self):
        """Test webhook event handling"""
        # Mock Stripe webhook
        mock_event = {
            'id': 'evt_123',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_123',
                    'customer': 'cus_123',
                    'status': 'active',
                }
            }
        }
        
        self.mock_stripe.Webhook.construct_event.return_value = mock_event
        
        # Handle webhook
        payload = json.dumps(mock_event).encode()
        result = self.provider.handle_webhook(payload, 'sig_123')
        
        # Verify result
        self.assertEqual(result['event_type'], 'customer.subscription.updated')
        self.assertEqual(result['data']['subscription_id'], 'sub_123')


class TenantPaymentServiceTest(TestCase):
    """Test tenant payment service"""
    
    def setUp(self):
        # Create test user and tenant
        self.owner = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        
        self.tenant = Tenant.objects.create(
            name="Test Club",
            slug="test-club",
            schema_name="tenant_test_club",
            domain="test-club.martialcomp.com",
            owner=self.owner,
            continent="europe_west",
            subscription_plan="essentials",
            is_active=True
        )
        
        # Mock payment provider
        self.mock_provider = MagicMock(spec=PaymentProvider)
        
        # Patch provider factory
        self.factory_patcher = patch('multitenant.payments.service.PaymentProviderFactory')
        self.mock_factory = self.factory_patcher.start()
        self.mock_factory.create_provider.return_value = self.mock_provider
        
        self.service = TenantPaymentService()
        
        # Mock settings
        self.settings_patcher = patch('multitenant.payments.service.settings')
        self.mock_settings = self.settings_patcher.start()
        self.mock_settings.PAYMENT_PROVIDERS = {
            'stripe': {'test': 'config'}
        }
        self.mock_settings.SITE_URL = 'https://martialcomp.com'
    
    def tearDown(self):
        self.factory_patcher.stop()
        self.settings_patcher.stop()
    
    def test_get_provider_for_tenant(self):
        """Test getting appropriate provider for tenant"""
        provider = self.service.get_provider_for_tenant(self.tenant)
        
        # Should use stripe for europe_west
        self.mock_factory.create_provider.assert_called_with(
            'stripe',
            {'test': 'config'}
        )
        
        self.assertEqual(provider, self.mock_provider)
    
    def test_create_tenant_subscription(self):
        """Test creating subscription for tenant"""
        # Mock provider responses
        self.mock_provider.create_customer.return_value = 'cus_123'
        self.mock_provider.create_subscription.return_value = {
            'id': 'sub_123',
            'status': 'active',
        }
        
        # Create subscription
        result = self.service.create_tenant_subscription(self.tenant, 'essentials')
        
        # Verify customer creation
        self.mock_provider.create_customer.assert_called_once()
        
        # Verify subscription creation
        self.mock_provider.create_subscription.assert_called_with(
            customer_id='cus_123',
            plan_id='essentials',
            metadata={
                'tenant_id': str(self.tenant.id),
                'tenant_name': 'Test Club',
                'continent': 'europe_west',
            }
        )
        
        # Verify tenant was updated
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.payment_config['customer_id'], 'cus_123')
        self.assertEqual(self.tenant.payment_config['subscription_id'], 'sub_123')
    
    def test_cancel_subscription(self):
        """Test cancelling subscription"""
        # Setup tenant with subscription
        self.tenant.payment_config = {
            'customer_id': 'cus_123',
            'subscription_id': 'sub_123',
        }
        self.tenant.save()
        
        # Mock cancellation
        self.mock_provider.cancel_subscription.return_value = {
            'id': 'sub_123',
            'status': 'cancelled',
        }
        
        # Cancel subscription
        result = self.service.cancel_tenant_subscription(self.tenant, immediate=True)
        
        # Verify API call
        self.mock_provider.cancel_subscription.assert_called_with(
            'sub_123',
            immediate=True
        )
        
        # Verify tenant was updated
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.subscription_status, 'cancelled')
    
    def test_webhook_processing(self):
        """Test webhook event processing"""
        # Mock provider webhook handling
        self.mock_provider.handle_webhook.return_value = {
            'event_type': 'customer.subscription.updated',
            'data': {
                'subscription_id': 'sub_123',
                'status': 'active',
                'cancel_at_period_end': False,
            }
        }
        
        # Setup tenant with subscription
        self.tenant.payment_config = {
            'subscription_id': 'sub_123',
        }
        self.tenant.save()
        
        # Process webhook
        payload = b'{"test": "data"}'
        result = self.service.handle_webhook('stripe', payload, 'sig_123')
        
        # Verify provider was called
        self.mock_provider.handle_webhook.assert_called_with(payload, 'sig_123')
        
        # Verify tenant was updated
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.subscription_status, 'active')
    
    def test_regional_provider_selection(self):
        """Test provider selection based on region"""
        test_cases = [
            ('africa', 'paystack'),
            ('south_america', 'mercadopago'),
            ('asia_other', 'alipay'),
            ('north_america', 'stripe'),
        ]
        
        for continent, expected_provider in test_cases:
            self.tenant.continent = continent
            self.tenant.save()
            
            # Get provider
            provider = self.service.get_provider_for_tenant(self.tenant)
            
            # Verify correct provider was selected
            expected_call = call(expected_provider, {'test': 'config'})
            self.assertIn(expected_call, self.mock_factory.create_provider.call_args_list)