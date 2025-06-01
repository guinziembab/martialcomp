"""
Vues d'administration super-admin pour la gestion des tenants.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from django.utils import timezone
from django.db.models import Count, Q, Sum
from datetime import datetime, timedelta

from multitenant.models import Tenant, Domain, TenantFeature
from multitenant.payments.models import TenantPayment
from competitions.models import Practitioner, Competition, CompetitionRegistration
from multitenant.forms import TenantForm, DomainForm, TenantFeatureForm


class SuperAdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour limiter l'accès aux super-admins."""
    def test_func(self):
        return self.request.user.is_superuser


class TenantDashboardView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    """Dashboard principal pour la gestion des tenants."""
    model = Tenant
    template_name = 'multitenant/admin/dashboard.html'
    context_object_name = 'tenants'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtres
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(domain__icontains=search) |
                Q(schema_name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        plan = self.request.GET.get('plan')
        if plan:
            queryset = queryset.filter(subscription_plan=plan)
        
        return queryset.select_related('owner').annotate(
            domain_count=Count('domains'),
            feature_count=Count('features'),
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques globales
        context['stats'] = {
            'total_tenants': Tenant.objects.count(),
            'active_tenants': Tenant.objects.filter(is_active=True).count(),
            'total_revenue': TenantPayment.objects.filter(
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'tenants_by_plan': Tenant.objects.values('subscription_plan').annotate(
                count=Count('id')
            ),
            'tenants_by_continent': Tenant.objects.values('continent').annotate(
                count=Count('id')
            ),
        }
        
        # Graphiques
        context['growth_data'] = self._get_growth_data()
        context['revenue_data'] = self._get_revenue_data()
        
        return context
    
    def _get_growth_data(self):
        """Données de croissance des 12 derniers mois."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            count = Tenant.objects.filter(
                created_at__lte=current_date
            ).count()
            
            data.append({
                'date': current_date.strftime('%Y-%m'),
                'count': count
            })
            
            # Avancer d'un mois
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return data
    
    def _get_revenue_data(self):
        """Données de revenus des 12 derniers mois."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)
        
        payments = TenantPayment.objects.filter(
            created_at__gte=start_date,
            status='completed'
        ).values('created_at__month', 'created_at__year').annotate(
            total=Sum('amount')
        ).order_by('created_at__year', 'created_at__month')
        
        return [
            {
                'month': f"{payment['created_at__year']}-{payment['created_at__month']:02d}",
                'revenue': float(payment['total'])
            }
            for payment in payments
        ]


class TenantDetailView(LoginRequiredMixin, SuperAdminRequiredMixin, DetailView):
    """Vue détaillée d'un tenant."""
    model = Tenant
    template_name = 'multitenant/admin/tenant_detail.html'
    context_object_name = 'tenant'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.object
        
        # Statistiques du tenant
        with connection.cursor() as cursor:
            # Basculer vers le schéma du tenant
            cursor.execute(f'SET search_path TO {tenant.schema_name}')
            
            # Compter les pratiquants
            cursor.execute("SELECT COUNT(*) FROM competitions_practitioner")
            practitioner_count = cursor.fetchone()[0]
            
            # Compter les compétitions
            cursor.execute("SELECT COUNT(*) FROM competitions_competition")
            competition_count = cursor.fetchone()[0]
            
            # Compter les inscriptions
            cursor.execute("SELECT COUNT(*) FROM competitions_registration")
            registration_count = cursor.fetchone()[0]
        
        context['tenant_stats'] = {
            'practitioners': practitioner_count,
            'competitions': competition_count,
            'registrations': registration_count,
        }
        
        # Domaines
        context['domains'] = tenant.domains.all()
        
        # Features
        context['features'] = tenant.features.all()
        
        # Paiements récents
        context['recent_payments'] = tenant.payments.order_by('-created_at')[:10]
        
        # Utilisation des ressources
        context['resource_usage'] = self._get_resource_usage(tenant)
        
        return context
    
    def _get_resource_usage(self, tenant):
        """Calcule l'utilisation des ressources du tenant."""
        with connection.cursor() as cursor:
            # Taille du schéma
            cursor.execute("""
                SELECT pg_size_pretty(
                    pg_database_size(current_database())
                ) as size
            """)
            db_size = cursor.fetchone()[0]
            
            # Nombre de connexions actives
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database()
                AND state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
        
        return {
            'database_size': db_size,
            'active_connections': active_connections,
            'storage_used': self._calculate_storage_used(tenant),
        }
    
    def _calculate_storage_used(self, tenant):
        """Calcule l'espace de stockage utilisé."""
        # Calculer la taille des fichiers media
        import os
        
        media_path = f"media/tenants/{tenant.schema_name}"
        total_size = 0
        
        if os.path.exists(media_path):
            for dirpath, dirnames, filenames in os.walk(media_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)
        
        # Convertir en format lisible
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                return f"{total_size:.1f} {unit}"
            total_size /= 1024.0
        
        return f"{total_size:.1f} TB"


class TenantCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    """Création d'un nouveau tenant."""
    model = Tenant
    form_class = TenantForm
    template_name = 'multitenant/admin/tenant_form.html'
    success_url = reverse_lazy('multitenant:admin-dashboard')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Tenant '{self.object.name}' créé avec succès."
        )
        return response


class TenantUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    """Modification d'un tenant."""
    model = Tenant
    form_class = TenantForm
    template_name = 'multitenant/admin/tenant_form.html'
    
    def get_success_url(self):
        return reverse_lazy('multitenant:admin-tenant-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Tenant '{self.object.name}' mis à jour."
        )
        return response


class TenantToggleStatusView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    """Active/désactive un tenant."""
    model = Tenant
    fields = []
    
    def post(self, request, *args, **kwargs):
        tenant = self.get_object()
        tenant.is_active = not tenant.is_active
        tenant.save()
        
        status = "activé" if tenant.is_active else "désactivé"
        messages.success(request, f"Tenant '{tenant.name}' {status}.")
        
        return redirect('multitenant:admin-tenant-detail', pk=tenant.pk)


class DomainCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    """Ajouter un domaine à un tenant."""
    model = Domain
    form_class = DomainForm
    template_name = 'multitenant/admin/domain_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        tenant_id = self.kwargs.get('tenant_id')
        if tenant_id:
            initial['tenant'] = get_object_or_404(Tenant, pk=tenant_id)
        return initial
    
    def get_success_url(self):
        return reverse_lazy(
            'multitenant:admin-tenant-detail',
            kwargs={'pk': self.object.tenant.pk}
        )


class DomainUpdateView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    """Met à jour un domaine existant."""
    model = Domain
    form_class = DomainForm
    template_name = 'multitenant/admin/domain_form.html'
    
    def get_success_url(self):
        return reverse_lazy('multitenant:admin-tenant-detail', kwargs={'pk': self.object.tenant.pk})
    
    def form_valid(self, form):
        messages.success(self.request, f"Domaine {form.instance.domain} mis à jour avec succès.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = self.object.tenant
        return context


class DomainDeleteView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    """Supprime un domaine."""
    model = Domain
    fields = []
    
    def post(self, request, *args, **kwargs):
        domain = self.get_object()
        tenant = domain.tenant
        
        # Vérifier qu'il reste au moins un domaine
        if tenant.domains.count() <= 1:
            messages.error(request, "Impossible de supprimer le dernier domaine d'un tenant.")
            return redirect('multitenant:admin-tenant-detail', pk=tenant.pk)
        
        # Vérifier que ce n'est pas le domaine principal
        if domain.is_primary:
            messages.error(request, "Impossible de supprimer le domaine principal. Définissez d'abord un autre domaine comme principal.")
            return redirect('multitenant:admin-tenant-detail', pk=tenant.pk)
        
        domain_name = domain.domain
        domain.delete()
        messages.success(request, f"Domaine {domain_name} supprimé avec succès.")
        return redirect('multitenant:admin-tenant-detail', pk=tenant.pk)


class TenantFeatureCreateView(LoginRequiredMixin, SuperAdminRequiredMixin, CreateView):
    """Ajoute une feature à un tenant."""
    model = TenantFeature
    form_class = TenantFeatureForm
    template_name = 'multitenant/admin/feature_form.html'
    
    def get_success_url(self):
        return reverse_lazy('multitenant:admin-tenant-detail', kwargs={'pk': self.kwargs['tenant_id']})
    
    def form_valid(self, form):
        tenant = get_object_or_404(Tenant, pk=self.kwargs['tenant_id'])
        form.instance.tenant = tenant
        messages.success(self.request, f"Feature {form.instance.get_feature_display()} ajoutée avec succès.")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = get_object_or_404(Tenant, pk=self.kwargs['tenant_id'])
        return context


class TenantFeatureToggleView(LoginRequiredMixin, SuperAdminRequiredMixin, UpdateView):
    """Active/désactive une feature pour un tenant."""
    model = TenantFeature
    fields = []
    
    def post(self, request, *args, **kwargs):
        feature = self.get_object()
        feature.is_enabled = not feature.is_enabled
        feature.save()
        
        status = "activée" if feature.is_enabled else "désactivée"
        messages.success(
            request,
            f"Feature '{feature.feature_code}' {status} pour '{feature.tenant.name}'."
        )
        
        return redirect('multitenant:admin-tenant-detail', pk=feature.tenant.pk)


class TenantPaymentsView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    """Liste des paiements d'un tenant."""
    model = TenantPayment
    template_name = 'multitenant/admin/payments_list.html'
    context_object_name = 'payments'
    paginate_by = 50
    
    def get_queryset(self):
        tenant = get_object_or_404(Tenant, pk=self.kwargs['tenant_id'])
        return tenant.payments.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tenant'] = get_object_or_404(Tenant, pk=self.kwargs['tenant_id'])
        return context


class SystemHealthView(LoginRequiredMixin, SuperAdminRequiredMixin, ListView):
    """Vue de santé du système multi-tenant."""
    template_name = 'multitenant/admin/system_health.html'
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        context = {}
        
        # Santé des tenants
        context['tenant_health'] = self._check_tenant_health()
        
        # Métriques système
        context['system_metrics'] = self._get_system_metrics()
        
        # Alertes
        context['alerts'] = self._get_system_alerts()
        
        return context
    
    def _check_tenant_health(self):
        """Vérifie la santé de chaque tenant."""
        health_data = []
        
        for tenant in Tenant.objects.filter(is_active=True):
            try:
                with connection.cursor() as cursor:
                    # Vérifier l'existence du schéma
                    cursor.execute("""
                        SELECT EXISTS(
                            SELECT schema_name 
                            FROM information_schema.schemata 
                            WHERE schema_name = %s
                        )
                    """, [tenant.schema_name])
                    
                    schema_exists = cursor.fetchone()[0]
                    
                    health_data.append({
                        'tenant': tenant,
                        'schema_exists': schema_exists,
                        'status': 'healthy' if schema_exists else 'error',
                        'last_payment': tenant.payments.filter(
                            status='completed'
                        ).order_by('-created_at').first()
                    })
            except Exception as e:
                health_data.append({
                    'tenant': tenant,
                    'status': 'error',
                    'error': str(e)
                })
        
        return health_data
    
    def _get_system_metrics(self):
        """Récupère les métriques système."""
        with connection.cursor() as cursor:
            # Connexions actives
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """)
            active_connections = cursor.fetchone()[0]
            
            # Taille totale de la base
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database()))
            """)
            db_size = cursor.fetchone()[0]
            
            # Nombre de schémas
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')
            """)
            schema_count = cursor.fetchone()[0]
        
        return {
            'active_connections': active_connections,
            'database_size': db_size,
            'schema_count': schema_count,
            'total_tenants': Tenant.objects.count(),
            'active_tenants': Tenant.objects.filter(is_active=True).count(),
        }
    
    def _get_system_alerts(self):
        """Récupère les alertes système."""
        alerts = []
        
        # Tenants sans paiement récent
        cutoff_date = timezone.now() - timedelta(days=35)
        overdue_tenants = Tenant.objects.filter(
            is_active=True,
            subscription_plan__in=['masters', 'champion']
        ).exclude(
            payments__created_at__gte=cutoff_date,
            payments__status='completed'
        )
        
        for tenant in overdue_tenants:
            alerts.append({
                'type': 'warning',
                'message': f"Tenant '{tenant.name}' sans paiement depuis plus de 35 jours",
                'tenant': tenant
            })
        
        # Tenants avec utilisation excessive
        for tenant in Tenant.objects.filter(is_active=True):
            # Ici, ajouter des vérifications d'utilisation
            pass
        
        return alerts