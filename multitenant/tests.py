"""
Unit tests for multi-tenant functionality
"""
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Tenant, Domain, TenantFeature
from .utils import validate_schema_name, create_schema_for_tenant


class TenantModelTest(TestCase):
    """Test the Tenant model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Club",
            slug="test-club",
            schema_name="tenant_test_club",
            domain="test-club.martialcomp.com",
            continent="europe_west",
            subscription_plan="essentials",
            is_active=True
        )
    
    def test_tenant_creation(self):
        """Test creating a tenant"""
        self.assertEqual(self.tenant.name, "Test Club")
        self.assertEqual(self.tenant.slug, "test-club")
        self.assertEqual(self.tenant.schema_name, "tenant_test_club")
        self.assertTrue(self.tenant.is_active)
    
    def test_pricing_calculation(self):
        """Test pricing calculation for different plans and continents"""
        # Europe West pricing
        self.tenant.subscription_plan = 'essentials'
        self.assertEqual(self.tenant.get_price_for_plan(), 9.99)
        
        self.tenant.subscription_plan = 'masters'
        self.assertEqual(self.tenant.get_price_for_plan(), 19.99)
        
        self.tenant.subscription_plan = 'champion'
        self.assertEqual(self.tenant.get_price_for_plan(), 29.99)
        
        # Africa pricing
        self.tenant.continent = 'africa'
        self.tenant.subscription_plan = 'essentials'
        self.assertEqual(self.tenant.get_price_for_plan(), 2.99)
    
    def test_features_matrix(self):
        """Test features availability for different plans"""
        # Essentials features
        self.tenant.subscription_plan = 'essentials'
        features = self.tenant.get_available_features()
        self.assertEqual(features['max_members'], 100)
        self.assertEqual(features['max_disciplines'], 2)
        self.assertFalse(features['competitions'])
        
        # Masters features
        self.tenant.subscription_plan = 'masters'
        features = self.tenant.get_available_features()
        self.assertEqual(features['max_members'], 300)
        self.assertEqual(features['max_disciplines'], 5)
        self.assertTrue(features['competitions'])
        
        # Champion features
        self.tenant.subscription_plan = 'champion'
        features = self.tenant.get_available_features()
        self.assertIsNone(features['max_members'])  # Unlimited
        self.assertIsNone(features['max_disciplines'])  # Unlimited
        self.assertTrue(features['competitions'])
        self.assertTrue(features['api_access'])


class DomainModelTest(TestCase):
    """Test the Domain model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Club",
            slug="test-club",
            schema_name="tenant_test_club",
            domain="test-club.martialcomp.com",
            continent="europe_west",
            subscription_plan="essentials",
            is_active=True
        )
    
    def test_domain_creation(self):
        """Test creating domains for a tenant"""
        # Create primary domain
        primary_domain = Domain.objects.create(
            tenant=self.tenant,
            domain="test-club.martialcomp.com",
            is_primary=True
        )
        
        # Create secondary domain
        secondary_domain = Domain.objects.create(
            tenant=self.tenant,
            domain="testclub.com",
            is_primary=False
        )
        
        self.assertEqual(self.tenant.domains.count(), 2)
        self.assertTrue(primary_domain.is_primary)
        self.assertFalse(secondary_domain.is_primary)


class SchemaValidationTest(TestCase):
    """Test schema name validation"""
    
    def test_valid_schema_names(self):
        """Test valid schema names"""
        valid_names = [
            'tenant_club',
            'tenant_123',
            'a',
            'tenant_with_underscores',
            'z' * 63,  # Maximum length
        ]
        
        for name in valid_names:
            try:
                validate_schema_name(name)
            except ValueError:
                self.fail(f"Valid schema name '{name}' was rejected")
    
    def test_invalid_schema_names(self):
        """Test invalid schema names"""
        invalid_names = [
            '',  # Empty
            'Tenant_Upper',  # Uppercase
            '123tenant',  # Starts with number
            'tenant-dashes',  # Contains dashes
            'tenant space',  # Contains space
            'public',  # Reserved word
            'a' * 64,  # Too long
            'SELECT',  # SQL keyword
        ]
        
        for name in invalid_names:
            with self.assertRaises(ValueError):
                validate_schema_name(name)


class TenantFeatureTest(TestCase):
    """Test the TenantFeature model"""
    
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Test Club",
            slug="test-club",
            schema_name="tenant_test_club",
            domain="test-club.martialcomp.com",
            continent="europe_west",
            subscription_plan="essentials",
            is_active=True
        )
    
    def test_feature_creation(self):
        """Test creating custom features for a tenant"""
        feature = TenantFeature.objects.create(
            tenant=self.tenant,
            feature_code='custom_reports',
            is_enabled=True,
            metadata={'report_types': ['financial', 'membership']}
        )
        
        self.assertEqual(feature.feature_code, 'custom_reports')
        self.assertTrue(feature.is_enabled)
        self.assertEqual(feature.metadata['report_types'], ['financial', 'membership'])