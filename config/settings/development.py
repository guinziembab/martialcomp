# config/settings/development.py
import os
from pathlib import Path
from .base import *

# Récupérer le chemin de base depuis base.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ✅ CORRECTION: Configuration complète pour développement local + mobile
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'martialcomp.local',
    '*.martialcomp.local',
    '.martialcomp.local',
    'testserver',  # Pour les tests Django
    # Ajout pour app mobile
    '192.168.0.4',  # IP local pour tests sur appareil physique
    '10.0.2.2',     # IP pour émulateur Android
]

# ✅ CORRECTION: Configuration CORS complète pour app mobile
CORS_ALLOW_ALL_ORIGINS = True  # Pour développement uniquement

CORS_ALLOWED_ORIGINS = [
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.0.4:19006",  # Expo (dev menu)
    "http://localhost:8081",      # Metro bundler
    "http://127.0.0.1:8081",
    "http://192.168.0.4:8081",    # Metro via IP locale
    "http://localhost:8080",      # Backend alternatif pour mobile
    "http://127.0.0.1:8080",
    "http://localhost:8888",      # Test port pour mobile
    "http://127.0.0.1:8888",
    "http://localhost:8002",      # Port libre pour mobile
    "http://127.0.0.1:8002",
]

CORS_ALLOW_CREDENTIALS = True
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
    'x-tenant-id',  # Pour multi-tenant
]

# ✅ AJOUT: Support django-cors-headers dans INSTALLED_APPS
if 'corsheaders' not in INSTALLED_APPS:
    INSTALLED_APPS = ['corsheaders'] + INSTALLED_APPS

# ✅ AJOUT: Middleware CORS en première position
if 'corsheaders.middleware.CorsMiddleware' not in MIDDLEWARE:
    MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE

# ✅ Configuration multi-tenant adaptée
MULTITENANT_DOMAIN = 'localhost:8000'  # Changé pour le développement local
MULTITENANT_SUBDOMAIN_ROUTING = False  # Désactivé pour le développement mobile

# Base de données PostgreSQL
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

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ✅ CORRECTION: Security Settings pour développement + mobile
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Permet l'accès JS pour mobile

# ✅ CORRECTION: CSRF Configuration pour développement local
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
    'http://0.0.0.0:8000',
    'http://127.0.0.1:8080',    # Port 8080 pour tests
    'http://localhost:8080',
    'http://0.0.0.0:8080',
    'http://192.168.0.4:8000',  # Pour appareil physique
    'http://192.168.0.4:8080',
    'http://localhost:8888',     # Test port
    'http://127.0.0.1:8888',
    'http://localhost:8002',     # Port libre
    'http://127.0.0.1:8002',
    'http://martialcomp.local:8000',
    'http://*.martialcomp.local:8000',
    'http://127.0.0.1:3000',
    'http://localhost:3000',
    'http://localhost:19006',   # Expo dev server
    'http://127.0.0.1:19006',
]

# ✅ CORRECTION: Configuration CSRF simplifiée pour mobile
CSRF_USE_SESSIONS = True  # Utilisation des sessions pour CSRF
CSRF_COOKIE_SAMESITE = None  # Plus permissif pour développement 
CSRF_COOKIE_AGE = 31449600  # 1 an pour éviter les expirations
# Pas de domain spécifique pour localhost
CSRF_COOKIE_DOMAIN = None  # Laissé par défaut pour localhost
SESSION_COOKIE_DOMAIN = None

# Configuration pour résoudre les erreurs CSRF
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'
CSRF_COOKIE_NAME = 'csrftoken'

# ✅ AJOUT: Configuration pour l'app mobile
# Disable CSRF for API endpoints used by mobile
CSRF_EXEMPT_URLS = [
    r'^/api/',  # Exemption CSRF pour toutes les routes API
]

# Configuration de debug pour CSRF (temporaire)
import logging
logging.getLogger('django.security.csrf').setLevel(logging.DEBUG)

# ✅ Configuration des fichiers statiques pour développement
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Email Configuration for Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ✅ CORRECTION: URL de base pour développement local
BASE_URL = 'http://localhost:8000'

# Configuration des redirections
LOGIN_REDIRECT_URL = '/competitions/dashboard/'
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/dashboard/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/competitions/onboarding/role/'
# Redirection après logout vers la page d'accueil avec paramètre pour éviter les boucles
LOGOUT_REDIRECT_URL = '/fr/?no_redirect=1'
ACCOUNT_LOGOUT_REDIRECT_URL = '/fr/?no_redirect=1'

# Configuration django-allauth
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# ✅ AJOUT: Configuration REST Framework pour API mobile
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ✅ AJOUT: Configuration pour les tokens d'API
if 'rest_framework.authtoken' not in INSTALLED_APPS:
    INSTALLED_APPS += ['rest_framework.authtoken']

# ✅ Configuration SIMPLE_JWT pour développement
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'ISSUER': 'martialcomp-api',
}

# Debug Toolbar pour développement
if DEBUG:
    try:
        import debug_toolbar
        if 'debug_toolbar' not in INSTALLED_APPS:
            INSTALLED_APPS += ['debug_toolbar']
        if 'debug_toolbar.middleware.DebugToolbarMiddleware' not in MIDDLEWARE:
            MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        
        # Configuration Debug Toolbar
        INTERNAL_IPS = ['127.0.0.1', 'localhost', '192.168.0.4']
        
        DEBUG_TOOLBAR_CONFIG = {
            'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        }
    except ImportError:
        pass

# Configuration Django Channels pour WebSocket
# ASGI_APPLICATION = 'config.asgi.application'  # TEMPORAIREMENT DÉSACTIVÉ

# Configuration Redis et Channels Layer
# CHANNEL_LAYERS = {  # TEMPORAIREMENT DÉSACTIVÉ
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('127.0.0.1', 6379)],
#             "capacity": 1500,
#             "expiry": 10,
#         },
#     },
# }

# Cache configuration - LocMemCache pour développement (pas besoin de Redis)
# Note: La configuration CACHES est déjà définie en haut du fichier (ligne 87-92)
# avec LocMemCache. Ne pas la redéfinir ici avec Redis.

# ✅ AMÉLIORATION: Logging plus détaillé pour debug mobile
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
        'colored': {
            'format': '[MOBILE] {levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'colored',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django-dev.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
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
            'level': 'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'competitions': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'multitenant': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'organizations': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Créer le répertoire de logs s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

# ✅ AJOUT: Configuration spéciale pour tests mobile
MOBILE_API_ENABLED = True
MOBILE_DEBUG = True

# Configuration des URLs d'authentification
LOGIN_URL = '/accounts/login/'

# ✅ AJOUT: Headers de sécurité adaptés pour développement
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'

print("Configuration de developpement chargee pour app mobile")
print(f"CORS Origins: {CORS_ALLOWED_ORIGINS}")
print(f"Allowed Hosts: {ALLOWED_HOSTS}")
print(f"Base URL: {BASE_URL}")