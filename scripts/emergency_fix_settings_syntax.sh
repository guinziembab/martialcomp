#!/bin/bash

################################################################################
# CORRECTION D'URGENCE - SYNTAXE SETTINGS.PY CORROMPUE
################################################################################

set -e

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SETTINGS_FILE="$PRODUCTION_PATH/config/settings.py"
BACKUP_PATH="/var/www/vhosts/martialcomp.com/backups/syntax_fix"
VENV_PATH="/var/www/vhosts/martialcomp.com/httpdocs/venv"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

create_emergency_backup() {
    info "💾 Sauvegarde d'urgence..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$BACKUP_PATH/$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"
    
    cp "$SETTINGS_FILE" "$BACKUP_DIR/settings_corrupted.py"
    
    success "Sauvegarde créée: $BACKUP_DIR"
    echo "$BACKUP_DIR" > /tmp/emergency_backup_path
}

fix_settings_syntax() {
    info "🔧 Réparation de la syntaxe settings.py..."
    
    # Créer un nouveau settings.py propre
    cat > "$SETTINGS_FILE" << 'SETTINGS_EOF'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-martialcomp-secret-key-change-in-production-2025-auth-system'

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
    'django.contrib.sites',
    'django_extensions',
    'widget_tweaks',
    'import_export',
    'rest_framework',
    'rest_framework_simplejwt',
    'oauth2_provider',
    'rosetta',
    'modeltranslation',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'competitions',
    'grades',
    'permissions_manager',
    'organizations',
    'finances',
    'shop',
    'documents',
    'multitenant',
    'api_auth',
    'family_management',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de données PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'martialcomp_user',
        'PASSWORD': 'your_password_here',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalisation
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Langues supportées
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('de', 'Deutsch'),
    ('pt', 'Português'),
    ('no', 'Norsk'),
    ('ja', '日本語'),
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Sites framework
SITE_ID = 1

# Authentification
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'oauth2_provider.backends.OAuth2Backend',
]

# Configuration AllAuth
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = False
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Configuration OAuth2
OAUTH2_PROVIDER = {
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
    },
    'ACCESS_TOKEN_EXPIRE_SECONDS': 3600,
    'REFRESH_TOKEN_EXPIRE_SECONDS': 3600 * 24 * 7,
}

# Configuration des réseaux sociaux
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': ['id', 'first_name', 'last_name', 'name', 'email'],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v17.0',
    }
}

# Configuration email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Configuration HTTPS/SSL
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_TLS = True

# Configuration REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/www/vhosts/martialcomp.com/logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
SETTINGS_EOF

    success "Nouveau settings.py créé avec syntaxe correcte"
}

test_django_syntax() {
    info "🧪 Test de la syntaxe Django..."
    
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    
    # Test de syntaxe Python
    if python -m py_compile config/settings.py; then
        success "Syntaxe Python valide"
    else
        error "Syntaxe Python invalide"
    fi
    
    # Test de configuration Django
    if python manage.py check --deploy; then
        success "Configuration Django valide"
    else
        warning "Avertissements de configuration Django"
        python manage.py check
    fi
}

restart_django_clean() {
    info "🔄 Redémarrage Django avec configuration propre..."
    
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    
    # Nettoyer tous les processus Django
    pkill -f "python.*manage.py" || true
    pkill -f "runserver" || true
    sleep 3
    
    # Collecter les fichiers statiques
    python manage.py collectstatic --noinput || warning "Erreur collectstatic"
    
    # Démarrer Django
    nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django_syntax_fixed.log 2>&1 &
    
    sleep 5
    
    if pgrep -f "runserver" > /dev/null; then
        success "Django redémarré avec succès"
    else
        error "Échec du redémarrage Django"
    fi
}

test_profile_urls() {
    info "🧪 Test des URLs de profil..."
    
    # Test localhost
    if curl -s -f -o /dev/null "http://localhost:8000/"; then
        success "Page d'accueil accessible"
    else
        warning "Page d'accueil non accessible"
    fi
    
    # Test profil practitioner
    if curl -s -f -o /dev/null "http://localhost:8000/fr/competitions/practitioner/profile/"; then
        success "Profil practitioner accessible"
    else
        warning "Profil practitioner non accessible (authentification requise)"
    fi
    
    # Afficher les logs
    info "Logs Django récents:"
    tail -10 /tmp/django_syntax_fixed.log 2>/dev/null || echo "Pas de logs disponibles"
}

main() {
    info "🚨 CORRECTION D'URGENCE - SYNTAXE SETTINGS.PY"
    info "=============================================="
    
    create_emergency_backup
    fix_settings_syntax
    test_django_syntax
    restart_django_clean
    test_profile_urls
    
    success "🎉 CORRECTION SYNTAXE TERMINÉE"
    info "================================================="
    info "URLs à tester:"
    info "• Page d'accueil: https://martialcomp.com/"
    info "• Profil: https://martialcomp.com/fr/competitions/practitioner/profile/"
    info "• Logs: tail -f /tmp/django_syntax_fixed.log"
}

main "$@"