"""
Configuration Django pour MartialComp - PRODUCTION IONOS VPS
Basé sur le guide de déploiement Ionos VPS
Domain: martialcomp.com
IP: 212.227.78.104
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Import des settings de base
from .settings import *

# ================================
# CONFIGURATION DE BASE PRODUCTION
# ================================

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'martialcomp.com,www.martialcomp.com,212.227.78.104').split(',')

# Secret key depuis les variables d'environnement (CRITIQUE)
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY doit être définie dans les variables d'environnement")

# ================================
# BASE DE DONNÉES POSTGRESQL
# ================================

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.getenv('DB_NAME', 'martialcomp_db'),
        'USER': os.getenv('DB_USER', 'martialcomp_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 20,
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 600,
    }
}

# ================================
# CACHE REDIS (OPTIONNEL)
# ================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'martialcomp',
        'TIMEOUT': 300,
    }
}

# Configuration du cache pour les sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ================================
# SÉCURITÉ PRODUCTION
# ================================

# Configuration CSRF pour production
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://martialcomp.com,https://www.martialcomp.com').split(',')
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'True').lower() == 'true'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# HTTPS et SSL
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = os.getenv('SECURE_BROWSER_XSS_FILTER', 'True').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = os.getenv('SECURE_CONTENT_TYPE_NOSNIFF', 'True').lower() == 'true'
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'True').lower() == 'true'

# Cookies sécurisés
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 heures

# Headers de sécurité
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'SAMEORIGIN')

# ================================
# FICHIERS STATIQUES ET MÉDIA
# ================================

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/staticfiles/'

MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/media/'

# Configuration pour les fichiers uploadés
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# ================================
# EMAIL CONFIGURATION
# ================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Configuration pour les erreurs 500
ADMINS = [
    ('Admin MartialComp', os.environ.get('ADMIN_EMAIL', 'admin@martialcomp.com')),
]
MANAGERS = ADMINS

# ================================
# LOGGING CONFIGURATION
# ================================

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
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/www/vhosts/martialcomp.com/logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/www/vhosts/martialcomp.com/logs/django_error.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'competitions': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'shop': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'multitenant': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ================================
# PERFORMANCES
# ================================

# Compression des réponses
USE_GZIP = True

# Optimisation des requêtes
CONN_MAX_AGE = 60

# Templates en cache
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# ================================
# CONFIGURATION SPÉCIFIQUE MARTIALCOMP
# ================================

# URL du site pour les emails et liens absolus
SITE_URL = 'https://martialcomp.com'

# Configuration Multi-tenant pour production
MULTITENANT_ENABLED = True
TENANT_DOMAIN_MODEL = 'multitenant.Tenant'

# Taille maximale pour les logos et images
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Configuration de la boutique
SHOP_ENABLED = True
SHOP_ALLOW_GUEST_CHECKOUT = True

# Configuration des QR codes
QR_CODE_CACHE_TIMEOUT = 3600  # 1 heure

# ================================
# INTÉGRATIONS EXTERNES
# ================================

# Configuration pour les APIs externes (si nécessaire)
EXTERNAL_API_TIMEOUT = 30

# Configuration de sauvegarde automatique
BACKUP_ENABLED = True
BACKUP_RETENTION_DAYS = 30

# ================================
# MONITORING ET MÉTRIQUES
# ================================

# Désactiver la collecte de métriques inutiles en production
SILKY_ENABLED = False

# Configuration pour les erreurs 404
SEND_BROKEN_LINK_EMAILS = True

# ================================
# CONFIGURATION RÉGIONALE
# ================================

# Configuration pour la France (timezone principal)
TIME_ZONE = 'Europe/Paris'
USE_TZ = True

# Configuration de la locale
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# ================================
# VARIABLES D'ENVIRONNEMENT REQUISES
# ================================

# Vérification des variables critiques
REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DB_PASSWORD',
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD',
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Variables d'environnement manquantes: {', '.join(missing_vars)}")

# ================================
# CONFIGURATION CORS (si API utilisée)
# ================================

if 'corsheaders' in INSTALLED_APPS:
    CORS_ALLOWED_ORIGINS = [
        "https://martialcomp.com",
        "https://www.martialcomp.com",
    ]
    CORS_ALLOW_CREDENTIALS = True

print("✅ Configuration de production chargée pour martialcomp.com")