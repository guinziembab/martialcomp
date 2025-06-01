from rest_framework import permissions
from django.contrib.contenttypes.models import ContentType
from .models import DocumentShare, DocumentFolder


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée qui permet uniquement aux propriétaires d'un objet de le modifier.
    """
    def has_object_permission(self, request, view, obj):
        # Les autorisations de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Les droits d'écriture sont réservés au propriétaire
        return obj.created_by == request.user


class HasDocumentPermission(permissions.BasePermission):
    """
    Permission qui vérifie si un utilisateur a accès à un document spécifique.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Les administrateurs ont toujours accès
        if user.is_superuser or user.is_staff:
            return True
        
        # Le propriétaire a toujours accès
        if obj.created_by == user:
            return True
        
        # Les documents publics sont accessibles en lecture
        if obj.is_public and request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier les partages directs avec l'utilisateur
        user_share = DocumentShare.objects.filter(document=obj, user=user).first()
        if user_share:
            if request.method in permissions.SAFE_METHODS:
                # Lecture autorisée pour tous les niveaux d'accès
                return True
            elif user_share.access_level in ['W', 'F'] and request.method in ['PUT', 'PATCH']:
                # Modification autorisée pour les niveaux d'accès Écriture et Contrôle total
                return True
            elif user_share.access_level == 'F' and request.method == 'DELETE':
                # Suppression autorisée uniquement pour le niveau d'accès Contrôle total
                return True
        
        # Vérifier les partages avec des groupes dont l'utilisateur fait partie
        # (clubs, fédérations, etc.)
        try:
            # Récupérer tous les objets dont l'utilisateur fait partie
            # Club
            try:
                from competitions.models import Club, ClubRole
                club_ids = []
                # Récupérer les clubs dont l'utilisateur est membre
                club_roles = ClubRole.objects.filter(user=user)
                for role in club_roles:
                    club_ids.append(role.club.id)
                
                # Vérifier si le document est partagé avec l'un de ces clubs
                club_content_type = ContentType.objects.get_for_model(Club)
                club_shares = DocumentShare.objects.filter(
                    document=obj,
                    group_content_type=club_content_type,
                    group_object_id__in=club_ids
                )
                
                if club_shares.exists():
                    share = club_shares.first()
                    if request.method in permissions.SAFE_METHODS:
                        return True
                    elif share.access_level in ['W', 'F'] and request.method in ['PUT', 'PATCH']:
                        return True
                    elif share.access_level == 'F' and request.method == 'DELETE':
                        return True
            except:
                pass
            
            # Fédération
            try:
                from competitions.models import Federation, FederationRole
                federation_ids = []
                # Récupérer les fédérations dont l'utilisateur est membre
                federation_roles = FederationRole.objects.filter(user=user)
                for role in federation_roles:
                    federation_ids.append(role.federation.id)
                
                # Vérifier si le document est partagé avec l'une de ces fédérations
                federation_content_type = ContentType.objects.get_for_model(Federation)
                federation_shares = DocumentShare.objects.filter(
                    document=obj,
                    group_content_type=federation_content_type,
                    group_object_id__in=federation_ids
                )
                
                if federation_shares.exists():
                    share = federation_shares.first()
                    if request.method in permissions.SAFE_METHODS:
                        return True
                    elif share.access_level in ['W', 'F'] and request.method in ['PUT', 'PATCH']:
                        return True
                    elif share.access_level == 'F' and request.method == 'DELETE':
                        return True
            except:
                pass
            
            # Groupes Django
            try:
                from django.contrib.auth.models import Group
                group_ids = user.groups.values_list('id', flat=True)
                
                # Vérifier si le document est partagé avec l'un de ces groupes
                group_content_type = ContentType.objects.get_for_model(Group)
                group_shares = DocumentShare.objects.filter(
                    document=obj,
                    group_content_type=group_content_type,
                    group_object_id__in=group_ids
                )
                
                if group_shares.exists():
                    share = group_shares.first()
                    if request.method in permissions.SAFE_METHODS:
                        return True
                    elif share.access_level in ['W', 'F'] and request.method in ['PUT', 'PATCH']:
                        return True
                    elif share.access_level == 'F' and request.method == 'DELETE':
                        return True
            except:
                pass
            
        except Exception as e:
            # En cas d'erreur, nier l'accès par sécurité
            return False
        
        # Par défaut, refuser l'accès
        return False


class HasFolderPermission(permissions.BasePermission):
    """
    Permission qui vérifie si un utilisateur a accès à un dossier spécifique.
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Les administrateurs ont toujours accès
        if user.is_superuser or user.is_staff:
            return True
        
        # Le propriétaire a toujours accès
        if obj.owner == user:
            return True
        
        # Les dossiers publics sont accessibles en lecture
        if obj.is_public and request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier les accès selon le rôle de l'utilisateur
        try:
            # Si l'utilisateur est un administrateur de fédération
            if obj.visible_to_federations:
                from competitions.models import FederationRole
                fed_roles = FederationRole.objects.filter(user=user, role='admin')
                if fed_roles.exists():
                    return request.method in permissions.SAFE_METHODS
            
            # Si l'utilisateur est un administrateur de club
            if obj.visible_to_clubs:
                from competitions.models import ClubRole
                club_roles = ClubRole.objects.filter(user=user, role='admin')
                if club_roles.exists():
                    return request.method in permissions.SAFE_METHODS
            
            # Si l'utilisateur est un pratiquant
            if obj.visible_to_practitioners:
                from competitions.models import Practitioner
                is_practitioner = Practitioner.objects.filter(user=user).exists()
                if is_practitioner:
                    return request.method in permissions.SAFE_METHODS
            
            # Si l'utilisateur est un juge/arbitre
            if obj.visible_to_judges:
                from competitions.models import Judge
                is_judge = Judge.objects.filter(user=user).exists()
                if is_judge:
                    return request.method in permissions.SAFE_METHODS
        except:
            pass
        
        # Par défaut, refuser l'accès
        return False


class CanViewDocumentLogs(permissions.BasePermission):
    """
    Permission qui permet uniquement aux administrateurs et aux propriétaires de voir les logs d'accès.
    """
    def has_permission(self, request, view):
        user = request.user
        
        # Les administrateurs ont toujours accès
        if user.is_superuser or user.is_staff:
            return True
        
        # Pour les autres utilisateurs, l'accès dépend du document spécifique
        # Vérifié dans has_object_permission
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Les administrateurs ont toujours accès
        if user.is_superuser or user.is_staff:
            return True
        
        # Le propriétaire du document peut voir les logs
        return obj.document.created_by == user