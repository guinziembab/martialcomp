"""
Outils de sécurité pour l'isolation organisationnelle.
"""
from functools import wraps
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect
from django.contrib import messages
import logging

# Configurer le logger de sécurité
security_logger = logging.getLogger('security.organization_access')

def require_organization_access(view_func):
    """
    Décorateur qui vérifie que l'utilisateur a accès Ã  l'objet demandé
    basé sur son organisation.
    
    Ã€ utiliser sur les vues qui accèdent Ã  un objet spécifique avec un ID.
    
    Exemple:
    @require_organization_access
    def my_view(request, object_id):
        obj = get_object_or_404(MyModel, pk=object_id)
        # Le décorateur a déjÃ  vérifié que l'utilisateur a accès Ã  cet objet
        ...
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérifier que l'utilisateur est connecté
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Les superusers et staff ont toujours accès
        if request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
            
        # Récupérer l'ID de l'objet (assumé Ãªtre le premier argument position ou un kwarg)
        object_id = None
        if args:
            object_id = args[0]
        else:
            # Chercher dans les arguments nommés (pk, id, object_id, etc.)
            for key in ['pk', 'id', 'object_id']:
                if key in kwargs:
                    object_id = kwargs[key]
                    break
        
        if not object_id:
            # Pas d'ID trouvé, laisser la vue gérer cela
            return view_func(request, *args, **kwargs)
            
        # Récupérer le modèle de la vue
        model = getattr(view_func, 'model', None)
        if not model:
            # Le modèle n'est pas spécifié, impossible de vérifier l'accès
            return view_func(request, *args, **kwargs)
            
        try:
            # Récupérer l'objet
            obj = model.objects.get(pk=object_id)
            
            # Vérifier si l'objet a une méthode pour vérifier l'accès
            if hasattr(obj, 'is_accessible_by'):
                if not obj.is_accessible_by(request.user):
                    security_logger.warning(
                        f"User {request.user.id} attempted to access {model.__name__} {object_id} "
                        f"from different organization"
                    )
                    raise PermissionDenied(_("Vous n'avez pas accès Ã  cette ressource"))
            # Sinon, vérifier s'il a un champ organisation
            elif hasattr(obj, 'organization') and hasattr(request.user, 'organization'):
                if obj.organization != request.user.organization:
                    security_logger.warning(
                        f"User {request.user.id} attempted to access {model.__name__} {object_id} "
                        f"from organization {request.user.organization.id} but object belongs to {obj.organization.id}"
                    )
                    raise PermissionDenied(_("Vous n'avez pas accès Ã  cette ressource"))
            # Vérifier s'il a un champ club
            elif hasattr(obj, 'club') and hasattr(request.user, 'club'):
                if obj.club != request.user.club:
                    security_logger.warning(
                        f"User {request.user.id} attempted to access {model.__name__} {object_id} "
                        f"from club {request.user.club.id} but object belongs to {obj.club.id}"
                    )
                    raise PermissionDenied(_("Vous n'avez pas accès Ã  cette ressource"))
            # Vérifier s'il a un champ fédération
            elif hasattr(obj, 'federation') and hasattr(request.user, 'federation'):
                if obj.federation != request.user.federation:
                    security_logger.warning(
                        f"User {request.user.id} attempted to access {model.__name__} {object_id} "
                        f"from federation {request.user.federation.id} but object belongs to {obj.federation.id}"
                    )
                    raise PermissionDenied(_("Vous n'avez pas accès Ã  cette ressource"))
                    
        except model.DoesNotExist:
            # L'objet n'existe pas, laisser la vue gérer cela
            pass
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def filter_queryset_for_user(queryset, user):
    """
    Filtre un queryset pour ne montrer que les objets accessibles Ã  l'utilisateur.
    
    Args:
        queryset: Le queryset Ã  filtrer
        user: L'utilisateur pour lequel filtrer
        
    Returns:
        QuerySet: Le queryset filtré
    """
    # Les superusers et staff voient tout
    if user.is_superuser or user.is_staff:
        return queryset
        
    # Utiliser le manager personnalisé s'il existe
    if hasattr(queryset, 'for_user'):
        return queryset.for_user(user)
    
    # Filtrer selon le type d'organisation de l'utilisateur
    model = queryset.model
    
    # Filtrer par organisation
    if hasattr(model, 'organization') and hasattr(user, 'organization') and user.organization:
        return queryset.filter(organization=user.organization)
        
    # Filtrer par club
    elif hasattr(model, 'club') and hasattr(user, 'club') and user.club:
        return queryset.filter(club=user.club)
        
    # Filtrer par fédération
    elif hasattr(model, 'federation') and hasattr(user, 'federation') and user.federation:
        return queryset.filter(federation=user.federation)
        
    # Si aucun filtrage n'est possible, ne retourner aucun objet
    # C'est plus sÃ»r que de retourner tous les objets sans filtrage
    return queryset.none()


def organization_isolated_view(model):
    """
    Décorateur de classe qui ajoute l'isolation organisationnelle Ã  une vue.
    
    Ce décorateur modifie get_queryset pour filtrer par l'organisation de l'utilisateur.
    
    Exemple:
    @organization_isolated_view(MyModel)
    class MyListView(ListView):
        template_name = 'my_template.html'
        # get_queryset sera automatiquement défini pour filtrer par organisation
    """
    def decorator(view_class):
        original_get_queryset = getattr(view_class, 'get_queryset', None)
        
        def get_queryset(self):
            # Utiliser le queryset original s'il existe, sinon tous les objets du modèle
            if original_get_queryset:
                queryset = original_get_queryset(self)
            else:
                queryset = model.objects.all()
                
            # Filtrer pour l'utilisateur actuel
            return filter_queryset_for_user(queryset, self.request.user)
            
        # Attacher la nouvelle méthode Ã  la classe
        view_class.get_queryset = get_queryset
        view_class.model = model
        
        return view_class
        
    return decorator


class OrganizationIsolationMiddleware:
    """
    Middleware qui vérifie l'isolation organisationnelle pour toutes les requÃªtes.
    
    Ce middleware surveille les fuites potentielles de données et les tentatives d'accès
    Ã  des ressources d'autres organisations.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Vérifie si la vue accède potentiellement Ã  des données d'autres organisations.
        Pour l'instant, c'est seulement un monitoring, pas un blocage actif.
        """
        # Ignorer les requÃªtes non authentifiées
        if not request.user.is_authenticated:
            return None
            
        # Ignorer les admins et le staff
        if request.user.is_superuser or request.user.is_staff:
            return None
            
        # Vérifier si la vue a une annotation indiquant qu'elle est sécurisée
        if getattr(view_func, 'organization_isolation_checked', False):
            return None
            
        # Vérifier si la vue a un nom qui indique qu'elle est probablement un listing
        view_name = view_func.__name__ if hasattr(view_func, '__name__') else str(view_func)
        if any(pattern in view_name.lower() for pattern in ['list', 'index', 'all', 'search']):
            # Log pour surveillance, Ã  transformer en blocage plus tard si nécessaire
            security_logger.info(
                f"User {request.user.id} accessing potential listing view {view_name} "
                f"without explicit organization isolation check."
            )
            
        return None


def mark_view_as_organization_isolated(view_func):
    """
    Marque une vue comme déjÃ  vérifiée pour l'isolation organisationnelle.
    Utile pour les vues qui implémentent leur propre logique d'isolation.
    """
    view_func.organization_isolation_checked = True
    return view_func
