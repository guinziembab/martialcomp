"""
Comprehensive tests for multi-tenant operations
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import override_settings
from unittest.mock import patch, MagicMock

from ..models import Tenant, Domain, TenantFeature
from ..utils import create_schema_for_tenant, drop_tenant_schema, SchemaContext
from ..middleware import TenantMiddleware, get_current_tenant


class TenantOperationsTest(TransactionTestCase):
    """Test tenant CRUD operations and schema management"""
    
    def setUp(self):
        # Create test users
        self.owner = User.objects.create_user(
            username='owner@test.com',
            email='owner@test.com',
            password='testpass123'
        )
        
    def test_tenant_creation(self):
        """Test creating a tenant with schema"""
        tenant = Tenant.objects.create(
            name="Test Martial Arts Club",
            slug="test-club",
            schema_name="tenant_test_club",
            domain="test-club.martialcomp.com",
            owner=self.owner,
            continent="europe_west",
            subscription_plan="essentials",
            is_active=True
        )
        
        # Test tenant attributes
        self.assertEqual(tenant.name, "Test Martial Arts Club")
        self.assertEqual(tenant.schema_name, "tenant_test_club")
        self.assertTrue(tenant.is_active)
        
        # Test pricing calculation
        self.assertEqual(tenant.get_price_for_plan(), 9.99)
        
        # Test features
        features = tenant.get_available_features()
        self.assertEqual(features['max_members'], 100)
        self.assertEqual(features['max_disciplines'], 2)
        self.assertFalse(features['competitions'])
    
    def test_domain_creation(self):
        """Test domain creation for tenant"""
        tenant = Tenant.objects.create(
            name="Test Club",
            slug="test",
            schema_name="tenant_test",
            domain="test.martialcomp.com",
            owner=self.owner,
            is_active=True
        )
        
        # Create primary domain
        primary_domain = Domain.objects.create(
            tenant=tenant,
            domain="test.martialcomp.com",
            is_primary=True
        )
        
        # Create secondary domain
        secondary_domain = Domain.objects.create(
            tenant=tenant,
            domain="testclub.com",
            is_primary=False
        )
        
        # Test domain relationships
        self.assertEqual(tenant.domains.count(), 2)
        self.assertTrue(primary_domain.is_primary)
        self.assertFalse(secondary_domain.is_primary)
        
        # Test domain string representation
        self.assertEqual(str(primary_domain), "test.martialcomp.com")
    
    def test_tenant_feature_management(self):
        """Test custom feature management"""
        tenant = Tenant.objects.create(
            name="Test Club",
            slug="test",
            schema_name="tenant_test",
            domain="test.martialcomp.com",
            owner=self.owner,
            is_active=True
        )
        
        # Add custom feature
        feature = TenantFeature.objects.create(
            tenant=tenant,
            feature_code='advanced_analytics',
            is_enabled=True,
            metadata={
                'dashboards': ['finance', 'membership'],
                'export_formats': ['pdf', 'excel']
            }
        )
        
        # Test feature attributes
        self.assertEqual(feature.feature_code, 'advanced_analytics')
        self.assertTrue(feature.is_enabled)
        self.assertEqual(feature.metadata['dashboards'], ['finance', 'membership'])
    
    @patch('multitenant.utils.connection')
    def test_schema_creation(self, mock_connection):
        """Test PostgreSQL schema creation"""
        tenant = Tenant.objects.create(
            name="Test Club",
            slug="test",
            schema_name="tenant_test",
            domain="test.martialcomp.com",
            owner=self.owner,
            is_active=True
        )
        
        # Mock cursor
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test schema creation
        create_schema_for_tenant(tenant)
        
        # Verify SQL execution
        expected_calls = [
            'CREATE SCHEMA IF NOT EXISTS "tenant_test"',
            'GRANT ALL ON SCHEMA "tenant_test" TO'
        ]
        
        executed_sql = ' '.join(call[0][0] for call in mock_cursor.execute.call_args_list)
        for expected in expected_calls:
            self.assertIn(expected, executed_sql)
    
    def test_subscription_lifecycle(self):
        """Test subscription plan changes"""
        tenant = Tenant.objects.create(
            name="Test Club",
            slug="test",
            schema_name="tenant_test",
            domain="test.martialcomp.com",
            owner=self.owner,
            continent="europe_west",
            subscription_plan="essentials",
            is_active=True,
            is_trial=True
        )
        
        # Test trial status
        self.assertTrue(tenant.is_trial)
        self.assertEqual(tenant.subscription_plan, "essentials")
        
        # Upgrade to masters
        tenant.subscription_plan = "masters"
        tenant.is_trial = False
        tenant.save()
        
        # Test new pricing
        self.assertEqual(tenant.get_price_for_plan(), 19.99)
        
        # Test new features
        features = tenant.get_available_features()
        self.assertEqual(features['max_members'], 300)
        self.assertTrue(features['competitions'])
    
    def test_regional_pricing(self):
        """Test pricing variations by continent"""
        continents_and_prices = [
            ('africa', 'essentials', 2.99),
            ('asia_southeast', 'masters', 9.99),
            ('europe_west', 'champion', 29.99),
            ('north_america', 'essentials', 9.99),
            ('south_america', 'masters', 11.99),
        ]
        
        for continent, plan, expected_price in continents_and_prices:
            tenant = Tenant(
                continent=continent,
                subscription_plan=plan
            )
            
            price = tenant.get_price_for_plan()
            self.assertEqual(
                price, 
                expected_price,
                f"Wrong price for {continent}/{plan}: got {price}, expected {expected_price}"
            )


class TenantMiddlewareTest(TestCase):
    """Test tenant middleware functionality"""
    
    def setUp(self):
        self.middleware = TenantMiddleware(get_response=lambda r: None)
        
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name="Test Club",
            slug="test-club",
            schema_name="tenant_test_club",
            domain="test-club.martialcomp.com",
            is_active=True
        )
        
        # Create domain
        Domain.objects.create(
            tenant=self.tenant,
            domain="test-club.martialcomp.com",
            is_primary=True
        )
    
    def test_tenant_identification_by_subdomain(self):
        """Test tenant identification from subdomain"""
        # Mock request
        request = MagicMock()
        request.get_host.return_value = "test-club.martialcomp.com"
        
        # Process request
        self.middleware.process_request(request)
        
        # Verify tenant was set
        self.assertEqual(request.tenant, self.tenant)
    
    def test_tenant_identification_by_custom_domain(self):
        """Test tenant identification from custom domain"""
        # Add custom domain
        Domain.objects.create(
            tenant=self.tenant,
            domain="customclub.com",
            is_primary=False
        )
        
        # Mock request
        request = MagicMock()
        request.get_host.return_value = "customclub.com"
        
        # Process request
        self.middleware.process_request(request)
        
        # Verify tenant was set
        self.assertEqual(request.tenant, self.tenant)
    
    @override_settings(PUBLIC_DOMAINS=['martialcomp.com', 'www.martialcomp.com'])
    def test_public_domain_access(self):
        """Test access to public domains"""
        # Mock request to public domain
        request = MagicMock()
        request.get_host.return_value = "www.martialcomp.com"
        
        # Process request
        self.middleware.process_request(request)
        
        # Verify no tenant was set
        self.assertIsNone(request.tenant)
    
    def test_inactive_tenant_rejection(self):
        """Test that inactive tenants are rejected"""
        # Deactivate tenant
        self.tenant.is_active = False
        self.tenant.save()
        
        # Mock request
        request = MagicMock()
        request.get_host.return_value = "test-club.martialcomp.com"
        
        # Process request should raise exception
        from django.core.exceptions import DisallowedHost
        with self.assertRaises(DisallowedHost):
            self.middleware.process_request(request)
    
    def test_schema_switching(self):
        """Test schema switching for tenant"""
        with patch('multitenant.middleware.connection') as mock_connection:
            # Mock request
            request = MagicMock()
            request.get_host.return_value = "test-club.martialcomp.com"
            
            # Process request
            self.middleware.process_request(request)
            
            # Verify schema was set
            mock_connection.set_schema.assert_called_with('tenant_test_club')
    
    def test_cleanup_after_request(self):
        """Test cleanup after request processing"""
        with patch('multitenant.middleware.connection') as mock_connection:
            # Mock request and response
            request = MagicMock()
            response = MagicMock()
            
            # Process response
            self.middleware.process_response(request, response)
            
            # Verify schema was reset to public
            mock_connection.set_schema.assert_called_with('public')


class SchemaContextTest(TestCase):
    """Test schema context manager"""
    
    def test_schema_context_switching(self):
        """Test schema context manager switches schemas correctly"""
        with patch('multitenant.utils.connection') as mock_connection:
            # Mock current schema
            mock_connection.schema_name = 'public'
            
            # Use context manager
            with SchemaContext('tenant_test'):
                # Verify schema was switched
                mock_connection.set_schema.assert_called_with('tenant_test')
            
            # Verify schema was restored
            mock_connection.set_schema.assert_called_with('public')
    
    def test_nested_schema_contexts(self):
        """Test nested schema contexts"""
        with patch('multitenant.utils.connection') as mock_connection:
            # Mock current schema
            mock_connection.schema_name = 'public'
            
            # Nested contexts
            with SchemaContext('tenant_1'):
                mock_connection.schema_name = 'tenant_1'
                
                with SchemaContext('tenant_2'):
                    mock_connection.schema_name = 'tenant_2'
                    # Should be in tenant_2
                    mock_connection.set_schema.assert_called_with('tenant_2')
                
                # Should restore to tenant_1
                mock_connection.set_schema.assert_called_with('tenant_1')
            
            # Should restore to public
            mock_connection.set_schema.assert_called_with('public')