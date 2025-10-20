# Configuration Django pour l'installation de production
# Ce fichier configure Django spécifiquement pour l'installateur de production

from .production import *
import os
from decouple import config

# Configuration de base pour l'installation
DEBUG = False
ALLOWED_HOSTS = [
    'martialcomp.com',
    'www.martialcomp.com',
    'localhost',
    '127.0.0.1',
]

# Ajout d'hosts dynamiques depuis les variables d'environnement
additional_hosts = config('ALLOWED_HOSTS', default='').split(',')
ALLOWED_HOSTS.extend([host.strip() for host in additional_hosts if host.strip()])

# Base de données PostgreSQL pour la production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB', default='martialcomp_db'),
        'USER': config('POSTGRES_USER', default='martialcomp_user'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='AQWZSX123ok,'),
        'HOST': config('POSTGRES_HOST', default='localhost'),
        'PORT': config('POSTGRES_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 60,
        }
    }
}

# Configuration des fichiers statiques pour la production
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Configuration des fichiers média
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuration des logs pour la production
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
            'filename': '/var/log/martialcomp/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'martialcomp': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuration de sécurité pour la production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_REFERRER_POLICY = 'same-origin'

# Configuration HTTPS
USE_TLS = config('USE_TLS', default=True, cast=bool)
if USE_TLS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Configuration des cookies
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 heure

# Configuration du cache pour la production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'martialcomp-cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# Configuration des sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# Configuration de l'email pour la production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@martialcomp.com')

# Configuration des admins pour les notifications d'erreur
ADMINS = [
    ('Admin MartialComp', 'admin@martialcomp.com'),
]
MANAGERS = ADMINS

# Configuration de la compression des réponses
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
] + MIDDLEWARE

# Configuration optimisée pour la production
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_TEMP_DIR = '/tmp'

# Configuration du timezone
USE_TZ = True
TIME_ZONE = 'Europe/Paris'

# Configuration de l'internationalisation
USE_I18N = True
USE_L10N = True

LANGUAGE_CODE = 'fr-fr'
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Configuration des templates optimisée
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Configuration de la validation des mots de passe
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

# Configuration des uploads de fichiers
UPLOAD_SETTINGS = {
    'MAX_FILE_SIZE': 50 * 1024 * 1024,  # 50MB
    'ALLOWED_EXTENSIONS': [
        'jpg', 'jpeg', 'png', 'gif', 'pdf', 
        'doc', 'docx', 'xls', 'xlsx', 'txt'
    ],
}

# Configuration pour les QR codes
QR_CODE_CACHE_ALIAS = 'default'

# Configuration pour les traductions
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'
MODELTRANSLATION_LANGUAGES = ('fr', 'en')

# Configuration pour l'export/import
IMPORT_EXPORT_USE_TRANSACTIONS = True

# Configuration spécifique pour l'installateur
INSTALLATION_MODE = True
SKIP_MIGRATIONS_CHECK = config('SKIP_MIGRATIONS_CHECK', default=False, cast=bool)

# URL de health check pour le monitoring
HEALTH_CHECK_URL = '/health/'

# Configuration de monitoring
MONITORING_ENABLED = True
COLLECT_METRICS = True

# Désactivation du mode debug toolbar en production
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: False,
}

# Configuration pour les API
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# Configuration CORS pour l'API
CORS_ALLOWED_ORIGINS = [
    "https://martialcomp.com",
    "https://www.martialcomp.com",
]

CORS_ALLOW_CREDENTIALS = True

# Message de configuration pour les logs
import logging
logger = logging.getLogger(__name__)
logger.info("Configuration Django chargée pour l'installation de production")