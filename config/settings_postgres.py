"""
Configuration minimale avec PostgreSQL pour contourner les problèmes d'importation.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-tv=2g@wtxxfu^6trqra-ewp9%j2gm^x3_&y)vhlo%jj+r_+0dq'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

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
    # Applications locales
    'competitions',
    'grades',
    'permissions_manager',
    'organizations',
    'finances',
    'shop',
    'multitenant',
    'api_auth',
    'documents',
    # Ne pas inclure 'security' qui semble problématique
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Désactiver temporairement les middlewares problématiques
    # 'security.middleware.SecurityMiddleware',
    # 'security.rate_limiting.RateLimitingMiddleware',
    # 'competitions.utils.security.OrganizationIsolationMiddleware',
    'multitenant.middleware.TenantMiddleware',  # Réactivé pour PostgreSQL
    # 'multitenant.cache.TenantCacheMiddleware',
    # 'multitenant.resource_limits.ResourceTrackerMiddleware',
    # 'multitenant.middleware.FeatureAccessMiddleware',
    # 'api_auth.middleware.JWTTenantMiddleware',
    # 'api_auth.middleware.APIErrorHandlingMiddleware',
    # 'api_auth.middleware.APILoggingMiddleware',
    # 'competitions.middleware.OnboardingMiddleware',
    # 'finances.middleware.FinancialAuditMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
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

# Database - using PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=public'
        },
        'CONN_MAX_AGE': 60,  # Durée de vie des connexions en secondes
    }
}

# Cache configuration
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

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# Languages disponibles
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

# Static files
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redirection après connexion
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/competitions/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Configuration des messages
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Configuration PostgreSQL pour le multi-tenant
# Les options sont déjà définies dans la configuration principale

# Configuration du routeur de base de données
DATABASE_ROUTERS = [
    'multitenant.routers.TenantDatabaseRouter',
]

# Configuration des domaines autorisés (sera étendu dynamiquement)
ALLOWED_HOSTS_DYNAMIC = True

# Configuration Multi-tenant
PUBLIC_DOMAINS = [
    'localhost',
    '127.0.0.1',
    'martialcomp.com',
    'www.martialcomp.com',
]

# Créer le répertoire de logs s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# Configuration CSRF pour multi-tenant
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.martialcomp.com',
]

# Configuration des cookies pour multi-tenant
SESSION_COOKIE_DOMAIN = None  # None permet les cookies pour localhost
CSRF_COOKIE_DOMAIN = None     # None permet les cookies pour localhost

# Sécurité CSRF
CSRF_COOKIE_HTTPONLY = False  # False permet à JavaScript d'accéder au cookie CSRF
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_USE_SESSIONS = False  # Utiliser les cookies au lieu des sessions
CSRF_COOKIE_SAMESITE = 'Lax'  # Protection contre CSRF