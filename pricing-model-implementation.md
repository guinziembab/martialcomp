# Pricing Model Implementation

## Overview

This document outlines the implementation details of the pricing model for MartialComp application, covering both backend and frontend components. The pricing model is designed to be flexible, supporting various subscription tiers, pay-per-use features, and special pricing for different user categories.

## Backend Implementation

### Database Models

```python
# multitenant/models.py

class SubscriptionTier(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_annually = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.PositiveIntegerField()
    max_competitions = models.PositiveIntegerField()
    max_storage_gb = models.PositiveIntegerField()
    features = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TenantSubscription(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('annually', 'Annually'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('canceled', 'Canceled'),
        ('trialing', 'Trialing'),
    ]
    
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PayPerUseFeature(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    unit_label = models.CharField(max_length=50)  # e.g., "per participant", "per GB"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class FeatureUsage(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    feature = models.ForeignKey(PayPerUseFeature, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    usage_date = models.DateTimeField()
    billed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class PromotionCode(models.Model):
    TYPE_CHOICES = [
        ('percentage', 'Percentage Discount'),
        ('fixed', 'Fixed Amount Discount'),
        ('free_months', 'Free Months'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    discount_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    current_uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Payment Integration

```python
# multitenant/payments/service.py

class PaymentService:
    def __init__(self, tenant):
        self.tenant = tenant
        self.provider = self._get_payment_provider()
    
    def _get_payment_provider(self):
        # Select payment provider based on tenant's region or preferences
        region = self.tenant.country
        if region in ['US', 'CA', 'MX']:
            return StripePaymentProvider(self.tenant)
        elif region in ['FR', 'DE', 'ES', 'IT']:
            return EuropeanPaymentProvider(self.tenant)
        else:
            return DefaultPaymentProvider(self.tenant)
    
    def create_subscription(self, tier_id, billing_cycle):
        tier = SubscriptionTier.objects.get(id=tier_id)
        price = tier.price_annually if billing_cycle == 'annually' else tier.price_monthly
        
        # Create subscription in payment provider
        payment_provider_subscription_id = self.provider.create_subscription(tier, billing_cycle, price)
        
        # Create subscription record in our database
        subscription = TenantSubscription.objects.create(
            tenant=self.tenant,
            tier=tier,
            billing_cycle=billing_cycle,
            start_date=timezone.now(),
            end_date=self._calculate_end_date(billing_cycle),
            payment_provider_subscription_id=payment_provider_subscription_id
        )
        
        return subscription
    
    def process_pay_per_use_charges(self, billing_cycle_end_date):
        # Get all unbilled feature usage for this tenant
        unbilled_usage = FeatureUsage.objects.filter(
            tenant=self.tenant,
            billed=False,
            usage_date__lt=billing_cycle_end_date
        )
        
        total_charge = 0
        usage_details = []
        
        # Calculate charges
        for usage in unbilled_usage:
            feature = usage.feature
            charge = usage.quantity * feature.price_per_unit
            total_charge += charge
            usage_details.append({
                'feature_name': feature.name,
                'quantity': usage.quantity,
                'unit_price': feature.price_per_unit,
                'total': charge
            })
            
            # Mark as billed
            usage.billed = True
            usage.save()
        
        # Process payment with the provider
        if total_charge > 0:
            invoice_id = self.provider.create_invoice(total_charge, usage_details)
            return {
                'success': True,
                'total_charge': total_charge,
                'invoice_id': invoice_id,
                'details': usage_details
            }
        
        return {
            'success': True,
            'total_charge': 0,
            'details': []
        }
    
    def _calculate_end_date(self, billing_cycle):
        if billing_cycle == 'annually':
            return timezone.now() + timezone.timedelta(days=365)
        else:  # monthly
            return timezone.now() + timezone.timedelta(days=30)
```

### API Endpoints

```python
# multitenant/views/subscription_views.py

class SubscriptionTierViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionTier.objects.filter(is_active=True)
    serializer_class = SubscriptionTierSerializer
    permission_classes = [IsAuthenticated]

class TenantSubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSubscriptionSerializer
    permission_classes = [IsAuthenticated, IsTenantOwner]
    
    def get_queryset(self):
        return TenantSubscription.objects.filter(tenant__owner=self.request.user)
    
    @action(detail=False, methods=['post'])
    def create_subscription(self, request):
        tier_id = request.data.get('tier_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not tier_id:
            return Response({'error': 'tier_id is required'}, status=400)
        
        try:
            # Get tenant from the authenticated user
            tenant = Tenant.objects.get(owner=request.user)
            
            # Initialize payment service
            payment_service = PaymentService(tenant)
            
            # Create subscription
            subscription = payment_service.create_subscription(tier_id, billing_cycle)
            
            return Response(TenantSubscriptionSerializer(subscription).data, status=201)
        except SubscriptionTier.DoesNotExist:
            return Response({'error': 'Invalid tier_id'}, status=400)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    @action(detail=True, methods=['post'])
    def cancel_subscription(self, request, pk=None):
        subscription = self.get_object()
        
        # Initialize payment service
        payment_service = PaymentService(subscription.tenant)
        
        # Cancel subscription
        result = payment_service.cancel_subscription(subscription.id)
        
        if result['success']:
            subscription.status = 'canceled'
            subscription.auto_renew = False
            subscription.save()
            return Response({'status': 'Subscription canceled'})
        else:
            return Response({'error': result['error']}, status=400)

class PromotionCodeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        code = request.data.get('code')
        
        if not code:
            return Response({'error': 'Promotion code is required'}, status=400)
        
        try:
            promotion = PromotionCode.objects.get(
                code=code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now()
            )
            
            # Check if max uses is reached
            if promotion.max_uses and promotion.current_uses >= promotion.max_uses:
                return Response({'valid': False, 'reason': 'This code has reached its maximum number of uses'})
            
            return Response({
                'valid': True,
                'discount_type': promotion.discount_type,
                'discount_value': promotion.discount_value,
                'description': promotion.description
            })
        except PromotionCode.DoesNotExist:
            return Response({'valid': False, 'reason': 'Invalid or expired promotion code'})
```

### Access Control & Feature Availability

```python
# multitenant/utils.py

def check_feature_availability(tenant, feature_key):
    """
    Check if a specific feature is available for a tenant based on their subscription tier.
    
    Args:
        tenant: The tenant object
        feature_key: String identifier for the feature
        
    Returns:
        tuple: (is_available, reason)
    """
    try:
        # Get active subscription
        subscription = TenantSubscription.objects.get(
            tenant=tenant,
            status='active',
            end_date__gte=timezone.now()
        )
        
        # Check if feature is included in subscription tier
        tier_features = subscription.tier.features
        if feature_key in tier_features and tier_features[feature_key]:
            return True, None
        
        # If not included in subscription, check if it's a pay-per-use feature
        try:
            PayPerUseFeature.objects.get(name=feature_key, is_active=True)
            return True, "pay_per_use"
        except PayPerUseFeature.DoesNotExist:
            return False, "Feature not available in your current plan"
            
    except TenantSubscription.DoesNotExist:
        return False, "No active subscription"

def record_feature_usage(tenant, feature_key, quantity=1):
    """
    Record usage of a pay-per-use feature.
    
    Args:
        tenant: The tenant object
        feature_key: String identifier for the feature
        quantity: Amount of usage to record
        
    Returns:
        bool: Success status
    """
    try:
        feature = PayPerUseFeature.objects.get(name=feature_key, is_active=True)
        
        # Record usage
        FeatureUsage.objects.create(
            tenant=tenant,
            feature=feature,
            quantity=quantity,
            usage_date=timezone.now()
        )
        
        return True
    except PayPerUseFeature.DoesNotExist:
        return False
```

### Middleware for Feature Access Control

```python
# multitenant/middleware.py

class FeatureAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns that require specific features
        # Format: (url_regex, feature_key)
        self.feature_patterns = [
            (r'^/api/v1/advanced-analytics/', 'advanced_analytics'),
            (r'^/api/v1/bulk-operations/', 'bulk_operations'),
            (r'^/api/v1/exports/', 'data_export'),
            (r'^/combats/realtime-scoring/', 'realtime_scoring'),
            # Add more feature-specific URL patterns
        ]
        
    def __call__(self, request):
        # Skip middleware for authentication and public pages
        if request.path.startswith('/api/v1/auth/') or request.path.startswith('/public/'):
            return self.get_response(request)
        
        # Get tenant from request (assuming it's set by another middleware)
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            return self.get_response(request)
        
        # Check if the requested URL requires a specific feature
        for pattern, feature_key in self.feature_patterns:
            if re.match(pattern, request.path):
                is_available, reason = check_feature_availability(tenant, feature_key)
                
                if not is_available:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'error': 'Feature not available',
                            'reason': reason,
                            'upgrade_url': '/subscriptions/upgrade/'
                        }, status=403)
                    else:
                        # Redirect to upgrade page for browser requests
                        return redirect('/subscriptions/upgrade/?feature=' + feature_key)
                
                # If it's a pay-per-use feature, record usage
                if reason == "pay_per_use":
                    record_feature_usage(tenant, feature_key)
                
                break
        
        return self.get_response(request)
```

## Frontend Implementation

### Subscription Management Component

```jsx
// frontend/src/components/SubscriptionManagement.jsx

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { fetchSubscriptionTiers, getCurrentSubscription, upgradeSubscription } from '../api/subscription';

const SubscriptionManagement = () => {
  const { t } = useTranslation();
  const [tiers, setTiers] = useState([]);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [selectedTier, setSelectedTier] = useState(null);
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadData = async () => {
      try {
        const [tiersData, subscriptionData] = await Promise.all([
          fetchSubscriptionTiers(),
          getCurrentSubscription()
        ]);
        
        setTiers(tiersData);
        setCurrentSubscription(subscriptionData);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    loadData();
  }, []);
  
  const handleTierSelect = (tierId) => {
    setSelectedTier(tierId);
  };
  
  const handleBillingCycleChange = (cycle) => {
    setBillingCycle(cycle);
  };
  
  const handleUpgradeSubscription = async () => {
    if (!selectedTier) return;
    
    try {
      setLoading(true);
      const result = await upgradeSubscription(selectedTier, billingCycle);
      setCurrentSubscription(result);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };
  
  if (loading) {
    return <div className="loading">{t('common.loading')}</div>;
  }
  
  if (error) {
    return <div className="error">{t('errors.loadingFailed')}: {error}</div>;
  }
  
  return (
    <div className="subscription-management">
      <h2>{t('subscription.title')}</h2>
      
      {currentSubscription && (
        <div className="current-plan">
          <h3>{t('subscription.currentPlan')}</h3>
          <div className="plan-details">
            <p><strong>{t('subscription.tier')}:</strong> {currentSubscription.tier.name}</p>
            <p><strong>{t('subscription.billingCycle')}:</strong> {t(`subscription.${currentSubscription.billing_cycle}`)}</p>
            <p><strong>{t('subscription.status')}:</strong> {t(`subscription.status.${currentSubscription.status}`)}</p>
            <p><strong>{t('subscription.renewalDate')}:</strong> {new Date(currentSubscription.end_date).toLocaleDateString()}</p>
          </div>
        </div>
      )}
      
      <div className="available-plans">
        <h3>{t('subscription.availablePlans')}</h3>
        
        <div className="billing-toggle">
          <span 
            className={billingCycle === 'monthly' ? 'active' : ''}
            onClick={() => handleBillingCycleChange('monthly')}
          >
            {t('subscription.monthly')}
          </span>
          <span 
            className={billingCycle === 'annually' ? 'active' : ''}
            onClick={() => handleBillingCycleChange('annually')}
          >
            {t('subscription.annually')} 
            <span className="savings-badge">{t('subscription.save')} 20%</span>
          </span>
        </div>
        
        <div className="plans-grid">
          {tiers.map(tier => (
            <div 
              key={tier.id} 
              className={`plan-card ${selectedTier === tier.id ? 'selected' : ''} ${currentSubscription && currentSubscription.tier.id === tier.id ? 'current' : ''}`}
              onClick={() => handleTierSelect(tier.id)}
            >
              <h4>{tier.name}</h4>
              <div className="price">
                {billingCycle === 'monthly' ? (
                  <>
                    <span className="amount">${tier.price_monthly}</span>
                    <span className="period">/ {t('subscription.month')}</span>
                  </>
                ) : (
                  <>
                    <span className="amount">${tier.price_annually / 12}</span>
                    <span className="period">/ {t('subscription.month')}</span>
                    <div className="annual-note">${tier.price_annually} {t('subscription.billedAnnually')}</div>
                  </>
                )}
              </div>
              <div className="features">
                <ul>
                  <li>{t('subscription.features.users', { count: tier.max_users })}</li>
                  <li>{t('subscription.features.competitions', { count: tier.max_competitions })}</li>
                  <li>{t('subscription.features.storage', { count: tier.max_storage_gb })}</li>
                  {Object.entries(tier.features).map(([key, enabled]) => (
                    enabled && <li key={key}>{t(`subscription.features.${key}`)}</li>
                  ))}
                </ul>
              </div>
              {currentSubscription && currentSubscription.tier.id === tier.id ? (
                <button className="current-plan-btn" disabled>{t('subscription.currentPlanBtn')}</button>
              ) : (
                <button className="select-plan-btn">{t('subscription.selectPlanBtn')}</button>
              )}
            </div>
          ))}
        </div>
      </div>
      
      {selectedTier && selectedTier !== (currentSubscription?.tier.id || null) && (
        <div className="upgrade-section">
          <button 
            className="upgrade-btn" 
            onClick={handleUpgradeSubscription}
            disabled={loading}
          >
            {t('subscription.upgradeBtn')}
          </button>
        </div>
      )}
      
      <div className="additional-features">
        <h3>{t('subscription.additionalFeatures')}</h3>
        <p>{t('subscription.payPerUseDescription')}</p>
        
        <div className="pay-per-use-features">
          {/* List of pay-per-use features */}
          <div className="feature-item">
            <div className="feature-info">
              <h4>{t('subscription.payPerUse.additionalParticipants')}</h4>
              <p>{t('subscription.payPerUse.additionalParticipantsDesc')}</p>
            </div>
            <div className="feature-pricing">
              $2.50 / {t('subscription.payPerUse.participant')}
            </div>
          </div>
          
          <div className="feature-item">
            <div className="feature-info">
              <h4>{t('subscription.payPerUse.additionalStorage')}</h4>
              <p>{t('subscription.payPerUse.additionalStorageDesc')}</p>
            </div>
            <div className="feature-pricing">
              $5.00 / {t('subscription.payPerUse.gigabyte')}
            </div>
          </div>
          
          <div className="feature-item">
            <div className="feature-info">
              <h4>{t('subscription.payPerUse.premiumSupport')}</h4>
              <p>{t('subscription.payPerUse.premiumSupportDesc')}</p>
            </div>
            <div className="feature-pricing">
              $50.00 / {t('subscription.payPerUse.session')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionManagement;
```

### Feature Gating Component

```jsx
// frontend/src/components/FeatureGate.jsx

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useTenant } from '../contexts/TenantContext';

/**
 * Component that conditionally renders children based on feature availability
 */
const FeatureGate = ({ featureKey, children, fallback }) => {
  const { t } = useTranslation();
  const { checkFeatureAvailability } = useTenant();
  const { isAvailable, reason } = checkFeatureAvailability(featureKey);
  
  if (isAvailable) {
    return <>{children}</>;
  }
  
  if (fallback) {
    return fallback;
  }
  
  return (
    <div className="feature-gate-placeholder">
      <div className="feature-unavailable">
        <h3>{t('features.unavailable.title')}</h3>
        <p>{t('features.unavailable.description', { feature: t(`features.${featureKey}`) })}</p>
        <Link to="/subscription/upgrade" className="upgrade-button">
          {t('features.unavailable.upgradeButton')}
        </Link>
      </div>
    </div>
  );
};

export default FeatureGate;
```

### Usage in Application

```jsx
// frontend/src/pages/AdvancedAnalytics.jsx

import React from 'react';
import { useTranslation } from 'react-i18next';
import FeatureGate from '../components/FeatureGate';
import AnalyticsDashboard from '../components/AnalyticsDashboard';

const AdvancedAnalytics = () => {
  const { t } = useTranslation();
  
  return (
    <div className="page advanced-analytics">
      <h1>{t('analytics.title')}</h1>
      
      <FeatureGate featureKey="advanced_analytics">
        <AnalyticsDashboard />
      </FeatureGate>
    </div>
  );
};

export default AdvancedAnalytics;
```

### Tenant Context for Feature Checking

```jsx
// frontend/src/contexts/TenantContext.jsx

import React, { createContext, useContext, useState, useEffect } from 'react';
import { fetchTenantInfo, checkFeatureAvailability } from '../api/tenant';

const TenantContext = createContext();

export const useTenant = () => useContext(TenantContext);

export const TenantProvider = ({ children }) => {
  const [tenant, setTenant] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const loadTenantInfo = async () => {
      try {
        const data = await fetchTenantInfo();
        setTenant(data.tenant);
        setSubscription(data.subscription);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };
    
    loadTenantInfo();
  }, []);
  
  const checkFeature = async (featureKey) => {
    try {
      const result = await checkFeatureAvailability(featureKey);
      return result;
    } catch (err) {
      console.error('Error checking feature availability:', err);
      return { isAvailable: false, reason: 'Error checking feature' };
    }
  };
  
  return (
    <TenantContext.Provider
      value={{
        tenant,
        subscription,
        loading,
        error,
        checkFeatureAvailability: checkFeature,
      }}
    >
      {children}
    </TenantContext.Provider>
  );
};
```

## Testing

### Backend Tests

```python
# multitenant/tests/test_pricing_model.py

from django.test import TestCase
from django.utils import timezone
from multitenant.models import (
    Tenant, SubscriptionTier, TenantSubscription, 
    PayPerUseFeature, FeatureUsage, PromotionCode
)
from multitenant.utils import check_feature_availability, record_feature_usage
from datetime import timedelta

class PricingModelTests(TestCase):
    def setUp(self):
        # Create test tenant
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            domain="test.example.com",
            owner_id=1
        )
        
        # Create subscription tiers
        self.basic_tier = SubscriptionTier.objects.create(
            name="Basic",
            description="Basic features",
            price_monthly=29.99,
            price_annually=299.99,
            max_users=5,
            max_competitions=10,
            max_storage_gb=10,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": False,
                "advanced_analytics": False
            }
        )
        
        self.pro_tier = SubscriptionTier.objects.create(
            name="Pro",
            description="Professional features",
            price_monthly=99.99,
            price_annually=999.99,
            max_users=50,
            max_competitions=100,
            max_storage_gb=100,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": True,
                "advanced_analytics": True
            }
        )
        
        # Create active subscription
        self.subscription = TenantSubscription.objects.create(
            tenant=self.tenant,
            tier=self.basic_tier,
            billing_cycle="monthly",
            status="active",
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            auto_renew=True
        )
        
        # Create pay-per-use feature
        self.ppu_feature = PayPerUseFeature.objects.create(
            name="additional_participants",
            description="Additional participants beyond the plan limit",
            price_per_unit=2.50,
            unit_label="per participant"
        )
        
        # Create promotion code
        self.promo_code = PromotionCode.objects.create(
            code="WELCOME20",
            description="20% off for new users",
            discount_type="percentage",
            discount_value=20.00,
            valid_from=timezone.now() - timedelta(days=10),
            valid_until=timezone.now() + timedelta(days=20),
            max_uses=100,
            current_uses=0
        )
    
    def test_feature_availability_included_in_plan(self):
        # Test feature included in plan
        is_available, reason = check_feature_availability(self.tenant, "basic_analytics")
        self.assertTrue(is_available)
        self.assertIsNone(reason)
    
    def test_feature_availability_not_included_in_plan(self):
        # Test feature not included in plan
        is_available, reason = check_feature_availability(self.tenant, "advanced_analytics")
        self.assertFalse(is_available)
        self.assertEqual(reason, "Feature not available in your current plan")
    
    def test_feature_availability_pay_per_use(self):
        # Test pay-per-use feature
        is_available, reason = check_feature_availability(self.tenant, "additional_participants")
        self.assertTrue(is_available)
        self.assertEqual(reason, "pay_per_use")
    
    def test_record_feature_usage(self):
        # Test recording feature usage
        success = record_feature_usage(self.tenant, "additional_participants", 5)
        self.assertTrue(success)
        
        # Verify usage was recorded
        usage = FeatureUsage.objects.filter(
            tenant=self.tenant,
            feature=self.ppu_feature,
            quantity=5,
            billed=False
        )
        self.assertEqual(usage.count(), 1)
    
    def test_promotion_code_validation(self):
        # Test valid promotion code
        promo = PromotionCode.objects.get(code="WELCOME20")
        self.assertEqual(promo.discount_type, "percentage")
        self.assertEqual(promo.discount_value, 20.00)
        self.assertTrue(promo.is_active)
        
        # Test using the promotion code
        promo.current_uses += 1
        promo.save()
        self.assertEqual(promo.current_uses, 1)
```

### Frontend Tests

```jsx
// frontend/src/components/__tests__/SubscriptionManagement.test.jsx

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SubscriptionManagement from '../SubscriptionManagement';
import { fetchSubscriptionTiers, getCurrentSubscription } from '../../api/subscription';

// Mock API calls
jest.mock('../../api/subscription', () => ({
  fetchSubscriptionTiers: jest.fn(),
  getCurrentSubscription: jest.fn(),
  upgradeSubscription: jest.fn()
}));

// Mock i18n
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key
  })
}));

describe('SubscriptionManagement', () => {
  const mockTiers = [
    {
      id: 1,
      name: 'Basic',
      price_monthly: 29.99,
      price_annually: 299.99,
      max_users: 5,
      max_competitions: 10,
      max_storage_gb: 10,
      features: {
        basic_analytics: true,
        standard_support: true
      }
    },
    {
      id: 2,
      name: 'Pro',
      price_monthly: 99.99,
      price_annually: 999.99,
      max_users: 50,
      max_competitions: 100,
      max_storage_gb: 100,
      features: {
        basic_analytics: true,
        standard_support: true,
        bulk_operations: true,
        advanced_analytics: true
      }
    }
  ];
  
  const mockSubscription = {
    id: 123,
    tier: mockTiers[0],
    billing_cycle: 'monthly',
    status: 'active',
    start_date: '2023-01-01T00:00:00Z',
    end_date: '2023-02-01T00:00:00Z',
    auto_renew: true
  };
  
  beforeEach(() => {
    fetchSubscriptionTiers.mockResolvedValue(mockTiers);
    getCurrentSubscription.mockResolvedValue(mockSubscription);
  });
  
  afterEach(() => {
    jest.clearAllMocks();
  });
  
  test('renders subscription management component', async () => {
    render(
      <MemoryRouter>
        <SubscriptionManagement />
      </MemoryRouter>
    );
    
    // Initially should show loading
    expect(screen.getByText('common.loading')).toBeInTheDocument();
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('subscription.title')).toBeInTheDocument();
    });
    
    // Should show current plan
    expect(screen.getByText('subscription.currentPlan')).toBeInTheDocument();
    
    // Should show available plans
    expect(screen.getByText('subscription.availablePlans')).toBeInTheDocument();
    
    // Should show both tiers
    expect(screen.getByText('Basic')).toBeInTheDocument();
    expect(screen.getByText('Pro')).toBeInTheDocument();
  });
  
  test('handles billing cycle toggle', async () => {
    render(
      <MemoryRouter>
        <SubscriptionManagement />
      </MemoryRouter>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('subscription.title')).toBeInTheDocument();
    });
    
    // Default should be monthly
    expect(screen.getByText('$29.99')).toBeInTheDocument();
    
    // Click on annually
    fireEvent.click(screen.getByText('subscription.annually'));
    
    // Should show annual price divided by 12
    expect(screen.getByText('$24.99')).toBeInTheDocument();
  });
  
  test('handles tier selection', async () => {
    render(
      <MemoryRouter>
        <SubscriptionManagement />
      </MemoryRouter>
    );
    
    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('subscription.title')).toBeInTheDocument();
    });
    
    // Click on Pro tier
    fireEvent.click(screen.getByText('Pro'));
    
    // Upgrade button should appear
    expect(screen.getByText('subscription.upgradeBtn')).toBeInTheDocument();
  });
});
```

## Deployment Considerations

### Database Migrations

When deploying the pricing model, you'll need to run migrations to create the necessary database tables:

```bash
python manage.py makemigrations multitenant
python manage.py migrate multitenant
```

### Initial Data

Create a data migration or management command to populate initial subscription tiers and pay-per-use features:

```python
# multitenant/management/commands/initialize_pricing_data.py

from django.core.management.base import BaseCommand
from multitenant.models import SubscriptionTier, PayPerUseFeature

class Command(BaseCommand):
    help = 'Initialize pricing data with subscription tiers and pay-per-use features'

    def handle(self, *args, **options):
        # Create subscription tiers
        basic_tier = SubscriptionTier.objects.create(
            name="Basic",
            description="Essential features for small clubs and organizations",
            price_monthly=29.99,
            price_annually=299.99,
            max_users=5,
            max_competitions=10,
            max_storage_gb=10,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": False,
                "advanced_analytics": False,
                "custom_branding": False,
                "api_access": False,
                "realtime_scoring": False
            }
        )
        
        standard_tier = SubscriptionTier.objects.create(
            name="Standard",
            description="Advanced features for growing organizations",
            price_monthly=59.99,
            price_annually=599.99,
            max_users=20,
            max_competitions=50,
            max_storage_gb=50,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": True,
                "advanced_analytics": False,
                "custom_branding": True,
                "api_access": False,
                "realtime_scoring": True
            }
        )
        
        pro_tier = SubscriptionTier.objects.create(
            name="Pro",
            description="Complete solution for professional organizations",
            price_monthly=99.99,
            price_annually=999.99,
            max_users=50,
            max_competitions=100,
            max_storage_gb=100,
            features={
                "basic_analytics": True,
                "standard_support": True,
                "bulk_operations": True,
                "advanced_analytics": True,
                "custom_branding": True,
                "api_access": True,
                "realtime_scoring": True
            }
        )
        
        # Create pay-per-use features
        PayPerUseFeature.objects.create(
            name="additional_participants",
            description="Additional participants beyond the plan limit",
            price_per_unit=2.50,
            unit_label="per participant"
        )
        
        PayPerUseFeature.objects.create(
            name="additional_storage",
            description="Additional storage beyond the plan limit",
            price_per_unit=5.00,
            unit_label="per GB"
        )
        
        PayPerUseFeature.objects.create(
            name="premium_support",
            description="Premium support sessions with a dedicated specialist",
            price_per_unit=50.00,
            unit_label="per session"
        )
        
        self.stdout.write(self.style.SUCCESS('Successfully initialized pricing data'))
```

### Configuration

Update your settings to include the new middleware:

```python
# settings.py

MIDDLEWARE = [
    # ... other middleware
    'multitenant.middleware.FeatureAccessMiddleware',
    # ... other middleware
]
```

## Future Enhancements

1. **Usage Analytics Dashboard**:
   - Implement a dashboard for tenants to view their feature usage and associated costs
   - Provide usage forecasts and recommendations for plan upgrades

2. **Granular Feature Controls**:
   - Implement a more detailed feature permission system
   - Allow customizing feature access per user role within a tenant

3. **Dynamic Pricing**:
   - Add support for regional pricing variations
   - Implement time-limited promotional pricing

4. **Subscription Management Automation**:
   - Automated emails for subscription renewals, upgrades, and expirations
   - Grace periods for payment failures
   - Automated downgrade workflows

5. **Integration with Finance Module**:
   - Connect with the finance module for comprehensive financial reporting
   - Automated invoice generation and tax calculations