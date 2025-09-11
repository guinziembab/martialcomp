from django.views.generic import ListView
from django.db.models import Q
from ..utils.discipline_filtering import filter_queryset_by_discipline_federation
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class BaseFilteredListView(ListView):
    """
    Classe de base pour toutes les vues listant des éléments Ã  filtrer par discipline/fédération.
    
    Cette classe applique automatiquement le filtrage selon les disciplines et fédérations
    accessibles Ã  l'utilisateur connecté.
    """
    
    def get_queryset(self):

        # Isolation par organisation
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentification requise")
        
        # Utiliser l'isolation organisationnelle
        base_queryset = get_organization_queryset(self.queryset.model, self.request.user)
        
        # Les administrateurs voient tous les objets de leur organisation
        if self.request.user.is_superuser or self.request.user.is_staff:
            return base_queryset

        queryset = super().get_queryset()
        
        # Si l'utilisateur n'est pas authentifié ou est superuser, pas de filtrage
        if not self.request.user.is_authenticated or self.request.user.is_superuser:
            return queryset
        
        # Appliquer le filtrage par discipline/fédération
        return filter_queryset_by_discipline_federation(queryset, self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajouter les disciplines accessibles au contexte
        if hasattr(self.request, 'user_disciplines'):
            context['user_disciplines'] = self.request.user_disciplines
            context['discipline_federation_mapping'] = self.request.discipline_federation_mapping
        
        return context


class BaseFilteredDetailView:
    """
    Mixin pour les vues de détail avec vérification d'accès par discipline.
    """
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Vérifier l'accès Ã  l'objet
        from ..utils.discipline_filtering import has_access_to_object
        if not has_access_to_object(self.request.user, obj):
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied("Vous n'avez pas accès Ã  cette ressource.")
        
        return obj 
