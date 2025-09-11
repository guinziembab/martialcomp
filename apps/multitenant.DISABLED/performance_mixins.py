"""
Performance-optimized mixins for multi-tenant views.
"""
from django.views.generic import View
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.contrib.auth.mixins import LoginRequiredMixin
from typing import Any, Dict, Optional
import logging

from .cache import tenant_cache, CacheManager
from .db_optimization import (
    TenantQueryOptimizer, 
    QueryCache,
    cached_tenant_method,
    optimized_tenant_query
)
from .utils import get_tenant

logger = logging.getLogger(__name__)


class TenantCacheMixin:
    """
    Mixin to provide caching functionality for tenant views.
    """
    cache_timeout = 300  # 5 minutes default
    
    def get_cache_key(self, suffix: str = '') -> str:
        """
        Generate a cache key for the current view.
        """
        tenant = get_tenant(self.request)
        view_name = self.__class__.__name__
        user_id = self.request.user.id if self.request.user.is_authenticated else 'anonymous'
        
        key_parts = [
            f"view:{view_name}",
            f"user:{user_id}",
        ]
        
        if suffix:
            key_parts.append(suffix)
        
        return ':'.join(key_parts)
    
    def get_cached_data(self, key: str, generator_func: callable) -> Any:
        """
        Get data from cache or generate it.
        """
        tenant_cache.set_tenant(get_tenant(self.request))
        return tenant_cache.get_or_set(key, generator_func, self.cache_timeout)
    
    def invalidate_cache(self, key: str):
        """
        Invalidate a specific cache key.
        """
        tenant_cache.set_tenant(get_tenant(self.request))
        tenant_cache.delete(key)


class TenantQueryMixin:
    """
    Mixin to optimize database queries for tenants.
    """
    select_related_fields = []
    prefetch_related_fields = []
    
    def get_optimized_queryset(self, base_queryset):
        """
        Apply query optimizations to a queryset.
        """
        queryset = base_queryset
        
        if self.select_related_fields:
            queryset = TenantQueryOptimizer.select_for_tenant(
                queryset, 
                self.select_related_fields
            )
        
        if self.prefetch_related_fields:
            queryset = TenantQueryOptimizer.prefetch_for_tenant(
                queryset,
                self.prefetch_related_fields
            )
        
        return queryset
    
    def get_queryset(self):
        """
        Override to apply optimizations.
        """
        queryset = super().get_queryset()
        return self.get_optimized_queryset(queryset)


class TenantPerformanceMixin(TenantCacheMixin, TenantQueryMixin):
    """
    Combined mixin for performance optimization.
    """
    enable_view_cache = False
    view_cache_timeout = 60  # 1 minute
    
    @method_decorator(cache_page(60))
    def dispatch(self, request, *args, **kwargs):
        """
        Apply view-level caching if enabled.
        """
        if self.enable_view_cache:
            return super().dispatch(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add performance metrics to context if in debug mode.
        """
        context = super().get_context_data(**kwargs)
        
        if hasattr(self.request, 'tenant'):
            # Cache tenant settings
            CacheManager.cache_tenant_settings(self.request.tenant)
            
            # Add tenant info to context
            context['tenant'] = self.request.tenant
            context['tenant_features'] = self.get_cached_data(
                'tenant_features',
                lambda: {
                    feature.feature_code: feature.is_enabled
                    for feature in self.request.tenant.features.all()
                }
            )
        
        return context


class TenantDashboardMixin(TenantPerformanceMixin):
    """
    Mixin for tenant dashboard views with heavy caching.
    """
    cache_timeout = 1800  # 30 minutes
    
    @cached_tenant_method('dashboard_stats:{tenant_id}', timeout=1800)
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get cached dashboard statistics.
        """
        from apps.competitions.models import Competition, Practitioner, Registration
        
        tenant = get_tenant(self.request)
        
        stats = {
            'total_practitioners': Practitioner.objects.filter(
                club__federations__tenants=tenant
            ).count(),
            
            'active_competitions': Competition.objects.filter(
                tenants=tenant,
                status__in=['registration_open', 'in_progress']
            ).count(),
            
            'total_registrations': Registration.objects.filter(
                competition__tenants=tenant
            ).count(),
            
            'recent_registrations': Registration.objects.filter(
                competition__tenants=tenant
            ).order_by('-created_at')[:5].select_related(
                'practitioner', 'competition'
            ),
        }
        
        return stats
    
    def get_context_data(self, **kwargs):
        """
        Add dashboard stats to context.
        """
        context = super().get_context_data(**kwargs)
        context['dashboard_stats'] = self.get_dashboard_stats()
        return context


class TenantListViewMixin(TenantPerformanceMixin):
    """
    Mixin for list views with pagination caching.
    """
    paginate_by = 25
    cache_timeout = 600  # 10 minutes
    
    def get_paginated_queryset_cache_key(self) -> str:
        """
        Generate cache key for paginated results.
        """
        page = self.request.GET.get('page', 1)
        ordering = self.request.GET.get('ordering', '')
        search = self.request.GET.get('search', '')
        
        return self.get_cache_key(f"page:{page}:ord:{ordering}:search:{search}")
    
    def get_queryset(self):
        """
        Get cached queryset for current page.
        """
        cache_key = self.get_paginated_queryset_cache_key()
        
        def generate_queryset():
            queryset = super().get_queryset()
            
            # Apply search if provided
            search = self.request.GET.get('search')
            if search and hasattr(self, 'search_fields'):
                from django.db.models import Q
                search_query = Q()
                for field in self.search_fields:
                    search_query |= Q(**{f"{field}__icontains": search})
                queryset = queryset.filter(search_query)
            
            # Apply ordering if provided
            ordering = self.request.GET.get('ordering')
            if ordering and hasattr(self, 'ordering_fields'):
                if ordering.lstrip('-') in self.ordering_fields:
                    queryset = queryset.order_by(ordering)
            
            return queryset
        
        return self.get_cached_data(cache_key, generate_queryset)


class TenantFormViewMixin(TenantPerformanceMixin):
    """
    Mixin for form views with cache invalidation.
    """
    invalidate_cache_on_success = True
    cache_keys_to_invalidate = []
    
    def form_valid(self, form):
        """
        Invalidate relevant caches on successful form submission.
        """
        response = super().form_valid(form)
        
        if self.invalidate_cache_on_success:
            tenant = get_tenant(self.request)
            
            # Invalidate specified cache keys
            for key in self.cache_keys_to_invalidate:
                self.invalidate_cache(key)
            
            # Invalidate tenant-wide caches
            CacheManager.invalidate_tenant_cache(tenant)
        
        return response


class TenantAPIViewMixin(TenantPerformanceMixin):
    """
    Mixin for API views with aggressive caching.
    """
    cache_timeout = 300  # 5 minutes
    use_etag = True
    
    def get_etag(self) -> str:
        """
        Generate ETag for response.
        """
        import hashlib
        import json
        
        data = self.get_serialized_data()
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check ETag and return 304 if not modified.
        """
        if self.use_etag and request.method == 'GET':
            etag = self.get_etag()
            if request.META.get('HTTP_IF_NONE_MATCH') == etag:
                from django.http import HttpResponseNotModified
                return HttpResponseNotModified()
        
        response = super().dispatch(request, *args, **kwargs)
        
        if self.use_etag and request.method == 'GET':
            response['ETag'] = self.get_etag()
        
        return response
