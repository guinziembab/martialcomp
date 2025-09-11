"""
Fonctions de verification de permissions avec cache
"""

from django.core.cache import cache
from django.contrib.auth import get_user_model
from .auth import user_has_permission as original_user_has_permission
from .auth import get_user_permissions as original_get_user_permissions

User = get_user_model()

class PermissionCache:
    """Gestionnaire de cache pour les permissions"""
    
    def __init__(self):
        self.cache_prefix = 'perm_cache'
        self.default_ttl = 300  # 5 minutes
    
    def get_cache_key(self, user_id, permission_code, context_type=None, context_id=None):
        """Genere une cle de cache pour une permission"""
        key_parts = [self.cache_prefix, str(user_id), permission_code]
        
        if context_type:
            key_parts.append(context_type)
        if context_id:
            key_parts.append(str(context_id))
        
        return ':'.join(key_parts)
    
    def get(self, user_id, permission_code, context_type=None, context_id=None):
        """Recupere une permission depuis le cache"""
        cache_key = self.get_cache_key(user_id, permission_code, context_type, context_id)
        return cache.get(cache_key)
    
    def set(self, user_id, permission_code, has_permission, context_type=None, context_id=None, ttl=None):
        """Met en cache une permission"""
        cache_key = self.get_cache_key(user_id, permission_code, context_type, context_id)
        ttl = ttl or self.default_ttl
        cache.set(cache_key, has_permission, ttl)
    
    def invalidate_user(self, user_id):
        """Invalide toutes les permissions d'un utilisateur"""
        try:
            pattern = f"{self.cache_prefix}:{user_id}:*"
            if hasattr(cache, 'keys'):  # Redis
                keys = cache.keys(pattern)
                for key in keys:
                    cache.delete(key)
        except Exception:
            pass

# Instance globale du cache
permission_cache = PermissionCache()

def user_has_permission(user, permission_code, context_type=None, context_id=None):
    """
    Verifie si un utilisateur a une permission (avec cache)
    """
    if not user or not user.is_authenticated:
        return False
    
    # Verifier le cache d'abord
    cached_result = permission_cache.get(user.id, permission_code, context_type, context_id)
    
    if cached_result is not None:
        return cached_result
    
    # Si pas en cache, calculer la permission
    has_permission = original_user_has_permission(user, permission_code, context_type, context_id)
    
    # Mettre en cache le resultat
    permission_cache.set(user.id, permission_code, has_permission, context_type, context_id)
    
    return has_permission

def get_user_permissions(user, context_type=None, context_id=None):
    """
    Recupere toutes les permissions d'un utilisateur (avec cache)
    """
    if not user or not user.is_authenticated:
        return []
    
    cache_key = f"user_perms:{user.id}:{context_type}:{context_id}"
    cached_permissions = cache.get(cache_key)
    
    if cached_permissions is not None:
        return cached_permissions
    
    # Calculer les permissions
    permissions = original_get_user_permissions(user, context_type, context_id)
    
    # Mettre en cache
    cache.set(cache_key, permissions, permission_cache.default_ttl)
    
    return permissions

def invalidate_user_permissions(user_id):
    """
    Invalide toutes les permissions d'un utilisateur
    """
    permission_cache.invalidate_user(user_id)
