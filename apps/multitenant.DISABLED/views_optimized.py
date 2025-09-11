from django.core.exceptions import PermissionDenied
"""
Example optimized views for multi-tenant applications.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy

from apps.competitions.models import Competition, Registration, Practitioner
from .mixins import TenantAwareViewMixin, TenantRequiredMixin
from .performance_mixins import (
    TenantDashboardMixin,
    TenantListViewMixin,
    TenantFormViewMixin,
    TenantCacheMixin,
    TenantAPIViewMixin
)


class OptimizedTenantDashboardView(LoginRequiredMixin, TenantRequiredMixin, 
                                  TenantDashboardMixin, TenantAwareViewMixin, 
                                  ListView):
    """
    Optimized dashboard view with aggressive caching.
    """
    template_name = 'multitenant/dashboard.html'
    model = Competition
    context_object_name = 'competitions'
    paginate_by = 10
    
    # Query optimizations
    select_related_fields = ['category', 'owner']
    prefetch_related_fields = ['registrations__practitioner']
    
    # Cache configuration
    cache_timeout = 1800  # 30 minutes
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        """Get optimized queryset for competitions."""
        queryset = super().get_queryset()
        return queryset.filter(
            status__in=['registration_open', 'in_progress']
        ).order_by('-date')
    
    def get_context_data(self, **kwargs):
        """Add cached dashboard data to context."""
        context = super().get_context_data(**kwargs)
        
        # Cache key for summary stats
        summary_key = self.get_cache_key('summary_stats')
        
        # Get or calculate summary stats
        context['summary'] = self.get_cached_data(
            summary_key,
            self._calculate_summary_stats
        )
        
        return context
    
    def _calculate_summary_stats(self):
        """Calculate summary statistics."""
        tenant = self.request.tenant
        
        return {
            'total_competitions': Competition.objects.filter(
                tenants=tenant
            ).count(),
            
            'active_practitioners': Practitioner.objects.filter(
                club__federations__tenants=tenant,
                is_active=True
            ).count(),
            
            'monthly_registrations': Registration.objects.filter(
                competition__tenants=tenant,
                created_at__month=datetime.now().month
            ).count(),
        }


class OptimizedCompetitionListView(LoginRequiredMixin, TenantRequiredMixin,
                                  TenantListViewMixin, TenantAwareViewMixin,
                                  ListView):
    """
    Optimized competition list with search and filtering.
    """
    model = Competition
    template_name = 'competitions/list.html'
    context_object_name = 'competitions'
    paginate_by = 25
    
    # Query optimizations
    select_related_fields = ['category', 'owner', 'location']
    prefetch_related_fields = ['disciplines', 'registrations']
    
    # Search configuration
    search_fields = ['name', 'description', 'location__name']
    ordering_fields = ['date', 'name', 'created_at']
    
    # Cache configuration
    cache_timeout = 600  # 10 minutes
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        """Get filtered and cached queryset."""
        queryset = super().get_queryset()
        
        # Apply status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Apply date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filter counts to context."""
        context = super().get_context_data(**kwargs)
        
        # Cache filter counts
        counts_key = self.get_cache_key('filter_counts')
        context['filter_counts'] = self.get_cached_data(
            counts_key,
            self._calculate_filter_counts
        )
        
        return context
    
    def _calculate_filter_counts(self):
        """Calculate counts for each filter option."""
        base_qs = Competition.objects.filter(tenants=self.request.tenant)
        
        return {
            'all': base_qs.count(),
            'registration_open': base_qs.filter(status='registration_open').count(),
            'in_progress': base_qs.filter(status='in_progress').count(),
            'completed': base_qs.filter(status='completed').count(),
        }


class OptimizedCompetitionDetailView(LoginRequiredMixin, TenantRequiredMixin,
                                    TenantCacheMixin, TenantAwareViewMixin,
                                    DetailView):
    """
    Optimized competition detail view.
    """
    model = Competition
    template_name = 'competitions/detail.html'
    context_object_name = 'competition'
    
    # Heavy prefetching for detail view
    select_related_fields = ['category', 'owner', 'location']
    prefetch_related_fields = [
        'disciplines',
        'registrations__practitioner__user',
        'registrations__practitioner__club',
        'matches__practitioner1',
        'matches__practitioner2',
    ]
    
    cache_timeout = 900  # 15 minutes
    
    def get_object(self, queryset=None):
        """Get cached competition object."""
        cache_key = self.get_cache_key(f'competition:{self.kwargs["pk"]}')
        
        def get_competition():
            if queryset is None:
                queryset = self.get_queryset()
            
            # Apply optimizations
            queryset = self.get_optimized_queryset(queryset)
            
            return get_object_or_404(queryset, pk=self.kwargs['pk'])
        
        return self.get_cached_data(cache_key, get_competition)
    
    def get_context_data(self, **kwargs):
        """Add registration statistics to context."""
        context = super().get_context_data(**kwargs)
        competition = context['competition']
        
        # Cache registration stats
        stats_key = self.get_cache_key(f'registration_stats:{competition.pk}')
        context['registration_stats'] = self.get_cached_data(
            stats_key,
            lambda: self._calculate_registration_stats(competition)
        )
        
        return context
    
    def _calculate_registration_stats(self, competition):
        """Calculate registration statistics."""
        registrations = competition.registrations.all()
        
        return {
            'total': registrations.count(),
            'confirmed': registrations.filter(status='confirmed').count(),
            'pending': registrations.filter(status='pending').count(),
            'by_category': registrations.values('category__name').annotate(
                count=Count('id')
            ),
        }


class OptimizedRegistrationCreateView(LoginRequiredMixin, TenantRequiredMixin,
                                     TenantFormViewMixin, TenantAwareViewMixin,
                                     CreateView):
    """
    Optimized registration creation with cache invalidation.
    """
    model = Registration
    template_name = 'registrations/create.html'
    fields = ['practitioner', 'category', 'weight_category']
    
    # Cache invalidation configuration
    cache_keys_to_invalidate = [
        'dashboard_stats',
        'registration_stats',
    ]
    
    def get_success_url(self):
        """Redirect to competition detail after registration."""
        return reverse_lazy('competition-detail', kwargs={
            'pk': self.object.competition.pk
        })
    
    def form_valid(self, form):
        """Add competition to registration before saving."""
        form.instance.competition_id = self.kwargs['competition_pk']
        return super().form_valid(form)


# Example API view with ETag support
from django.http import JsonResponse
from django.views import View
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class OptimizedCompetitionAPIView(TenantRequiredMixin, TenantAPIViewMixin, View):
    """
    Optimized API view with ETag support.
    """
    cache_timeout = 300  # 5 minutes
    
    def get(self, request, *args, **kwargs):
        """Get competition data as JSON."""
        competition_id = kwargs.get('pk')
        
        # Get cached data
        cache_key = f'api:competition:{competition_id}'
        data = self.get_cached_data(
            cache_key,
            lambda: self._get_competition_data(competition_id)
        )
        
        return JsonResponse(data)
    
    def _get_competition_data(self, competition_id):
        """Get serialized competition data."""
        competition = get_object_or_404(
            Competition.objects.select_related('category', 'owner'),
            pk=competition_id,
            tenants=self.request.tenant
        )
        
        return {
            'id': competition.id,
            'name': competition.name,
            'date': competition.date.isoformat(),
            'status': competition.status,
            'category': competition.category.name,
            'registration_count': competition.registrations.count(),
        }
    
    def get_serialized_data(self):
        """Get data for ETag generation."""
        return self._get_competition_data(self.kwargs.get('pk'))
