# config/settings/development.py
import os
from pathlib import Path
from .base import *

# RÃ©cupÃ©rer le chemin de base depuis base.py
# BASE_DIR est dÃ©jÃ  dÃ©fini dans base.py, mais nous le redÃ©finissons ici pour plus de sÃ©curitÃ©
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Base de donnÃ©es PostgreSQL (alignÃ©e avec la production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'martialcomp_dev'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Cache Configuration (Local memory instead of Redis for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session Configuration - Using database instead of Redis for development
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Security Settings for Development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Allow JS access for development

# CSRF Configuration for Development
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000', 
    'http://localhost:8000',
    'http://127.0.0.1:3000',  # Pour le frontend React si utilisÃ©
    'http://localhost:3000'
]

# Configuration CSRF simplifiÃ©e pour le debug
CSRF_USE_SESSIONS = False  # False pour utiliser les cookies
CSRF_COOKIE_SAMESITE = 'Lax'  # Plus permissif que 'Strict' 
CSRF_COOKIE_AGE = None  # Pas d'expiration - utilisera l'expiration de session par dÃ©faut
# CSRF_FAILURE_VIEW = 'competitions.views.csrf_failure'  # DÃ©sactivÃ© temporairement pour debug

# Email Configuration for Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# URL de base pour la gÃ©nÃ©ration des QR codes et liens absolus
BASE_URL = 'http://127.0.0.1:8000'

# CORRECTION: Configuration des redirections pour django-allauth
# CORRECTION: URL de redirection avec le chemin complet incluant /competitions/
LOGIN_REDIRECT_URL = '/competitions/dashboard/'  # URL complÃ¨te avec le prÃ©fixe
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/dashboard/'  # SpÃ©cifique Ã  django-allauth
ACCOUNT_SIGNUP_REDIRECT_URL = '/competitions/onboarding/role/'  # SpÃ©cifique Ã  django-allauth
LOGOUT_REDIRECT_URL = '/fr/'  # On garde la redirection de dÃ©connexion vers la page d'accueil

# Configuration django-allauth
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Ne pas bloquer l'utilisateur en attente de vÃ©rification
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True  # Connecter automatiquement aprÃ¨s confirmation email
ACCOUNT_USERNAME_REQUIRED = True  # Exiger un nom d'utilisateur

# Debug Toolbar pour faciliter le dÃ©veloppement
if DEBUG:
    # Django Debug Toolbar - seulement en mode DEBUG
    try:
        import debug_toolbar
        if 'debug_toolbar' not in INSTALLED_APPS:
            INSTALLED_APPS += ['debug_toolbar']
        if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
            # Ajouter le middleware au dÃ©but ou avant CommonMiddleware
            middleware_index = MIDDLEWARE.index('django.middleware.common.CommonMiddleware') if 'django.middleware.common.CommonMiddleware' in MIDDLEWARE else 0
            MIDDLEWARE.insert(middleware_index, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        # Configuration de Debug Toolbar
        INTERNAL_IPS = ['127.0.0.1', 'localhost']
    except ImportError:
        pass

# Development-specific logging
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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django-dev.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # Changer en 'DEBUG' pour voir les requÃªtes SQL
            'propagate': False,
        },
        'competitions': {  # Ajout d'un logger spÃ©cifique pour l'application competitions
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# CrÃ©er le rÃ©pertoire de logs s'il n'existe pas
import os
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

LOGIN_URL = '/accounts/login/'
