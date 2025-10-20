import os
import locale
import logging
from pathlib import Path
import sys
from decouple import config

# Forcer l'encodage UTF-8 globalement
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# Configuration locale sécurisée
try:
    if os.name != 'nt':  # Unix/Linux/macOS
        locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')
    else:  # Windows
        locale.setlocale(locale.LC_ALL, 'French_France.1252')
except locale.Error:
    # Fallback si la locale n'est pas disponible
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass  # Utiliser la locale par défaut

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ajouter le chemin du projet au sys.path pour faciliter les importations
sys.path.append(str(BASE_DIR / 'apps'))

# Configuration encodage
USE_I18N = True
USE_L10N = True
USE_TZ = True
DEFAULT_CHARSET = 'utf-8'
FILE_CHARSET = 'utf-8'

# Configuration timezone
TIME_ZONE = 'Europe/Paris'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-martialcomp-secret-key-change-in-production-2025-auth-system')

# Configuration base de données avec encodage UTF-8
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'martialcomp'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'rosetta',
    'modeltranslation',
    'widget_tweaks',
    'crispy_forms',
    'crispy_bootstrap5',
    'import_export',
    'channels',
    
    # Applications MartialComp (maintenant dans apps/)
    'apps.competitions.apps.CompetitionsConfig',
    'apps.organizations',
    # 'apps.multitenant',  # Désactivé (fichiers corrompus provoquant des null bytes)
    'apps.grades',
    'apps.finances',
    'apps.shop',
    'apps.documents',
    'apps.family_management',
    'apps.permissions_manager',
    'apps.payment',
    'apps.task_management',  # Gestion des tâches Kanban
    'apps.membership',  # Système d'adhésion MartialComp v2.0
    'accounts',
    'apps.security',
    'api_auth',
]

# Solution de secours avec chemin d'importation correct
try:
    # Le middleware est dans un package - UTILISER LE NOUVEAU CHEMIN
    from apps.competitions.middleware import OnboardingRedirectMiddleware
    MIDDLEWARE_ONBOARDING = 'apps.competitions.middleware.OnboardingRedirectMiddleware'
    print("SUCCESS: Middleware OnboardingRedirectMiddleware trouve et importe avec succes.")
except (ImportError, AttributeError) as e:
    # Si le middleware n'existe pas, utiliser un middleware générique
    MIDDLEWARE_ONBOARDING = 'django.middleware.common.CommonMiddleware'
    import logging
    logging.getLogger(__name__).warning(
        f"OnboardingRedirectMiddleware n'est pas disponible: {str(e)}. "
        "Assurez-vous que le fichier apps/competitions/middleware.py existe avec la classe OnboardingRedirectMiddleware."
    )

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # 'apps.multitenant.middleware.TenantMiddleware',  # Désactivé tant que le module est réparé
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'apps.finances.middleware.CurrencyMiddleware',
    MIDDLEWARE_ONBOARDING,
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.isolation.OrganizationSecurityMiddleware',  # APRÈS l'authentification - Middleware d'isolation organisationnelle
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'apps.payment.middleware.SubscriptionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # Templates globaux
            BASE_DIR / 'apps' / 'competitions' / 'templates',  # Templates competitions
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.finances.context_processors.financial_stats',
                'apps.competitions.context_processors.language_context',
                'apps.payment.context_processors.subscription_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en'

# Langues supportées (18 langues)
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('pt', 'Português'),
    ('ru', 'Русский'),
    ('vi', 'Tiếng Việt'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh-hans', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('ko', '한국어'),
]

# Configuration django-modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = 'fr'
MODELTRANSLATION_LANGUAGES = ('fr', 'en')
MODELTRANSLATION_FALLBACK_LANGUAGES = ('fr', 'en')

# Chemins des fichiers de traduction
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='MartialComp <noreply@martialcomp.com>')

# Email addresses for different services
ACCOUNTING_EMAIL = config('ACCOUNTING_EMAIL', default='finance@martialcomp.com')
CUSTOMER_SERVICE_EMAIL = config('CUSTOMER_SERVICE_EMAIL', default='support@martialcomp.com')
SUPPORT_EMAIL = config('SUPPORT_EMAIL', default='support@martialcomp.com')

# Site URL for email links
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site framework
SITE_ID = 1

# Authentication
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ================================================================
# DJANGO ALLAUTH CONFIGURATION - SYNTAXE MODERNE 2025
# ================================================================

# Configuration des méthodes de connexion
ACCOUNT_LOGIN_METHODS = {'email', 'username'}

# Configuration des champs d'inscription
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']

# Configuration de l'email
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'

# Configuration des sessions et redirections
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_SESSION_REMEMBER = True

# Adaptateurs personnalisés pour l'onboarding
ACCOUNT_ADAPTER = 'apps.competitions.adapters.MartialCompAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'apps.competitions.adapters.MartialCompSocialAccountAdapter'

# URLs de redirection (CORRIGÉES - sans préfixe de langue)
LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_SIGNUP_REDIRECT_URL = '/competitions/onboarding/role/'
LOGOUT_REDIRECT_URL = '/fr/'
LOGIN_URL = '/accounts/login/'

# Configuration d'authentification sociale
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = False
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_STORE_TOKENS = True

# Fournisseurs d'authentification sociale
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
        'VERIFIED_EMAIL': True,
    },
    'facebook': {
        'APP': {
            'client_id': os.getenv('FACEBOOK_APP_ID', ''),
            'secret': os.getenv('FACEBOOK_APP_SECRET', ''),
        },
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': ['id', 'first_name', 'last_name', 'name', 'email'],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v18.0',
    }
}

# ================================================================
# AUTRES CONFIGURATIONS
# ================================================================

# Crispy Forms Configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Multi-tenant Configuration
PUBLIC_DOMAINS = ['localhost', '127.0.0.1', 'testserver']

# CSRF Configuration
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = False

# ================================================================
# CONFIGURATION LOGGING AVEC ENCODAGE UTF-8 (COMPLÈTEMENT CORRIGÉE)
# ================================================================

# Créer le répertoire de logs s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'utf8_console': {
            'format': 'INFO {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'utf8_console',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.competitions': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ================================================================
# CONFIGURATION ROSETTA POUR TRADUCTIONS
# ================================================================

if 'rosetta' in INSTALLED_APPS:
    ROSETTA_MESSAGES_SOURCE_LANGUAGE_CODE = 'fr'
    ROSETTA_MESSAGES_SOURCE_LANGUAGE_NAME = 'Français'
    
    ROSETTA_LANGUAGES = [
        ('es', 'Español'),
        ('pt', 'Português'), 
        ('no', 'Norsk'),
        ('en', 'English'),
        ('it', 'Italiano'),
        ('de', 'Deutsch'),
        ('ar', 'العربية'),
    ]
    
    ROSETTA_SHOW_AT_ADMIN_PANEL = True
    ROSETTA_AUTO_COMPILE = True
    ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
    ROSETTA_REQUIRES_AUTH = True
    ROSETTA_MESSAGES_PER_PAGE = 25
    
    ROSETTA_EXCLUDED_APPLICATIONS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'allauth',
    ]

# ================================================================
# DEEPL TRANSLATION SERVICE
# ================================================================

DEEPL_API_KEY = config('DEEPL_API_KEY', default='')
if not DEEPL_API_KEY:
    # Réduire le bruit en prod: log en DEBUG uniquement
    logging.getLogger(__name__).debug("DeepL API key not found; translation features disabled.")

DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate'

DEEPL_LANGUAGE_MAPPING = {
    'fr': 'FR',
    'en': 'EN',
    'es': 'ES',
    'it': 'IT',
    'de': 'DE',
    'pt': 'PT',
    'ru': 'RU',
    'vi': 'VI',
    'ja': 'JA',
    'zh-hans': 'ZH',
    'ar': 'AR',
    'ko': 'KO',
    'nl': 'NL',
    'pl': 'PL',
    'sv': 'SV',
    'no': 'NB',
}

# Cache Configuration avec Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'martialcomp',
        'TIMEOUT': 300,
    }
}

# Configuration pour les sessions avec Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Configuration pour les permissions
PERMISSION_CACHE_ENABLED = True
PERMISSION_CACHE_TTL = 300  # 5 minutes

# ================================================================
# LOGGING DE SÉCURITÉ POUR LA SEGMENTATION
# ================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'security': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'formatter': 'security',
        },
        'organization_access_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'organization_access.log'),
            'formatter': 'security',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'security.organization_access': {
            'handlers': ['organization_access_file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.core.isolation': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Créer le répertoire des logs s'il n'existe pas
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)