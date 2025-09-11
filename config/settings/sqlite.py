# config/settings/sqlite.py
import os
from pathlib import Path
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']

# Base de données SQLite pour les tests locaux
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(__file__).resolve().parent.parent.parent / 'db.sqlite3',
    }
}

# Cache Configuration (simple locmem)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines

# Security Settings for Development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True

# Email Configuration for Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# URL de base pour la génération des QR codes et liens absolus
BASE_URL = 'http://127.0.0.1:8000'

# Configuration des redirections pour django-allauth
LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/competitions/onboarding/role/'
LOGOUT_REDIRECT_URL = '/fr/'

# Configuration django-allauth
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_USERNAME_REQUIRED = True