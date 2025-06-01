"""
Integration tests for multi-tenant functionality
"""
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.test.utils import override_settings

from ..models import Tenant, Domain
from ..forms import TenantOnboardingForm


@override_settings(
    ALLOWED_HOSTS=['*'],
    PUBLIC_DOMAINS=['martialcomp.com', 'localhost'],
    TENANT_BASE_DOMAINS=['martialcomp.com']
)
class TenantOnboardingIntegrationTest(TransactionTestCase):
    """Test the complete onboarding flow"""
    
    def setUp(self):
        self.client = Client()
    
    def test_onboarding_form_display(self):
        """Test that onboarding form displays correctly"""
        response = self.client.get(reverse('multitenant:tenant_onboarding'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bienvenue sur MartialComp')
        self.assertContains(response, 'name="owner_email"')
        self.assertContains(response, 'name="subdomain"')
    
    def test_successful_onboarding(self):
        """Test successful tenant creation through onboarding"""
        form_data = {
            'owner_email': 'newclub@example.com',
            'owner_first_name': 'John',
            'owner_last_name': 'Doe',
            'owner_password': 'securepass123',
            'owner_password_confirm': 'securepass123',
            'name': 'New Martial Arts Club',
            'subdomain': 'new-club',
            'continent': 'europe_west',
            'country': 'FR',
            'language': 'fr',
            'subscription_plan': 'essentials',
            'currency': 'EUR',
            'timezone': 'Europe/Paris',
            'accept_terms': True,
        }
        
        response = self.client.post(
            reverse('multitenant:tenant_onboarding'),
            data=form_data,
            follow=False
        )
        
        # Should redirect to tenant domain
        self.assertEqual(response.status_code, 302)
        
        # Verify tenant was created
        tenant = Tenant.objects.get(slug='new-club')
        self.assertEqual(tenant.name, 'New Martial Arts Club')
        self.assertEqual(tenant.domain, 'new-club.martialcomp.com')
        self.assertEqual(tenant.continent, 'europe_west')
        
        # Verify owner was created
        owner = User.objects.get(email='newclub@example.com')
        self.assertEqual(owner.first_name, 'John')
        self.assertEqual(owner.last_name, 'Doe')
        self.assertEqual(tenant.owner, owner)
        
        # Verify domain was created
        domain = Domain.objects.get(tenant=tenant, is_primary=True)
        self.assertEqual(domain.domain, 'new-club.martialcomp.com')
    
    def test_duplicate_subdomain_rejection(self):
        """Test that duplicate subdomains are rejected"""
        # Create existing tenant
        existing_tenant = Tenant.objects.create(
            name="Existing Club",
            slug="existing-club",
            schema_name="tenant_existing_club",
            domain="existing-club.martialcomp.com",
            is_active=True
        )
        
        form_data = {
            'owner_email': 'another@example.com',
            'owner_first_name': 'Jane',
            'owner_last_name': 'Smith',
            'owner_password': 'password123',
            'owner_password_confirm': 'password123',
            'name': 'Another Club',
            'subdomain': 'existing-club',  # Duplicate!
            'continent': 'europe_west',
            'country': 'FR',
            'language': 'fr',
            'subscription_plan': 'essentials',
            'currency': 'EUR',
            'timezone': 'Europe/Paris',
            'accept_terms': True,
        }
        
        response = self.client.post(
            reverse('multitenant:tenant_onboarding'),
            data=form_data
        )
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ce sous-domaine est déjà utilisé')
    
    def test_reserved_subdomain_rejection(self):
        """Test that reserved subdomains are rejected"""
        form_data = {
            'owner_email': 'admin@example.com',
            'owner_first_name': 'Admin',
            'owner_last_name': 'User',
            'owner_password': 'password123',
            'owner_password_confirm': 'password123',
            'name': 'Admin Club',
            'subdomain': 'admin',  # Reserved!
            'continent': 'europe_west',
            'country': 'FR',
            'language': 'fr',
            'subscription_plan': 'essentials',
            'currency': 'EUR',
            'timezone': 'Europe/Paris',
            'accept_terms': True,
        }
        
        response = self.client.post(
            reverse('multitenant:tenant_onboarding'),
            data=form_data
        )
        
        # Should not redirect (form has errors)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ce sous-domaine est réservé')


@override_settings(
    ALLOWED_HOSTS=['*'],
    PUBLIC_DOMAINS=['martialcomp.com'],
    TENANT_BASE_DOMAINS=['martialcomp.com']
)
class TenantAccessIntegrationTest(TestCase):
    """Test tenant access and isolation"""
    
    def setUp(self):
        # Create test tenants
        self.owner1 = User.objects.create_user(
            username='owner1@test.com',
            email='owner1@test.com',
            password='testpass123'
        )
        
        self.tenant1 = Tenant.objects.create(
            name="Club One",
            slug="club-one",
            schema_name="tenant_club_one",
            domain="club-one.martialcomp.com",
            owner=self.owner1,
            is_active=True
        )
        
        Domain.objects.create(
            tenant=self.tenant1,
            domain="club-one.martialcomp.com",
            is_primary=True
        )
        
        self.owner2 = User.objects.create_user(
            username='owner2@test.com',
            email='owner2@test.com',
            password='testpass123'
        )
        
        self.tenant2 = Tenant.objects.create(
            name="Club Two",
            slug="club-two",
            schema_name="tenant_club_two",
            domain="club-two.martialcomp.com",
            owner=self.owner2,
            is_active=True
        )
        
        Domain.objects.create(
            tenant=self.tenant2,
            domain="club-two.martialcomp.com",
            is_primary=True
        )
        
        self.client = Client()
    
    def test_tenant_info_api(self):
        """Test tenant info API endpoint"""
        # Request for tenant1
        response = self.client.get(
            reverse('multitenant:tenant_info'),
            HTTP_HOST='club-one.martialcomp.com'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['tenant']['name'], 'Club One')
        self.assertEqual(data['tenant']['domain'], 'club-one.martialcomp.com')
        
        # Request for tenant2
        response = self.client.get(
            reverse('multitenant:tenant_info'),
            HTTP_HOST='club-two.martialcomp.com'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['tenant']['name'], 'Club Two')
    
    def test_tenant_dashboard_access(self):
        """Test tenant dashboard access control"""
        # Login as owner1
        self.client.login(username='owner1@test.com', password='testpass123')
        
        # Access tenant1 dashboard
        response = self.client.get(
            reverse('multitenant:tenant_dashboard'),
            HTTP_HOST='club-one.martialcomp.com'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Club One')
        
        # Try to access tenant2 dashboard (should fail)
        response = self.client.get(
            reverse('multitenant:tenant_dashboard'),
            HTTP_HOST='club-two.martialcomp.com',
            follow=False
        )
        
        # Should redirect to login or show error
        self.assertIn(response.status_code, [302, 403])
    
    def test_tenant_settings_owner_only(self):
        """Test that only owner can access tenant settings"""
        # Create regular user for tenant1
        regular_user = User.objects.create_user(
            username='regular@test.com',
            email='regular@test.com',
            password='testpass123'
        )
        
        # Login as regular user
        self.client.login(username='regular@test.com', password='testpass123')
        
        # Try to access settings
        response = self.client.get(
            reverse('multitenant:tenant_settings'),
            HTTP_HOST='club-one.martialcomp.com'
        )
        
        # Should be redirected or forbidden
        self.assertIn(response.status_code, [302, 403])
        
        # Login as owner
        self.client.login(username='owner1@test.com', password='testpass123')
        
        # Access settings
        response = self.client.get(
            reverse('multitenant:tenant_settings'),
            HTTP_HOST='club-one.martialcomp.com'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paramètres de l\'organisation')
    
    def test_billing_page_access(self):
        """Test billing page access control"""
        # Login as owner
        self.client.login(username='owner1@test.com', password='testpass123')
        
        # Access billing page
        response = self.client.get(
            reverse('multitenant:tenant_billing'),
            HTTP_HOST='club-one.martialcomp.com'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Facturation et abonnement')
        self.assertContains(response, 'Plan actuel')


class TenantFormValidationTest(TestCase):
    """Test form validations"""
    
    def test_onboarding_form_validation(self):
        """Test onboarding form validation"""
        # Test password mismatch
        form_data = {
            'owner_email': 'test@example.com',
            'owner_first_name': 'Test',
            'owner_last_name': 'User',
            'owner_password': 'password123',
            'owner_password_confirm': 'differentpassword',  # Mismatch!
            'name': 'Test Club',
            'subdomain': 'test-club',
            'continent': 'europe_west',
            'country': 'FR',
            'language': 'fr',
            'subscription_plan': 'essentials',
            'currency': 'EUR',
            'timezone': 'Europe/Paris',
            'accept_terms': True,
        }
        
        form = TenantOnboardingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Les mots de passe ne correspondent pas', form.errors['__all__'])
        
        # Test duplicate email
        existing_user = User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='password123'
        )
        
        form_data['owner_email'] = 'existing@example.com'
        form_data['owner_password_confirm'] = 'password123'
        
        form = TenantOnboardingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('owner_email', form.errors)
        
        # Test terms not accepted
        form_data['owner_email'] = 'new@example.com'
        form_data['accept_terms'] = False
        
        form = TenantOnboardingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('accept_terms', form.errors)
    
    def test_settings_form_validation(self):
        """Test settings form validation"""
        from ..forms import TenantSettingsForm
        
        tenant = Tenant.objects.create(
            name="Test Club",
            slug="test",
            schema_name="tenant_test",
            domain="test.martialcomp.com",
            is_active=True
        )
        
        # Test valid form
        form_data = {
            'name': 'Updated Club Name',
            'country': 'UK',
            'language': 'en',
            'currency': 'GBP',
            'timezone': 'Europe/London',
            'primary_color': '#ff0000',
            'secondary_color': '#00ff00',
        }
        
        form = TenantSettingsForm(data=form_data, instance=tenant)
        self.assertTrue(form.is_valid())
        
        # Test invalid color format
        form_data['primary_color'] = 'not-a-color'
        
        form = TenantSettingsForm(data=form_data, instance=tenant)
        self.assertFalse(form.is_valid())
        self.assertIn('primary_color', form.errors)