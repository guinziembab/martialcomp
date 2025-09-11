"""
Utilitaires pour la gestion des organisations
"""

from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

def get_user_organization(user):
    """
    Retourne l'organisation de l'utilisateur connecte
    Utilise le cache pour optimiser les performances
    """
    if not user or not user.is_authenticated:
        return None
    
    # Verifier le cache
    cache_key = f'user_org_{user.id}'
    cached_org = cache.get(cache_key)
    if cached_org is not None:
        return cached_org
    
    try:
        # Essayer d'abord via UserProfile
        from apps.competitions.models.users import UserProfile
        profile = UserProfile.objects.get(user=user)
        if profile.organization:
            cache.set(cache_key, profile.organization, 300)  # Cache 5 minutes
            return profile.organization
    except (ImportError, UserProfile.DoesNotExist):
        pass
    
    try:
        # Essayer via OrganizationMember
        from apps.organizations.models import OrganizationMember
        member = OrganizationMember.objects.filter(user=user).first()
        if member and member.organization:
            cache.set(cache_key, member.organization, 300)
            return member.organization
    except ImportError:
        pass
    
    return None

def get_user_organizations(user):
    """
    Retourne toutes les organisations de l'utilisateur
    """
    if not user or not user.is_authenticated:
        return []
    
    try:
        from apps.organizations.models import OrganizationMember
        return [member.organization for member in OrganizationMember.objects.filter(user=user)]
    except ImportError:
        return []

def check_organization_access(user, organization):
    """
    Verifie si l'utilisateur a acces a l'organisation
    """
    if not user or not user.is_authenticated or not organization:
        return False
    
    user_org = get_user_organization(user)
    return user_org == organization
