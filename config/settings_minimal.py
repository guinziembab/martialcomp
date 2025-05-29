"""
Configuration minimale pour contourner les problèmes d'importation.
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
    # Applications locales simplifiées
    'competitions',
    'grades',
    'permissions_manager',
    'organizations',
    'finances',
    'shop',
    'multitenant',
    'api_auth',
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
    # 'multitenant.middleware.TenantMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - using SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

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

# Créer le répertoire de logs s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)