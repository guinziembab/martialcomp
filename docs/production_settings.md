# Configuration Django Optimale pour la Production

Ce fichier présente la configuration Django recommandée pour l'environnement de production de MartialComp. Il s'agit d'un exemple de fichier `config/settings/production.py` optimisé pour la performance, la sécurité et la stabilité.

```python
# config/settings/production.py

import os
from .base import *  # noqa

# SÉCURITÉ
# ------------------------------------------------------------------------------
# Voir https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# AVERTISSEMENT: Gardez le secret key utilisé en production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Désactiver le mode DEBUG en production
DEBUG = False

# Configuration de l'hôte
ALLOWED_HOSTS = [
    'martialcomp.com',
    'www.martialcomp.com',
    '.martialcomp.com',  # Permet tous les sous-domaines
    os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(','),
]

# HTTPS/SSL
# ------------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# APPLICATIONS
# ------------------------------------------------------------------------------
INSTALLED_APPS += [
    'gunicorn',
    'whitenoise.runserver_nostatic',
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configuration de la protection contre les attaques CSRF
CSRF_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True
CSRF_COOKIE_SAMESITE = 'Strict'

# STOCKAGE STATIQUE ET MÉDIA
# ------------------------------------------------------------------------------
STATIC_ROOT = os.path.join(BASE_DIR, '../static')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, '../media')
MEDIA_URL = '/media/'

# Configuration WhiteNoise pour la compression et la mise en cache
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_MAX_AGE = 31536000  # 1 an

# BASE DE DONNÉES
# ------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'martialcomp'),
        'USER': os.environ.get('DB_USER', 'martialcomp'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
        },
        'ATOMIC_REQUESTS': True,
        'AUTOCOMMIT': True,
    }
}

# CACHE
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': True,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
        },
        'KEY_PREFIX': 'martialcomp',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Cache de session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 heures

# Cache de page
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 600  # 10 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = 'martialcomp'

# E-MAIL
# ------------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'MartialComp <noreply@martialcomp.com>'
SERVER_EMAIL = 'server@martialcomp.com'
EMAIL_SUBJECT_PREFIX = '[MartialComp] '

# INTERNATIONALISATION
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'fr'
USE_I18N = True
USE_L10N = True
USE_TZ = True
TIME_ZONE = 'Europe/Paris'

LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('de', 'Deutsch'),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# LOGGING
# ------------------------------------------------------------------------------
LOG_DIR = os.path.join(BASE_DIR, '../logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'competitions': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
        },
        'py.warnings': {
            'handlers': ['console', 'file'],
        },
    },
}

# CELERY
# ------------------------------------------------------------------------------
if 'celery' in INSTALLED_APPS:
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TIMEZONE = TIME_ZONE
    CELERY_TASK_TIME_LIMIT = 60 * 60 * 5  # 5 heures
    CELERY_TASK_SOFT_TIME_LIMIT = 60 * 60 * 4  # 4 heures
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# MODULES OPTIONNELS
# ------------------------------------------------------------------------------
# Vérification et activation conditionnelle des modules optionnels

# Module Grades
try:
    import grades
    if 'grades' not in INSTALLED_APPS:
        INSTALLED_APPS.append('grades')
except ImportError:
    pass

# Module Finances
try:
    import finances
    if 'finances' not in INSTALLED_APPS:
        INSTALLED_APPS.append('finances')
except ImportError:
    pass

# Module Shop (dépend de finances)
if 'finances' in INSTALLED_APPS:
    try:
        import shop
        if 'shop' not in INSTALLED_APPS:
            INSTALLED_APPS.append('shop')
    except ImportError:
        pass

# Module Organizations
try:
    import organizations
    if 'organizations' not in INSTALLED_APPS:
        INSTALLED_APPS.append('organizations')
except ImportError:
    pass

# SÉCURITÉ AVANCÉE
# ------------------------------------------------------------------------------
ADMINS = [
    ('Admin MartialComp', 'admin@martialcomp.com'),
]
MANAGERS = ADMINS

# Protection contre les attaques par force brute
if 'axes' in INSTALLED_APPS:
    AXES_FAILURE_LIMIT = 5  # Nombre de tentatives avant verrouillage
    AXES_COOLOFF_TIME = 1  # Durée de verrouillage en heures
    AXES_LOCK_OUT_AT_FAILURE = True
    AXES_LOCKOUT_TEMPLATE = 'account/lockout.html'

# Configuration du middleware de contenu sécurisé (CSP)
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com", "cdnjs.cloudflare.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "cdnjs.cloudflare.com")
CSP_FONT_SRC = ("'self'", "fonts.googleapis.com", "fonts.gstatic.com", "cdnjs.cloudflare.com")
CSP_IMG_SRC = ("'self'", "data:", "*.martialcomp.com")

# OPTIMISATIONS DE PERFORMANCE
# ------------------------------------------------------------------------------
# Compression GZip
MIDDLEWARE.append('django.middleware.gzip.GZipMiddleware')

# Template caching
TEMPLATES[0]['OPTIONS']['loaders'] = [
    ('django.template.loaders.cached.Loader', [
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ]),
]

# Cache du middleware
MIDDLEWARE.insert(2, 'django.middleware.cache.UpdateCacheMiddleware')
MIDDLEWARE.append('django.middleware.cache.FetchFromCacheMiddleware')

# GESTION DES ERREURS
# ------------------------------------------------------------------------------
# Templates d'erreur personnalisés
handler404 = 'competitions.views.errors.handler404'
handler500 = 'competitions.views.errors.handler500'
handler403 = 'competitions.views.errors.handler403'
handler400 = 'competitions.views.errors.handler400'

# URL DE REDIRECTION
# ------------------------------------------------------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# CONFIGURATION DES TÉLÉCHARGEMENTS DE FICHIERS
# ------------------------------------------------------------------------------
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# REST FRAMEWORK
# ------------------------------------------------------------------------------
if 'rest_framework' in INSTALLED_APPS:
    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': [
            'rest_framework.renderers.JSONRenderer',
        ],
        'DEFAULT_PARSER_CLASSES': [
            'rest_framework.parsers.JSONParser',
        ],
        'DEFAULT_AUTHENTICATION_CLASSES': [
            'rest_framework_simplejwt.authentication.JWTAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        ],
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/day',
            'user': '1000/day',
        },
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,
        'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema',
        'EXCEPTION_HANDLER': 'competitions.utils.api.custom_exception_handler',
    }

# MODULES PERSONNALISÉS
# ------------------------------------------------------------------------------
# Paramètres spécifiques au module Competitions
COMPETITION_CATEGORIES_PER_PAGE = 20
COMPETITION_RESULTS_CACHE_TIMEOUT = 60 * 5  # 5 minutes

# Paramètres spécifiques au module Grades (si activé)
if 'grades' in INSTALLED_APPS:
    GRADE_SYSTEM_TYPES = [
        ('belt', 'Système de ceintures'),
        ('dan', 'Système Dan/Kyu'),
        ('level', 'Système par niveau'),
    ]
    GRADE_MIN_TIME_BETWEEN_PROMOTIONS = 90  # 90 jours

# Paramètres spécifiques au module Finances (si activé)
if 'finances' in INSTALLED_APPS:
    PAYMENT_PROVIDERS = [
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ]
    DEFAULT_PAYMENT_PROVIDER = 'stripe'
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Paramètres spécifiques au module Shop (si activé)
if 'shop' in INSTALLED_APPS:
    SHOP_CURRENCY = 'EUR'
    SHOP_TAX_RATE = 0.20  # 20% TVA
    SHOP_ORDER_EXPIRATION_HOURS = 24  # 24 heures

# MONITORING
# ------------------------------------------------------------------------------
# Sentry.io configuration (si utilisé)
if 'sentry_sdk' in sys.modules:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN', ''),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,  # Ajuster selon le volume
        send_default_pii=False,
        environment=os.environ.get('ENVIRONMENT', 'production'),
    )

# FINAL CHECKS
# ------------------------------------------------------------------------------
# Vérifier que le site est correctement configuré
if os.environ.get('DJANGO_CHECK_DEPLOYMENT', '0') == '1':
    # Import nécessaire pour check_security
    from django.core.management.utils import get_random_secret_key
    from django.core.checks.security.base import SECRET_KEY_INSECURE_PREFIX

    if SECRET_KEY.startswith(SECRET_KEY_INSECURE_PREFIX):
        print("WARNING: SECRET_KEY is insecure and must be changed!")
    if DEBUG:
        print("WARNING: DEBUG is enabled in production!")
    for h in ALLOWED_HOSTS:
        if h == '*':
            print("WARNING: ALLOWED_HOSTS contains '*', which is insecure!")
```

## Points clés de la configuration

Cette configuration a été optimisée pour:

### 1. Sécurité

- **SSL/HTTPS** obligatoire
- **Protection CSRF** renforcée
- **En-têtes de sécurité** (HSTS, XSS, etc.)
- **Politique de sécurité du contenu** (CSP)
- **Limitations sur les téléchargements**
- **Stockage sécurisé des secrets** via variables d'environnement

### 2. Performance

- **Cache Redis** pour les sessions et les données
- **WhiteNoise** pour servir les fichiers statiques
- **Connexions persistantes** à la base de données
- **Compression GZip**
- **Mise en cache des templates**
- **Paramètres optimisés** pour les applications à fort trafic

### 3. Fiabilité

- **Logging** complet vers fichiers et emails
- **Timeouts** adaptés pour éviter les blocages
- **Gestion des erreurs** personnalisée
- **Paramètres de base de données** robustes
- **Monitoring** intégré (option Sentry)

### 4. Modularité

- **Détection automatique** des modules optionnels
- **Configuration conditionnelle** selon les modules disponibles
- **Paramètres spécifiques** pour chaque module

## Fichier .env exemple

Voici un exemple de fichier `.env` à placer dans le répertoire racine du projet:

```
# Django
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=votre_clé_secrète_complexe_ici
DJANGO_ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com

# Base de données
DB_NAME=martialcomp
DB_USER=martialcomp_user
DB_PASSWORD=mot_de_passe_sécurisé
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=no-reply@martialcomp.com
EMAIL_HOST_PASSWORD=mot_de_passe_email

# Redis
REDIS_URL=redis://localhost:6379/1

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Paiement
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
ENVIRONMENT=production

# Vérification du déploiement
DJANGO_CHECK_DEPLOYMENT=1
```

## Mise en œuvre

1. Placez ce fichier à l'emplacement `config/settings/production.py`
2. Créez un fichier `.env` avec les variables d'environnement nécessaires
3. Assurez-vous que le serveur peut lire le fichier `.env` (permissions)
4. Redémarrez Gunicorn et les autres services
5. Vérifiez les logs pour vous assurer que tout fonctionne correctement

## Notes importantes

- **Ne jamais** stocker des secrets directement dans ce fichier
- **Toujours** vérifier que DEBUG est à FALSE en production
- Ajuster les paramètres de cache et de base de données selon vos besoins
- Les paramètres de sécurité sont str