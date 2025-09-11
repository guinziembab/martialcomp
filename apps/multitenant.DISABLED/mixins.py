from django.db import models
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.contrib.auth.mixins import AccessMixin
from django.db.models.query import QuerySet
from django import forms

from .middleware import get_current_tenant


class TenantAwareQuerySet(QuerySet):
    """
    QuerySet personnalisé qui filtre automatiquement par tenant.
    """
    
    def _filter_by_tenant(self):
        """Applique le filtre tenant si nécessaire."""
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant'):
            return self.filter(tenant=tenant)
        return self
    
    def _clone(self):
        """Clone le queryset en conservant les filtres tenant."""
        c = super()._clone()
        return c
    
    # Surcharge des méthodes principales pour appliquer le filtre tenant
    def all(self):
        return super().all()._filter_by_tenant()
    
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)._filter_by_tenant()
    
    def exclude(self, *args, **kwargs):
        return super().exclude(*args, **kwargs)._filter_by_tenant()
    
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)


class TenantAwareManager(models.Manager):
    """
    Manager personnalisé qui utilise TenantAwareQuerySet.
    """
    
    def get_queryset(self):
        """Retourne un TenantAwareQuerySet."""
        return TenantAwareQuerySet(self.model, using=self._db)
    
    def create(self, **kwargs):
        """Crée un objet en ajoutant automatiquement le tenant."""
        tenant = get_current_tenant()
        if tenant and hasattr(self.model, 'tenant') and 'tenant' not in kwargs:
            kwargs['tenant'] = tenant
        return super().create(**kwargs)


class TenantAwareModel(models.Model):
    """
    Modèle abstrait pour les modèles tenant-aware.
    Ajoute automatiquement un champ tenant et utilise TenantAwareManager.
    """
    
    tenant = models.ForeignKey(
        'multitenant.Tenant',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        verbose_name='Tenant'
    )
    
    objects = TenantAwareManager()
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['tenant']),
        ]
    
    def save(self, *args, **kwargs):
        """Sauvegarde en ajoutant automatiquement le tenant si nécessaire."""
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ImproperlyConfigured(
                    f"Impossible de sauvegarder {self.__class__.__name__} sans tenant défini"
                )
        super().save(*args, **kwargs)


class TenantAwareViewMixin:
    """
    Mixin pour les vues Django qui filtrent automatiquement par tenant.
    """
    
    def get_queryset(self):
        """Filtre le queryset par tenant."""
        queryset = super().get_queryset()
        
        if hasattr(self.request, 'tenant') and self.request.tenant:
            if hasattr(queryset.model, 'tenant'):
                queryset = queryset.filter(tenant=self.request.tenant)
        
        return queryset
    
    def get_form_kwargs(self):
        """Ajoute le tenant aux kwargs du formulaire."""
        kwargs = super().get_form_kwargs()
        
        if hasattr(self.request, 'tenant') and self.request.tenant:
            kwargs['tenant'] = self.request.tenant
        
        return kwargs


class TenantRequiredMixin(AccessMixin):
    """
    Mixin qui s'assure qu'un tenant est défini pour accéder Ã  la vue.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class SuperAdminRequiredMixin(AccessMixin):
    """
    Mixin qui s'assure que l'utilisateur est un super-administrateur.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.is_superuser:
            raise PermissionDenied("Accès réservé aux super-administrateurs")
            
        return super().dispatch(request, *args, **kwargs)


class TenantFormMixin:
    """
    Mixin pour les formulaires Django qui gèrent automatiquement le tenant.
    """
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        
        # Cacher le champ tenant s'il existe
        if 'tenant' in self.fields:
            self.fields['tenant'].widget = forms.HiddenInput()
    
    def save(self, commit=True):
        """Sauvegarde en ajoutant le tenant."""
        instance = super().save(commit=False)
        
        if hasattr(instance, 'tenant') and not instance.tenant_id:
            if self.tenant:
                instance.tenant = self.tenant
            else:
                tenant = get_current_tenant()
                if tenant:
                    instance.tenant = tenant
        
        if commit:
            instance.save()
        
        return instance


class TenantAdminMixin:
    """
    Mixin pour l'admin Django qui filtre automatiquement par tenant.
    """
    
    def get_queryset(self, request):
        """Filtre le queryset par tenant dans l'admin."""
        qs = super().get_queryset(request)
        
        # Pour l'admin, on peut voir tous les tenants si on est superadmin
        if request.user.is_superuser:
            return qs
        
        # Sinon, filtrer par tenant de l'utilisateur
        if hasattr(request, 'tenant') and request.tenant:
            if hasattr(qs.model, 'tenant'):
                qs = qs.filter(tenant=request.tenant)
        
        return qs
    
    def save_model(self, request, obj, form, change):
        """Sauvegarde en ajoutant le tenant si nécessaire."""
        if hasattr(obj, 'tenant') and not obj.tenant_id:
            if hasattr(request, 'tenant') and request.tenant:
                obj.tenant = request.tenant
        
        super().save_model(request, obj, form, change)


# Décorateur pour marquer une fonction comme nécessitant un tenant
def tenant_required(view_func):
    """
    Décorateur qui s'assure qu'un tenant est défini pour accéder Ã  la vue.
    """
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'tenant') or not request.tenant:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Accès refusé: aucun tenant défini")
        return view_func(request, *args, **kwargs)
    
    wrapped_view.__wrapped__ = view_func
    return wrapped_view
