from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import Tenant, Domain, TenantFeature


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'slug', 'domain', 'continent', 'plan_info', 
        'is_active', 'created_at'
    ]
    list_filter = [
        'is_active', 'continent', 'subscription_plan', 
        'payment_provider', 'created_at'
    ]
    search_fields = ['name', 'slug', 'domain', 'stripe_account_id']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'activated_at', 
        'deactivated_at', 'price_display'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': (
                'id', 'name', 'slug', 'schema_name', 'owner',
                'is_active', 'created_at', 'updated_at'
            )
        }),
        (_('Configuration domaine'), {
            'fields': ('domain',)
        }),
        (_('Localisation et facturation'), {
            'fields': (
                'continent', 'country', 'timezone', 'currency', 'language'
            )
        }),
        (_('Abonnement'), {
            'fields': (
                'subscription_plan', 'price_display',
                'subscription_start_date', 'subscription_end_date',
                'is_trial', 'trial_end_date'
            )
        }),
        (_('Configuration paiement'), {
            'fields': (
                'payment_provider', 'stripe_account_id', 'payment_config'
            ),
            'classes': ('collapse',)
        }),
        (_('Limites et fonctionnalités'), {
            'fields': (
                'max_users', 'max_disciplines', 'features_config'
            ),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('activated_at', 'deactivated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def plan_info(self, obj):
        """Affiche le plan et son prix."""
        price = obj.get_price_for_plan()
        plan = obj.get_subscription_plan_display()
        return format_html(
            '<span style="font-weight: bold;">{}</span><br>'
            '<span style="color: #666;">{}â‚¬/an</span>',
            plan, price
        )
    plan_info.short_description = _('Plan')
    
    def price_display(self, obj):
        """Affiche le prix selon le continent."""
        price = obj.get_price_for_plan()
        return f"{price}â‚¬/an"
    price_display.short_description = _('Prix annuel')
    
    def get_queryset(self, request):
        """Filtre pour les superadmins uniquement."""
        qs = super().get_queryset(request)
        
        # Seuls les superadmins peuvent voir tous les tenants
        if not request.user.is_superuser:
            # Les admins normaux ne voient que leur propre tenant
            if hasattr(request, 'tenant') and request.tenant:
                qs = qs.filter(id=request.tenant.id)
            else:
                qs = qs.none()
        
        return qs
    
    def has_add_permission(self, request):
        """Seuls les superadmins peuvent créer des tenants."""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Seuls les superadmins peuvent supprimer des tenants."""
        return request.user.is_superuser
    
    def save_model(self, request, obj, form, change):
        """Génère automatiquement le nom du schéma si nécessaire."""
        if not obj.schema_name:
            obj.schema_name = f"tenant_{obj.slug.replace('-', '_')}"
        
        super().save_model(request, obj, form, change)
        
        # Créer le schéma PostgreSQL si c'est une nouvelle création
        if not change:
            from .utils import create_schema_for_tenant
            try:
                create_schema_for_tenant(obj)
                self.message_user(
                    request,
                    f"Schéma PostgreSQL '{obj.schema_name}' créé avec succès.",
                    level='SUCCESS'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f"Erreur lors de la création du schéma: {str(e)}",
                    level='ERROR'
                )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ['domain', 'tenant', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['domain', 'tenant__name']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        """Seuls les superadmins peuvent ajouter des domaines."""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Seuls les superadmins peuvent supprimer des domaines."""
        return request.user.is_superuser


@admin.register(TenantFeature)
class TenantFeatureAdmin(admin.ModelAdmin):
    list_display = [
        'tenant', 'feature_code', 'is_enabled', 
        'enabled_until', 'has_metadata'
    ]
    list_filter = ['is_enabled', 'feature_code']
    search_fields = ['tenant__name', 'feature_code']
    readonly_fields = []
    
    fieldsets = (
        (_('Configuration'), {
            'fields': (
                'tenant', 'feature_code', 'is_enabled', 'enabled_until'
            )
        }),
        (_('Métadonnées'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def has_metadata(self, obj):
        """Indique si des métadonnées sont présentes."""
        return bool(obj.metadata)
    has_metadata.boolean = True
    has_metadata.short_description = _('Métadonnées')
    
    def get_queryset(self, request):
        """Filtre selon les permissions."""
        qs = super().get_queryset(request)
        
        if not request.user.is_superuser:
            if hasattr(request, 'tenant') and request.tenant:
                qs = qs.filter(tenant=request.tenant)
            else:
                qs = qs.none()
        
        return qs
