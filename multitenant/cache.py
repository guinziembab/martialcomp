"""
Multi-tenant caching utilities and middleware.
"""
import hashlib
from typing import Any, Optional, Union
from django.core.cache import caches
from django.conf import settings
import redis
from django.utils.functional import LazyObject
from .models import Tenant


class TenantCacheKeyPrefix:
    """
    Cache key prefix generator for tenant isolation.
    """
    def __init__(self, tenant: Optional[Tenant] = None):
        self.tenant = tenant
    
    def generate_key(self, original_key: str) -> str:
        """
        Generate a tenant-specific cache key.
        """
        if not self.tenant:
            # For public/shared cache
            return f"public:{original_key}"
        
        # Create tenant-specific key
        return f"tenant:{self.tenant.schema_name}:{original_key}"
    
    def parse_key(self, cache_key: str) -> tuple[str, str]:
        """
        Parse a cache key to extract tenant and original key.
        """
        parts = cache_key.split(':', 2)
        if len(parts) < 3:
            return 'public', cache_key
        
        return parts[1], parts[2]


class TenantCache:
    """
    Tenant-aware cache backend wrapper.
    """
    def __init__(self, backend_name: str = 'default'):
        self.backend = caches[backend_name]
        self.key_prefix = TenantCacheKeyPrefix()
    
    def set_tenant(self, tenant: Optional[Tenant]):
        """
        Set the current tenant for cache operations.
        """
        self.key_prefix.tenant = tenant
    
    def get(self, key: str, default=None) -> Any:
        """
        Get value from cache with tenant isolation.
        """
        tenant_key = self.key_prefix.generate_key(key)
        return self.backend.get(tenant_key, default)
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None):
        """
        Set value in cache with tenant isolation.
        """
        tenant_key = self.key_prefix.generate_key(key)
        return self.backend.set(tenant_key, value, timeout)
    
    def delete(self, key: str):
        """
        Delete key from cache.
        """
        tenant_key = self.key_prefix.generate_key(key)
        return self.backend.delete(tenant_key)
    
    def clear_tenant_cache(self, tenant: Tenant):
        """
        Clear all cache entries for a specific tenant.
        """
        # This method depends on the cache backend
        # For Redis, we can use pattern matching
        if hasattr(self.backend, '_cache'):
            cache_client = self.backend._cache
            if isinstance(cache_client, redis.Redis):
                pattern = f"tenant:{tenant.schema_name}:*"
                keys = cache_client.keys(pattern)
                if keys:
                    cache_client.delete(*keys)
    
    def get_or_set(self, key: str, callable_or_value: Any, timeout: Optional[int] = None) -> Any:
        """
        Get value from cache or set it if missing.
        """
        value = self.get(key)
        if value is None:
            if callable(callable_or_value):
                value = callable_or_value()
            else:
                value = callable_or_value
            self.set(key, value, timeout)
        return value
    
    def increment(self, key: str, delta: int = 1) -> int:
        """
        Increment a numeric value in cache.
        """
        tenant_key = self.key_prefix.generate_key(key)
        try:
            return self.backend.incr(tenant_key, delta)
        except ValueError:
            # Key doesn't exist or isn't numeric
            self.set(key, delta)
            return delta
    
    def decrement(self, key: str, delta: int = 1) -> int:
        """
        Decrement a numeric value in cache.
        """
        tenant_key = self.key_prefix.generate_key(key)
        try:
            return self.backend.decr(tenant_key, delta)
        except ValueError:
            # Key doesn't exist or isn't numeric
            self.set(key, -delta)
            return -delta


class GlobalTenantCache(LazyObject):
    """
    Global tenant cache instance.
    """
    def _setup(self):
        self._wrapped = TenantCache()


# Global cache instance
tenant_cache = GlobalTenantCache()


class CacheManager:
    """
    Manager for tenant-specific cache operations.
    """
    @staticmethod
    def cache_tenant_settings(tenant: Tenant, timeout: int = 3600):
        """
        Cache tenant settings and configuration.
        """
        cache = TenantCache()
        cache.set_tenant(tenant)
        
        # Cache tenant features
        features = {
            feature.feature_code: feature.is_enabled
            for feature in tenant.features.all()
        }
        cache.set('features', features, timeout)
        
        # Cache regional settings
        regional_data = {
            'continent': tenant.continent,
            'currency': tenant.get_currency(),
            'payment_provider': tenant.get_payment_provider(),
            'timezone': tenant.get_timezone(),
        }
        cache.set('regional_settings', regional_data, timeout)
        
        # Cache subscription data
        subscription_data = {
            'plan': tenant.subscription_plan,
            'payment_frequency': tenant.payment_frequency,
            'status': tenant.subscription_status,
            'trial_ends_at': tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None,
            'current_period_end': tenant.current_period_end.isoformat() if tenant.current_period_end else None,
        }
        cache.set('subscription', subscription_data, timeout)
    
    @staticmethod
    def cache_club_metadata(tenant: Tenant, timeout: int = 3600):
        """
        Cache club-specific metadata.
        """
        cache = TenantCache()
        cache.set_tenant(tenant)
        
        # Cache club statistics
        from competitions.models import Competition, Practitioner
        stats = {
            'total_practitioners': Practitioner.objects.filter(
                club__federations__tenants=tenant
            ).count(),
            'active_competitions': Competition.objects.filter(
                tenants=tenant,
                status='active'
            ).count(),
            'total_competitions': Competition.objects.filter(
                tenants=tenant
            ).count(),
        }
        cache.set('club_stats', stats, timeout)
    
    @staticmethod
    def invalidate_tenant_cache(tenant: Tenant):
        """
        Invalidate all cache entries for a tenant.
        """
        cache = TenantCache()
        cache.clear_tenant_cache(tenant)
    
    @staticmethod
    def warm_cache(tenant: Tenant):
        """
        Pre-populate cache with frequently used data.
        """
        CacheManager.cache_tenant_settings(tenant)
        CacheManager.cache_club_metadata(tenant)


# Cache middleware for automatic tenant context
class TenantCacheMiddleware:
    """
    Middleware to automatically set tenant context for cache operations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set tenant context for cache if available
        if hasattr(request, 'tenant'):
            tenant_cache.set_tenant(request.tenant)
        else:
            tenant_cache.set_tenant(None)
        
        response = self.get_response(request)
        
        # Clear tenant context after request
        tenant_cache.set_tenant(None)
        
        return response