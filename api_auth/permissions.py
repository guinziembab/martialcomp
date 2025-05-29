from rest_framework import permissions
from django.utils.translation import gettext_lazy as _


class IsTenantUser(permissions.BasePermission):
    """
    Permission vérifiant que l'utilisateur appartient au tenant actuel.
    """
    message = _("Vous n'êtes pas autorisé à accéder aux ressources de ce tenant.")
    
    def has_permission(self, request, view):
        # Vérifier si un tenant est défini dans la requête
        tenant = getattr(request, 'tenant', None)
        
        # Si aucun tenant n'est défini, autoriser (un autre middleware gérera)
        if not tenant:
            return True
        
        # Si l'utilisateur est un superuser, autoriser
        if request.user.is_superuser:
            return True
        
        # Vérifier si l'utilisateur a un accès au tenant
        # (en fonction de l'implémentation spécifique)
        if hasattr(request.user, 'tenant_access'):
            return tenant.id in request.user.tenant_access
        
        # Dans certains cas, le token pourrait contenir directement l'ID du tenant
        if hasattr(request, 'auth') and isinstance(request.auth, dict):
            return request.auth.get('tenant_id') == str(tenant.id)
        
        return False


class IsTokenOwner(permissions.BasePermission):
    """
    Permission vérifiant que l'utilisateur est le propriétaire du token.
    """
    message = _("Vous n'êtes pas autorisé à accéder à ce token.")
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsDeviceOwner(permissions.BasePermission):
    """
    Permission vérifiant que l'utilisateur est le propriétaire de l'appareil.
    """
    message = _("Vous n'êtes pas autorisé à accéder à cet appareil.")
    
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class HasRolePermission(permissions.BasePermission):
    """
    Permission basée sur le rôle de l'utilisateur.
    """
    def __init__(self, required_roles=None):
        self.required_roles = required_roles or []
    
    def has_permission(self, request, view):
        # Si aucun rôle n'est requis, autoriser
        if not self.required_roles:
            return True
        
        # Si l'utilisateur est un superuser, autoriser
        if request.user.is_superuser:
            return True
        
        # Vérifier le rôle de l'utilisateur
        user_profile = getattr(request.user, 'profile', None)
        if not user_profile or not hasattr(user_profile, 'role'):
            return False
        
        return user_profile.role in self.required_roles


class HasFederationPermission(permissions.BasePermission):
    """
    Permission vérifiant que l'utilisateur a des droits dans la fédération.
    """
    message = _("Vous n'avez pas les permissions requises dans cette fédération.")
    
    def has_permission(self, request, view):
        # Si le paramètre federation_id n'est pas fourni, on ne filtre pas
        federation_id = request.query_params.get('federation_id')
        if not federation_id:
            return True
            
        # Si l'utilisateur est un superuser, autoriser
        if request.user.is_superuser:
            return True
        
        # Vérifier si l'utilisateur a des permissions dans cette fédération
        # Cette implémentation dépend de votre modèle de données
        try:
            from competitions.models import Federation
            federation = Federation.objects.get(id=federation_id)
            
            # Vérifier si l'utilisateur est administrateur de la fédération
            if request.user in federation.administrators.all():
                return True
                
            # Autres vérifications de permissions...
            
        except (ImportError, Federation.DoesNotExist):
            pass
            
        return False


class HasClubPermission(permissions.BasePermission):
    """
    Permission vérifiant que l'utilisateur a des droits dans le club.
    """
    message = _("Vous n'avez pas les permissions requises dans ce club.")
    
    def has_permission(self, request, view):
        # Si le paramètre club_id n'est pas fourni, on ne filtre pas
        club_id = request.query_params.get('club_id')
        if not club_id:
            return True
            
        # Si l'utilisateur est un superuser, autoriser
        if request.user.is_superuser:
            return True
        
        # Vérifier si l'utilisateur a des permissions dans ce club
        try:
            from competitions.models import Club
            club = Club.objects.get(id=club_id)
            
            # Vérifier si l'utilisateur est propriétaire du club
            if club.owner == request.user:
                return True
                
            # Vérifier si l'utilisateur est un administrateur du club
            if request.user in club.administrators.all():
                return True
                
            # Autres vérifications de permissions...
            
        except (ImportError, Club.DoesNotExist):
            pass
            
        return False