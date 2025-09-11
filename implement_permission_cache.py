#!/usr/bin/env python3
"""
Implementation d'un systeme de cache pour les permissions
Utilise Redis pour optimiser les verifications de permissions
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class PermissionCacheManager:
    """Gestionnaire de cache pour les permissions"""
    
    def __init__(self):
        self.cache_prefix = 'perm_cache'
        self.default_ttl = 300  # 5 minutes par defaut
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_sets': 0,
            'cache_invalidations': 0
        }
    
    def get_cache_key(self, user_id, permission_code, context_type=None, context_id=None):
        """Genere une cle de cache pour une permission"""
        key_parts = [self.cache_prefix, str(user_id), permission_code]
        
        if context_type:
            key_parts.append(context_type)
        if context_id:
            key_parts.append(str(context_id))
        
        return ':'.join(key_parts)
    
    def get_cached_permission(self, user_id, permission_code, context_type=None, context_id=None):
        """Recupere une permission depuis le cache"""
        cache_key = self.get_cache_key(user_id, permission_code, context_type, context_id)
        result = cache.get(cache_key)
        
        if result is not None:
            self.stats['cache_hits'] += 1
            return result
        else:
            self.stats['cache_misses'] += 1
            return None
    
    def set_cached_permission(self, user_id, permission_code, has_permission, context_type=None, context_id=None, ttl=None):
        """Met en cache une permission"""
        cache_key = self.get_cache_key(user_id, permission_code, context_type, context_id)
        ttl = ttl or self.default_ttl
        
        cache.set(cache_key, has_permission, ttl)
        self.stats['cache_sets'] += 1
    
    def invalidate_user_permissions(self, user_id):
        """Invalide toutes les permissions d'un utilisateur"""
        try:
            # Pattern pour trouver toutes les cles de cache de l'utilisateur
            pattern = f"{self.cache_prefix}:{user_id}:*"
            
            # Pour Redis, on peut utiliser SCAN pour trouver les cles
            # Pour le cache Django standard, on utilise une approche differente
            if hasattr(cache, 'keys'):  # Redis
                keys = cache.keys(pattern)
                for key in keys:
                    cache.delete(key)
            else:
                # Pour le cache local, on ne peut pas faire de pattern matching
                # On invalide manuellement les permissions connues
                self._invalidate_known_permissions(user_id)
            
            self.stats['cache_invalidations'] += 1
            print(f"   Permissions invalidees pour l'utilisateur {user_id}")
            
        except Exception as e:
            print(f"Erreur lors de l'invalidation des permissions: {e}")
    
    def _invalidate_known_permissions(self, user_id):
        """Invalide les permissions connues pour un utilisateur"""
        # Liste des permissions communes a invalider
        common_permissions = [
            'view_organization',
            'edit_organization',
            'manage_members',
            'view_competitions',
            'manage_competitions',
            'view_finances',
            'manage_finances',
        ]
        
        context_types = ['global', 'federation', 'club', 'competition']
        
        for perm in common_permissions:
            for context in context_types:
                cache_key = self.get_cache_key(user_id, perm, context)
                cache.delete(cache_key)
    
    def get_cache_stats(self):
        """Retourne les statistiques du cache"""
        return self.stats.copy()
    
    def reset_cache_stats(self):
        """Remet a zero les statistiques"""
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_sets': 0,
            'cache_invalidations': 0
        }

class CachedPermissionChecker:
    """Verificateur de permissions avec cache"""
    
    def __init__(self):
        self.cache_manager = PermissionCacheManager()
    
    def user_has_permission(self, user, permission_code, context_type=None, context_id=None):
        """Verifie si un utilisateur a une permission (avec cache)"""
        if not user or not user.is_authenticated:
            return False
        
        # Verifier le cache d'abord
        cached_result = self.cache_manager.get_cached_permission(
            user.id, permission_code, context_type, context_id
        )
        
        if cached_result is not None:
            return cached_result
        
        # Si pas en cache, calculer la permission
        has_permission = self._calculate_permission(user, permission_code, context_type, context_id)
        
        # Mettre en cache le resultat
        self.cache_manager.set_cached_permission(
            user.id, permission_code, has_permission, context_type, context_id
        )
        
        return has_permission
    
    def _calculate_permission(self, user, permission_code, context_type=None, context_id=None):
        """Calcule une permission sans cache"""
        try:
            # Importer les fonctions de permission existantes
            from apps.permissions_manager.auth import user_has_permission as original_checker
            
            # Utiliser la fonction originale
            return original_checker(user, permission_code, context_type, context_id)
            
        except ImportError:
            # Fallback: logique de permission simplifiee
            return self._fallback_permission_check(user, permission_code, context_type, context_id)
    
    def _fallback_permission_check(self, user, permission_code, context_type=None, context_id=None):
        """Verification de permission de fallback"""
        try:
            # Verifier via UserProfile
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=user)
            
            # Permissions de base selon le role
            role_permissions = {
                'club_manager': ['view_organization', 'edit_organization', 'manage_members', 'view_competitions', 'manage_competitions'],
                'federation_admin': ['view_organization', 'edit_organization', 'manage_members', 'view_competitions', 'manage_competitions', 'view_finances', 'manage_finances'],
                'participant': ['view_organization', 'view_competitions'],
            }
            
            user_permissions = role_permissions.get(profile.role, [])
            return permission_code in user_permissions
            
        except (ImportError, UserProfile.DoesNotExist):
            return False
    
    def get_user_permissions(self, user, context_type=None, context_id=None):
        """Recupere toutes les permissions d'un utilisateur (avec cache)"""
        if not user or not user.is_authenticated:
            return []
        
        cache_key = f"user_perms:{user.id}:{context_type}:{context_id}"
        cached_permissions = cache.get(cache_key)
        
        if cached_permissions is not None:
            self.cache_manager.stats['cache_hits'] += 1
            return cached_permissions
        
        # Calculer les permissions
        try:
            from apps.permissions_manager.auth import get_user_permissions as original_getter
            permissions = original_getter(user, context_type, context_id)
        except ImportError:
            permissions = self._fallback_get_permissions(user, context_type, context_id)
        
        # Mettre en cache
        cache.set(cache_key, permissions, self.cache_manager.default_ttl)
        self.cache_manager.stats['cache_sets'] += 1
        
        return permissions
    
    def _fallback_get_permissions(self, user, context_type=None, context_id=None):
        """Recuperation de permissions de fallback"""
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.get(user=user)
            
            role_permissions = {
                'club_manager': ['view_organization', 'edit_organization', 'manage_members', 'view_competitions', 'manage_competitions'],
                'federation_admin': ['view_organization', 'edit_organization', 'manage_members', 'view_competitions', 'manage_competitions', 'view_finances', 'manage_finances'],
                'participant': ['view_organization', 'view_competitions'],
            }
            
            return role_permissions.get(profile.role, [])
            
        except (ImportError, UserProfile.DoesNotExist):
            return []

class PermissionCacheImplementation:
    """Implementation complete du systeme de cache des permissions"""
    
    def __init__(self):
        self.checker = CachedPermissionChecker()
        self.cache_manager = self.checker.cache_manager
    
    def create_permission_utils(self):
        """Cree le fichier utils pour les permissions avec cache"""
        utils_path = 'apps/permissions_manager/cached_auth.py'
        
        if not os.path.exists(utils_path):
            os.makedirs(os.path.dirname(utils_path), exist_ok=True)
            
            utils_content = '''"""
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
'''
            
            with open(utils_path, 'w', encoding='utf-8') as f:
                f.write(utils_content)
            
            print(f"   Cree: {utils_path}")
    
    def update_settings_for_cache(self):
        """Met a jour les settings pour activer le cache Redis"""
        settings_path = 'config/settings/base.py'
        
        if not os.path.exists(settings_path):
            print(f"Fichier settings non trouve: {settings_path}")
            return
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Verifier si Redis est deja configure
            if 'redis' in content.lower():
                print("Redis deja configure dans les settings")
                return
            
            # Ajouter la configuration Redis
            redis_config = '''
# Cache Configuration avec Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'martialcomp',
        'TIMEOUT': 300,
    }
}

# Configuration pour les sessions avec Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Configuration pour les permissions
PERMISSION_CACHE_ENABLED = True
PERMISSION_CACHE_TTL = 300  # 5 minutes
'''
            
            # Insérer avant la fin du fichier
            if 'CACHES = {' not in content:
                # Ajouter avant la dernière ligne
                lines = content.split('\n')
                insert_index = len(lines) - 1
                lines.insert(insert_index, redis_config)
                content = '\n'.join(lines)
                
                with open(settings_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"   Mis a jour: {settings_path}")
            else:
                print("Configuration cache deja presente")
        
        except Exception as e:
            print(f"Erreur lors de la mise a jour des settings: {e}")
    
    def create_cache_middleware(self):
        """Cree un middleware pour invalider automatiquement le cache"""
        middleware_path = 'apps/permissions_manager/middleware.py'
        
        if not os.path.exists(middleware_path):
            os.makedirs(os.path.dirname(middleware_path), exist_ok=True)
            
            middleware_content = '''"""
Middleware pour la gestion du cache des permissions
"""

from django.core.cache import cache
from .cached_auth import invalidate_user_permissions

class PermissionCacheMiddleware:
    """
    Middleware pour invalider le cache des permissions
    lors de modifications des roles/permissions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Invalider le cache si l'utilisateur a ete modifie
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Verifier si les permissions ont ete modifiees
            if self._permissions_changed(request):
                invalidate_user_permissions(request.user.id)
        
        return response
    
    def _permissions_changed(self, request):
        """
        Detecte si les permissions ont ete modifiees
        """
        # Verifier les URLs qui modifient les permissions
        permission_urls = [
            '/admin/',
            '/api/permissions/',
            '/api/roles/',
            '/api/organizations/',
        ]
        
        return any(url in request.path for url in permission_urls)
'''
            
            with open(middleware_path, 'w', encoding='utf-8') as f:
                f.write(middleware_content)
            
            print(f"   Cree: {middleware_path}")
    
    def run_implementation(self):
        """Execute l'implementation complete du cache"""
        print("Implementation du systeme de cache des permissions...")
        
        # 1. Creer les utilitaires de cache
        print("\n1. Creation des utilitaires de cache...")
        self.create_permission_utils()
        
        # 2. Creer le middleware
        print("\n2. Creation du middleware de cache...")
        self.create_cache_middleware()
        
        # 3. Mettre a jour les settings
        print("\n3. Mise a jour des settings...")
        self.update_settings_for_cache()
        
        # 4. Tester le systeme
        print("\n4. Test du systeme de cache...")
        self.test_cache_system()
        
        print("\nImplementation terminee!")
        print("N'oubliez pas d'installer django-redis: pip install django-redis")
        print("Et de demarrer Redis: redis-server")
    
    def test_cache_system(self):
        """Teste le systeme de cache"""
        try:
            # Tester avec un utilisateur
            user = User.objects.filter(is_active=True).first()
            
            if user:
                print(f"Test avec l'utilisateur: {user.username}")
                
                # Test de verification de permission
                has_perm = self.checker.user_has_permission(user, 'view_organization')
                print(f"   Permission view_organization: {has_perm}")
                
                # Test de recuperation des permissions
                permissions = self.checker.get_user_permissions(user)
                print(f"   Permissions: {permissions}")
                
                # Afficher les statistiques
                stats = self.cache_manager.get_cache_stats()
                print(f"   Statistiques cache: {stats}")
            else:
                print("Aucun utilisateur trouve pour le test")
        
        except Exception as e:
            print(f"Erreur lors du test: {e}")

def main():
    """Fonction principale"""
    implementation = PermissionCacheImplementation()
    implementation.run_implementation()

if __name__ == "__main__":
    main()
