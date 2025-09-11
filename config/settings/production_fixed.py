# config/settings/production.py
import os
from pathlib import Path
from .base import *

# Récupérer le chemin de base depuis base.py
# BASE_DIR est déjà défini dans base.py, mais nous le redéfinissons ici pour plus de sécurité
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['martialcomp.com', 'www.martialcomp.com', '212.227.78.104', '127.0.0.1', 'localhost', '*']

# Base de données PostgreSQL pour production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'martialcomp_user',
        'PASSWORD': 'AQWZSX123ok,',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Cache Configuration (désactivé pour éviter les problèmes Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Session Configuration - Using database for production
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Security Settings for Production - DÉSACTIVÉS POUR LES TESTS HTTP
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = False  # DÉSACTIVÉ pour HTTP
CSRF_COOKIE_SECURE = False     # DÉSACTIVÉ pour HTTP
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Permettre l'accès JavaScript pour le rafraîchissement automatique

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
# HSTS désactivé pour les tests HTTP
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# CSRF Configuration for Production
CSRF_TRUSTED_ORIGINS = [
    'https://martialcomp.com',
    'https://www.martialcomp.com',
    'http://212.227.78.104:8080',
    'http://127.0.0.1:8080',
    'http://localhost:8080',
]

# Configuration CSRF pour production
CSRF_USE_SESSIONS = False  # False pour utiliser les cookies
CSRF_COOKIE_SAMESITE = 'Lax'  # Plus permissif que 'Strict'
CSRF_COOKIE_AGE = None  # Pas d'expiration - utilisera l'expiration de session par défaut

# Email Configuration for Production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com')

# URL de base pour la génération des QR codes et liens absolus
BASE_URL = 'https://martialcomp.com'

# Configuration des redirections pour django-allauth
LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'  # URL complète avec le préfixe
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'  # Spécifique à django-allauth
ACCOUNT_SIGNUP_REDIRECT_URL = '/competitions/onboarding/role/'  # Spécifique à django-allauth
LOGOUT_REDIRECT_URL = '/fr/'  # On garde la redirection de déconnexion vers la page d'accueil

# Configuration django-allauth
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Vérification obligatoire en production
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True  # Connecter automatiquement après confirmation email
ACCOUNT_USERNAME_REQUIRED = True  # Exiger un nom d'utilisateur

# Production-specific logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/tmp/django_errors.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'ERROR',  # Seulement les erreurs en production
            'propagate': False,
        },
        'competitions': {  # Logger spécifique pour l'application competitions
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
} 