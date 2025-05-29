"""
Configuration de développement - Cache sans Redis
"""
# Importer tout des settings de base
from .settings import *

# REMPLACER la configuration du cache pour éviter Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
    'session': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'session_cache_table',
    }
}

# Session configuration avec le cache DB au lieu de Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'

# Afficher toutes les erreurs en développement
DEBUG = True

# Désactiver la sécurité stricte pour le développement
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email backend pour le développement
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Enlever le cache middleware qui peut causer des problèmes sans Redis
MIDDLEWARE = list(MIDDLEWARE)
if 'multitenant.cache.TenantCacheMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('multitenant.cache.TenantCacheMiddleware')