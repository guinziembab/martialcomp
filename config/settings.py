"""
Django settings for config project optimisé pour le déploiement sur Render.

Ce fichier contient les configurations optimisées pour l'environnement de production
tout en maintenant la compatibilité avec le développement local.
"""
import os
import dj_database_url
from pathlib import Path
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-tv=2g@wtxxfu^6trqra-ewp9%j2gm^x3_&y)vhlo%jj+r_+0dq')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Configuration des hôtes autorisés
ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    'testserver',
    'martialcomp.onrender.com',
    '.onrender.com',  # Accepte tous les sous-domaines de onrender.com
]

# Ajout des domaines de Render
if os.environ.get('RENDER_EXTERNAL_HOSTNAME'):
    ALLOWED_HOSTS.append(os.environ.get('RENDER_EXTERNAL_HOSTNAME'))

# Ajout explicite du domaine de l'application Render
ALLOWED_HOSTS.append('martialcomp.onrender.com')

# Si des hôtes supplémentaires sont spécifiés dans les variables d'environnement
if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS.extend(os.environ.get('ALLOWED_HOSTS').split(','))

# Configuration CSRF pour multi-tenant
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8001',
    'http://127.0.0.1:8001',
    'https://*.martialcomp.com',
    'https://*.onrender.com',  # Ajout des domaines Render
]

# Configuration des cookies pour multi-tenant
SESSION_COOKIE_DOMAIN = None  # None permet les cookies pour localhost
CSRF_COOKIE_DOMAIN = None     # None permet les cookies pour localhost

# Sécurité CSRF
CSRF_COOKIE_HTTPONLY = False  # False permet à JavaScript d'accéder au cookie CSRF
CSRF_COOKIE_SECURE = not DEBUG  # True en production
# Configuration CSRF standard
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_USE_SESSIONS = False  # Utiliser les cookies au lieu des sessions
CSRF_COOKIE_SAMESITE = 'Lax'  # Protection contre CSRF
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7 * 52  # 1 an

# Configuration du modèle de tarification
PAYMENT_PROVIDERS = {
    'stripe': {
        'api_key': os.environ.get('STRIPE_SECRET_KEY', 'sk_test_your_stripe_key'),
        'webhook_secret': os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_your_webhook_secret'),
        'public_key': os.environ.get('STRIPE_PUBLIC_KEY', 'pk_test_your_public_key'),
    },
    'paystack': {
        'api_key': os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_your_paystack_key'),
        'webhook_secret': os.environ.get('PAYSTACK_WEBHOOK_SECRET', 'your_paystack_webhook_secret'),
        'public_key': os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_your_public_key'),
    },
    'mercadopago': {
        'access_token': os.environ.get('MERCADOPAGO_ACCESS_TOKEN', 'TEST-your_mercadopago_token'),
        'public_key': os.environ.get('MERCADOPAGO_PUBLIC_KEY', 'TEST-your_mercadopago_public_key'),
    },
    'alipay': {
        'app_id': os.environ.get('ALIPAY_APP_ID', 'your_alipay_app_id'),
        'private_key': os.environ.get('ALIPAY_PRIVATE_KEY', 'your_alipay_private_key'),
        'public_key': os.environ.get('ALIPAY_PUBLIC_KEY', 'your_alipay_public_key'),
    },
}

# Mapping des régions vers les fournisseurs de paiement
PAYMENT_REGION_MAPPING = {
    'africa': 'paystack',
    'europe_west': 'stripe',
    'europe_east': 'stripe',
    'north_america': 'stripe',
    'south_america': 'mercadopago',
    'central_america': 'mercadopago',
    'asia_se': 'stripe',
    'asia_other': 'alipay',
    'middle_east': 'stripe',
    'oceania': 'stripe',
}


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Bibliothèques tierces
    'django_extensions',
    'widget_tweaks',
    'import_export',
    'rest_framework',
    'rest_framework_simplejwt',
    'oauth2_provider',
    'whitenoise.runserver_nostatic',  # Pour servir les fichiers statiques en production
    # Applications locales
    'competitions',
    'grades',
    'permissions_manager',
    'organizations',
    'finances',
    'shop',
    'documents',  # Gestion documentaire
    'multitenant',  # Module multi-tenant
    'api_auth',  # Application API pour l'authentification
    'security',  # Module de sécurité
    'family_management.apps.FamilyManagementConfig',  # Gestion familiale
]

MIDDLEWARE = [
    'config.allowed_hosts_override.AllowedHostsOverrideMiddleware',  # Ajoutez ce middleware en premier
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Pour servir les fichiers statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'security.middleware.SecurityMiddleware',  # Middleware de sécurité personnalisé
    'security.rate_limiting.RateLimitingMiddleware',  # Middleware de limitation de taux
    'competitions.utils.security.OrganizationIsolationMiddleware',  # Middleware d'isolation organisationnelle
    'multitenant.middleware.TenantMiddleware',  # Middleware multi-tenant
    'multitenant.cache.TenantCacheMiddleware',  # Cache multi-tenant
    'multitenant.resource_limits.ResourceTrackerMiddleware',  # Tracking des ressources
    'multitenant.middleware.FeatureAccessMiddleware',  # Contrôle d'accès aux fonctionnalités
    'api_auth.middleware.JWTTenantMiddleware',  # JWT Tenant middleware
    'api_auth.middleware.APIErrorHandlingMiddleware',  # API Error middleware
    'api_auth.middleware.APILoggingMiddleware',  # API Logging middleware
    'competitions.middleware.OnboardingMiddleware',
    'finances.middleware.FinancialAuditMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Processeurs de contexte standard Django
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                # Processeurs de contexte personnalisés
                'competitions.context_processors.url_checker',
                'competitions.context_processors.global_context',
                'competitions.context_processors.category_cache',
                'competitions.context_processors.language_context',
                # Processeurs de contexte pour les finances
                'finances.context_processors.financial_stats',
            ],
            'libraries': {
                # Bibliothèques de tags/filtres personnalisés
                'custom_filters': 'competitions.templatetags.custom_filters',
                'competition_tags': 'competitions.templatetags.competition_tags',
            },
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database - Configuration optimisée pour Render
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Utiliser la variable d'environnement DATABASE_URL de Render si disponible
# sinon fallback sur SQLite pour le développement
DATABASES = {
    'default': dj_database_url.config(
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3'),
        conn_max_age=600
    )
}

# Cache configuration - Adaptation pour Render
# Utiliser un cache mémoire en production car Redis n'est pas disponible par défaut sur Render
if DEBUG:
    # En développement, essayer d'utiliser Redis si disponible
    try:
        import django_redis
        CACHES = {
            'default': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': 'redis://127.0.0.1:6379/1',
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': 'martialcomp',
            },
            'session': {
                'BACKEND': 'django_redis.cache.RedisCache',
                'LOCATION': 'redis://127.0.0.1:6379/2',
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                },
                'KEY_PREFIX': 'session',
            },
        }
        # Session configuration avec Redis
        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
        SESSION_CACHE_ALIAS = 'session'
    except ImportError:
        # Fallback to local memory cache if Redis is not available
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
        # Session configuration avec base de données
        SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    # En production sur Render, utiliser le cache mémoire
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
    # Session configuration avec base de données
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_TZ = True

# Available languages
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('pt', 'Português'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]


# Static files (CSS, JavaScript, Images) - Configuration optimisée pour Render
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = []

# Ajouter le répertoire static s'il existe (évite l'avertissement W004)
static_dir = os.path.join(BASE_DIR, 'static')
if os.path.exists(static_dir):
    STATICFILES_DIRS.append(static_dir)

# Configuration de Whitenoise pour servir les fichiers statiques en production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files - Configuration pour Render
# En production, les fichiers média devraient être stockés sur un service cloud
# comme AWS S3, mais pour le déploiement initial sur Render, nous utilisons le système de fichiers local
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redirection après connexion
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/competitions/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Configuration des messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Configuration de la session
SESSION_COOKIE_AGE = 86400  # 24 heures en secondes
SESSION_COOKIE_SECURE = not DEBUG  # True en production avec HTTPS

# Configuration du logger adaptée pour Render
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'competitions': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'grades': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'organizations': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'finances': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuration de l'import-export
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Configuration spécifique à PostgreSQL
if 'postgresql' in DATABASES['default'].get('ENGINE', ''):
    try:
        # Test si psycopg2 est disponible avant d'ajouter postgres
        import psycopg2
        INSTALLED_APPS += ['django.contrib.postgres']
    except ImportError:
        pass
    
# Configuration du rate limiting
RATE_LIMIT_WINDOW_SIZE = 60  # Fenêtre de 60 secondes (1 minute)
RATE_LIMIT_MAX_REQUESTS = 100  # 100 requêtes par minute par IP
RATE_LIMIT_SENSITIVE_MAX_REQUESTS = 10  # 10 requêtes par minute pour les endpoints sensibles
RATE_LIMIT_SENSITIVE_PATHS = [
    '/login/',
    '/admin/login/',
    '/api/token/',
    '/api/auth/',
    '/password-reset/',
]
RATE_LIMIT_EXEMPT_IPS = ['127.0.0.1', '::1']  # IPs exemptées du rate limiting

# Cryptographie et Sécurité
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Configuration pour la nouvelle structure d'organisation
USE_NEW_ORGANIZATION_MODEL = True  # Activer la nouvelle structure d'organisation

# Configuration Email pour Render
if DEBUG:
    # En développement, utiliser le backend console
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    # En production, utiliser SMTP
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.sendgrid.net')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'apikey')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com')

# Gestion des fichiers média
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# Configurations spécifiques aux différentes applications
COMPETITION_SETTINGS = {
    'allow_multi_discipline': True,  # Permettre aux compétitions d'avoir plusieurs disciplines
    'require_medical_certificate': True,  # Exiger un certificat médical pour l'inscription
}

GRADE_SETTINGS = {
    'enable_automatic_promotion': False,  # Activer la promotion automatique des grades
    'show_history': True,  # Afficher l'historique des grades
}

# Import des paramètres du module finances
try:
    from .finance_settings import *
except ImportError:
    # Paramètres par défaut si le fichier n'existe pas
    FINANCE_SETTINGS = {
        'max_transaction_amount_without_validation': 5000,
        'transaction_validators_required': {'default': 1},
    }

# Paramètres de sécurité pour la production
if not DEBUG:
    # Configuration du proxy HTTPS pour Render
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Configuration Multi-tenant
PUBLIC_DOMAINS = [
    'localhost',
    '127.0.0.1',
    'testserver',
    'martialcomp.com',
    'www.martialcomp.com',
    'martialcomp.onrender.com',
]

# Configuration du routeur de base de données
DATABASE_ROUTERS = [
    'multitenant.routers.TenantDatabaseRouter',
]

# Configuration des domaines autorisés (sera étendu dynamiquement)
ALLOWED_HOSTS_DYNAMIC = False

# Configuration Stripe
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Configuration des plans et tarifs
SUBSCRIPTION_PLANS = {
    'essentials': {
        'name': 'Dojo Essentials',
        'max_users': 100,
        'max_disciplines': 2,
        'features': ['basic_management', 'grades', 'local_competitions'],
    },
    'masters': {
        'name': "Master's Circle", 
        'max_users': 300,
        'max_disciplines': 5,
        'features': ['basic_management', 'grades', 'all_competitions', 'technical_scoring', 'reporting'],
    },
    'champion': {
        'name': 'Grand Champion Suite',
        'max_users': None,  # Illimité
        'max_disciplines': None,  # Illimité
        'features': ['all'],
    },
}

# Configuration REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else 'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# Configuration JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Configuration OAuth2 Provider
OAUTH2_PROVIDER = {
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
        'clubs': 'Access to clubs data',
        'competitions': 'Access to competitions data',
        'practitioners': 'Access to practitioners data',
    },
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,  # 1 hour
    'REFRESH_TOKEN_EXPIRE_SECONDS': 2592000,  # 30 days
    'AUTHORIZATION_CODE_EXPIRE_SECONDS': 600,  # 10 minutes
    'REFRESH_TOKEN_GRACE_PERIOD_SECONDS': 120,  # 2 minutes
}

# Configuration des tokens de rafraîchissement
REFRESH_TOKEN_LIFETIME_DAYS = 30

# CORS Settings
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.martialcomp.com',
    'https://*.onrender.com',
]
CORS_ALLOW_CREDENTIALS = True