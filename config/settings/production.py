"""
Configuration de production pour MartialComp
Paramètres optimisés pour la sécurité et les performances
"""

import os
from pathlib import Path
from decouple import config
from .base import *

# BASE_DIR déjà défini dans base.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-secret-key-here-change-in-production')

# Configuration de sécurité
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Configuration Cloudflare
USE_TZ = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Configuration HTTPS
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Permet l'iframe depuis le même domaine (aperçu du site)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Configuration CSRF pour production
# Note: Django ne supporte pas les wildcards dans CSRF_TRUSTED_ORIGINS
# Ajouter explicitement tous les domaines nécessaires
CSRF_TRUSTED_ORIGINS = [
    'https://martialcomp.com',
    'https://www.martialcomp.com',
]
# Ajouter des origines supplémentaires depuis les variables d'environnement si nécessaire
csrf_origins_env = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if csrf_origins_env:
    CSRF_TRUSTED_ORIGINS.extend([origin.strip() for origin in csrf_origins_env.split(',') if origin.strip()])

CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = False  # Utiliser les cookies CSRF

# Configuration de la base de données de production
# Utiliser les mêmes paramètres que le développement si les variables d'environnement ne sont pas définies
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'martialcomp'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',  # Plus permissif que 'require'
        },
    }
}

# Configuration Redis pour la production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'martialcomp_prod',
        'TIMEOUT': 300,
    }
}

# Configuration des sessions avec Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 heure
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Configuration pour les permissions
PERMISSION_CACHE_ENABLED = True
PERMISSION_CACHE_TTL = 300  # 5 minutes

# Configuration des logs
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
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/martialcomp.log',
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
        'apps.organizations': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.permissions_manager': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuration des fichiers statiques et média (Plesk + Cloudflare)
STATIC_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/static/'
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Configuration des fichiers média
MEDIA_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/media/'
MEDIA_URL = '/media/'

# Configuration du cache des templates pour la production
TEMPLATES[0]['APP_DIRS'] = False  # Désactiver app_dirs
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Configuration des middlewares de sécurité
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'corsheaders.middleware.CorsMiddleware',  # DÉSACTIVÉ: Cloudflare gère CORS (duplication si activé)
    # 'apps.core.middleware.block_practitioner.BlockPractitionerMiddleware',  # DÉSACTIVÉ: Plus nécessaire
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # AJOUTÉ : Middleware de localisation manquant
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # AJOUTÉ : Middleware Allauth manquant
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.permissions_manager.middleware.PermissionsMiddleware',
]

# ================================================================
# CONFIGURATION DES EMAILS - POSTFIX LOCAL PLESK
# ================================================================
# Option 1: Postfix local (recommandé pour Plesk/IONOS)
# Le serveur Postfix de Plesk gère l'envoi sans authentification depuis localhost
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Utiliser le Postfix local de Plesk par défaut, ou IONOS SMTP si configuré
_email_host = os.environ.get('EMAIL_HOST', 'localhost')
if _email_host == 'localhost':
    # Configuration Postfix local (pas d'authentification nécessaire)
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 25
    EMAIL_USE_TLS = False
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
else:
    # Configuration IONOS SMTP externe
    EMAIL_HOST = _email_host
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

EMAIL_TIMEOUT = 30  # Timeout en secondes

# Adresses email par défaut
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'MartialComp <noreply@martialcomp.com>')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', 'noreply@martialcomp.com')

# Emails de service
ACCOUNTING_EMAIL = os.environ.get('ACCOUNTING_EMAIL', 'finance@martialcomp.com')
CUSTOMER_SERVICE_EMAIL = os.environ.get('CUSTOMER_SERVICE_EMAIL', 'support@martialcomp.com')
SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL', 'support@martialcomp.com')

# Administrateurs pour les notifications d'erreurs
ADMINS = [
    ('MartialComp Admin', os.environ.get('ADMIN_EMAIL', 'admin@martialcomp.com')),
]
MANAGERS = ADMINS

# URL du site pour les liens dans les emails
SITE_URL = os.environ.get('SITE_URL', 'https://martialcomp.com')

# Configuration de la sécurité des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configuration des sessions
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Configuration des performances
CONN_MAX_AGE = 60  # Connexions DB persistantes
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB max pour les uploads

# Configuration des applications tierces
if 'sentry' in INSTALLED_APPS:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN', ''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True,
    )

# Configuration du monitoring
if 'django_prometheus' in INSTALLED_APPS:
    MIDDLEWARE.insert(0, 'django_prometheus.middleware.PrometheusBeforeMiddleware')
    MIDDLEWARE.append('django_prometheus.middleware.PrometheusAfterMiddleware')

# Configuration des CORS pour application mobile
cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]

# Ajouter les origins par défaut pour mobile si non définies
if not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        'https://martialcomp.com',
        'https://www.martialcomp.com',
        'https://api.martialcomp.com',
    ]

# Pour les apps Expo/React Native en développement/preview
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^exp://.*$",  # Expo Go app
    r"^https://.*\.expo\.dev$",  # Expo web builds
]

CORS_ALLOW_CREDENTIALS = True

# Autoriser localhost pour le développement mobile
CORS_ALLOWED_ORIGINS += ["http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:19006"]

# Headers autorisés pour les requêtes mobiles
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-tenant-id',
    'x-device-id',
    'x-app-version',
    'cache-control',
    'pragma',
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_EXPOSE_HEADERS = [
    'content-disposition',
    'x-request-id',
]

# Optimiser les preflight requests (OPTIONS) pour l'app mobile
CORS_PREFLIGHT_MAX_AGE = 86400  # 24 heures de cache pour les OPTIONS requests

# Configuration des domaines autorisés pour les emails
ALLOWED_EMAIL_DOMAINS = os.environ.get('ALLOWED_EMAIL_DOMAINS', '').split(',')

# Configuration des backups automatiques
BACKUP_ENABLED = True
BACKUP_RETENTION_DAYS = 30
BACKUP_PATH = '/var/backups/martialcomp/'

# Configuration du monitoring des performances
PERFORMANCE_MONITORING = {
    'enabled': True,
    'slow_query_threshold': 1.0,  # secondes
    'cache_hit_ratio_threshold': 0.8,
    'memory_usage_threshold': 0.9,
}

# Configuration de la sécurité des API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT pour mobile
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',      # Augmenté de 100 à 1000 pour éviter le blocage
        'user': '10000/hour',     # Augmenté de 1000 à 10000 pour l'app mobile
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Configuration des tests en production
if os.environ.get('RUNNING_TESTS'):
    # Désactiver certaines fonctionnalités pendant les tests
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# URGENT FIX - Désactiver practitioner admin après chargement des apps
try:
    import apps.competitions.admin_override
except Exception as e:
    print(f"⚠️ Impossible de charger admin_override: {e}")

print("✅ Configuration de production chargée")