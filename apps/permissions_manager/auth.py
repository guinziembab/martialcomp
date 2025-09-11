# permissions_manager/auth.py

from django.contrib.contenttypes.models import ContentType
from .models import Permission, Role, UserRoleAssignment

def user_has_permission(user, permission_code, context=None):
    """
    Vérifie si un utilisateur a une permission spécifique dans un contexte donné

    Args:
        user: L'utilisateur Ã  vérifier
        permission_code: Le code de la permission Ã  vérifier
        context: L'objet de contexte (federation, club, competition, etc.)
                Si None, vérifie uniquement les permissions globales

    Returns:
        Boolean: True si l'utilisateur a la permission, False sinon
    """
    # Superuser a toutes les permissions
    if user.is_superuser:
        return True

    # Construire le filtre de base
    query_filter = {
        'user': user,
        'is_active': True,
        'role__permissions__code': permission_code,
    }

    # Ajouter le contexte si spécifié
    if context:
        content_type = ContentType.objects.get_for_model(context)
        query_filter.update({
            'content_type': content_type,
            'object_id': context.id,
        })
    else:
        # Pour les permissions globales, le content_type et l'object_id sont None
        query_filter.update({
            'content_type__isnull': True,
            'object_id__isnull': True,
        })

    # Vérifier si l'attribution existe
    return UserRoleAssignment.objects.filter(**query_filter).exists()

def get_user_permissions(user, context=None):
    """
    Retourne toutes les permissions d'un utilisateur dans un contexte donné

    Args:
        user: L'utilisateur
        context: L'objet de contexte (facultatif)

    Returns:
        QuerySet: Liste des objets Permission
    """
    # Construire le filtre de base
    query_filter = {
        'user': user,
        'is_active': True,
    }

    # Ajouter le contexte si spécifié
    if context:
        content_type = ContentType.objects.get_for_model(context)
        query_filter.update({
            'content_type': content_type,
            'object_id': context.id,
        })

    # Récupérer les attributions de rÃ´les
    assignments = UserRoleAssignment.objects.filter(**query_filter)

    # Récupérer toutes les permissions associées Ã  ces rÃ´les
    from django.db.models import Q
    permission_filter = Q(roles__assignments__in=assignments)

    # Ajouter les permissions globales si on est dans un contexte spécifique
    if context:
        global_assignments = UserRoleAssignment.objects.filter(
            user=user,
            is_active=True,
            content_type__isnull=True,
            object_id__isnull=True,
        )
        permission_filter |= Q(roles__assignments__in=global_assignments)

    return Permission.objects.filter(permission_filter).distinct()

def get_user_roles(user, context=None):
    """
    Retourne tous les rÃ´les d'un utilisateur dans un contexte donné

    Args:
        user: L'utilisateur
        context: L'objet de contexte (facultatif)

    Returns:
        QuerySet: Liste des objets Role
    """
    query_filter = {
        'assignments__user': user,
        'assignments__is_active': True,
    }

    if context:
        content_type = ContentType.objects.get_for_model(context)
        query_filter.update({
            'assignments__content_type': content_type,
            'assignments__object_id': context.id,
        })
    else:
        query_filter.update({
            'assignments__content_type__isnull': True,
            'assignments__object_id__isnull': True,
        })

    return Role.objects.filter(**query_filter).distinct()
