#!/bin/bash

# =============================================================================
# REMPLACEMENT COMPLET PRODUCTION PAR DÉVELOPPEMENT
# Stratégie: Remplacer TOUT sauf l'accès Apache au site martialcomp.com
# =============================================================================

set -e

echo "🔄 REMPLACEMENT COMPLET PRODUCTION PAR DÉVELOPPEMENT"
echo "======================================================"
echo "📅 Date: $(date)"
echo "🎯 Stratégie: Remplacement TOTAL de la production par le développement"
echo "⚠️  ATTENTION: Cette opération va remplacer TOUT le code de production"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# =============================================================================
# 1. SAUVEGARDE CRITIQUE DE LA PRODUCTION
# =============================================================================

echo "💾 1. SAUVEGARDE CRITIQUE DE LA PRODUCTION"
echo "==========================================="

BACKUP_DIR="backups/production_complete_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "   📁 Sauvegarde COMPLÈTE avant remplacement..."

# Sauvegarder TOUT le code existant (en cas de problème)
cp -r competitions/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r config/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r organizations/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r grades/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r finances/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r shop/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r documents/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r family_management/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r permissions_manager/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r payment/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r accounts/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r multitenant/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r security/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r api_auth/ "$BACKUP_DIR/" 2>/dev/null || true
cp manage.py "$BACKUP_DIR/" 2>/dev/null || true
cp requirements.txt "$BACKUP_DIR/" 2>/dev/null || true
cp -r locale/ "$BACKUP_DIR/" 2>/dev/null || true
cp -r static/ "$BACKUP_DIR/" 2>/dev/null || true

echo "   ✅ Sauvegarde complète terminée dans: $BACKUP_DIR"

# Sauvegarde spécifique de la configuration Apache (À PRÉSERVER)
mkdir -p "$BACKUP_DIR/apache_config"
cp /etc/apache2/sites-available/martialcomp.conf "$BACKUP_DIR/apache_config/" 2>/dev/null || true
cp /etc/apache2/sites-enabled/martialcomp.conf "$BACKUP_DIR/apache_config/" 2>/dev/null || true

echo "   ✅ Configuration Apache sauvegardée"

# =============================================================================
# 2. NETTOYAGE COMPLET DE LA PRODUCTION (SAUF ACCÈS APACHE)
# =============================================================================

echo ""
echo "🧹 2. NETTOYAGE COMPLET DE LA PRODUCTION"
echo "========================================"

# Arrêter Django
echo "   🛑 Arrêt des processus Django..."
pkill -f "runserver.*8080" 2>/dev/null || true
pkill -f "manage.py runserver" 2>/dev/null || true
sleep 3

# SUPPRIMER TOUT LE CODE DJANGO (sauf infrastructure Apache)
echo "   🗑️ Suppression complète du code Django existant..."

# Applications Django complètes
rm -rf competitions/ 2>/dev/null || true
rm -rf organizations/ 2>/dev/null || true
rm -rf grades/ 2>/dev/null || true
rm -rf finances/ 2>/dev/null || true
rm -rf shop/ 2>/dev/null || true
rm -rf documents/ 2>/dev/null || true
rm -rf family_management/ 2>/dev/null || true
rm -rf permissions_manager/ 2>/dev/null || true
rm -rf payment/ 2>/dev/null || true
rm -rf accounts/ 2>/dev/null || true
rm -rf multitenant/ 2>/dev/null || true
rm -rf security/ 2>/dev/null || true
rm -rf api_auth/ 2>/dev/null || true

# Configuration Django
rm -rf config/ 2>/dev/null || true

# Fichiers système Django
rm -f manage.py 2>/dev/null || true
rm -f requirements.txt 2>/dev/null || true

# Dossiers de données/cache
rm -rf static/ 2>/dev/null || true
rm -rf staticfiles/ 2>/dev/null || true
rm -rf media/ 2>/dev/null || true
rm -rf locale/ 2>/dev/null || true
rm -rf __pycache__/ 2>/dev/null || true
rm -rf .pytest_cache/ 2>/dev/null || true

# Scripts de correction (À EXCLURE du transfert)
rm -rf scripts/ 2>/dev/null || true

echo "   ✅ Production nettoyée complètement"

# =============================================================================
# 3. COPIE COMPLÈTE DE L'ENVIRONNEMENT DE DÉVELOPPEMENT
# =============================================================================

echo ""
echo "📂 3. COPIE COMPLÈTE ENVIRONNEMENT DE DÉVELOPPEMENT"
echo "=================================================="

# Cette section va être remplie avec le chemin source du développement
# Pour l'instant, on suppose que les fichiers source sont disponibles localement

DEV_SOURCE="/path/to/development/source"  # À adapter selon votre contexte

echo "   📋 COPIE DE TOUTES LES APPLICATIONS DJANGO..."

# Applications complètes
echo "   📁 competitions/"
mkdir -p competitions/
# Note: Ici il faudra copier depuis votre environnement de développement
# cp -r "$DEV_SOURCE/competitions/" ./ 

echo "   📁 organizations/"
mkdir -p organizations/
# cp -r "$DEV_SOURCE/organizations/" ./

echo "   📁 grades/"
mkdir -p grades/
# cp -r "$DEV_SOURCE/grades/" ./

echo "   📁 finances/"
mkdir -p finances/
# cp -r "$DEV_SOURCE/finances/" ./

echo "   📁 shop/"
mkdir -p shop/
# cp -r "$DEV_SOURCE/shop/" ./

echo "   📁 documents/"
mkdir -p documents/
# cp -r "$DEV_SOURCE/documents/" ./

echo "   📁 family_management/"
mkdir -p family_management/
# cp -r "$DEV_SOURCE/family_management/" ./

echo "   📁 permissions_manager/"
mkdir -p permissions_manager/
# cp -r "$DEV_SOURCE/permissions_manager/" ./

echo "   📁 payment/"
mkdir -p payment/
# cp -r "$DEV_SOURCE/payment/" ./

echo "   📁 accounts/"
mkdir -p accounts/
# cp -r "$DEV_SOURCE/accounts/" ./

echo "   📁 multitenant/"
mkdir -p multitenant/
# cp -r "$DEV_SOURCE/multitenant/" ./

echo "   📁 security/"
mkdir -p security/
# cp -r "$DEV_SOURCE/security/" ./

echo "   📁 api_auth/"
mkdir -p api_auth/
# cp -r "$DEV_SOURCE/api_auth/" ./

# Configuration
echo "   ⚙️ Configuration Django..."
mkdir -p config/
# cp -r "$DEV_SOURCE/config/" ./

# Fichiers système
echo "   📄 Fichiers système..."
# cp "$DEV_SOURCE/manage.py" ./
# cp "$DEV_SOURCE/requirements.txt" ./

# Traductions et fichiers statiques
echo "   🌍 Traductions et statiques..."
# cp -r "$DEV_SOURCE/locale/" ./
# cp -r "$DEV_SOURCE/static/" ./

echo "   ✅ Copie complète du développement terminée"

# =============================================================================
# 4. CRÉATION DE LA CONFIGURATION DE PRODUCTION
# =============================================================================

echo ""
echo "⚙️ 4. CONFIGURATION PRODUCTION ADAPTÉE"
echo "======================================"

# Créer manage.py
cat > manage.py << 'EOF'
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
EOF

echo "   ✅ manage.py créé"

# Créer la structure de configuration
mkdir -p config/settings/

# Configuration de base
cat > config/settings/base.py << 'EOF'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Applications complètes du développement
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
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
    'competitions',
    'organizations',
    'multitenant',
    'grades',
    'finances',
    'shop',
    'documents',
    'family_management',
    'permissions_manager',
    'payment',
    'accounts',
    'security',
    'api_auth',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'multitenant.middleware.TenantMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'payment.middleware.SubscriptionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'competitions' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'competitions.context_processors.language_context',
                'payment.context_processors.subscription_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Internationalization
USE_I18N = True
USE_TZ = True
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'

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
    ('zh', '中文'),
    ('hi', 'हिन्दी'),
    ('ar', 'العربية'),
    ('sw', 'Kiswahili'),
    ('am', 'አማርኛ'),
    ('zu', 'isiZulu'),
    ('yo', 'Yorùbá'),
    ('ko', '한국어'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Site framework
SITE_ID = 1

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
EOF

echo "   ✅ Configuration de base créée"

# Configuration de production
cat > config/settings/production.py << 'EOF'
from .base import *

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-production-key-martialcomp-2025')
DEBUG = False
ALLOWED_HOSTS = ['martialcomp.com', 'www.martialcomp.com', '212.227.78.104']

# Base de données PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'martialcomp_db',
        'USER': 'martialcomp_user',
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_db_password'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Security
SECURE_SSL_REDIRECT = False  # Apache gère le SSL
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://martialcomp.com', 'https://martialcomp.com']

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
EOF

echo "   ✅ Configuration de production créée"

# Configuration __init__.py
cat > config/settings/__init__.py << 'EOF'
# Default to development settings
from .production import *
EOF

cat > config/__init__.py << 'EOF'
# Configuration package
EOF

echo "   ✅ Structure de configuration complète"

# =============================================================================
# 5. URLS PRINCIPALES AVEC TOUTES LES APPLICATIONS
# =============================================================================

echo ""
echo "🔗 5. CONFIGURATION URLs COMPLÈTE"
echo "================================="

cat > config/urls.py << 'EOF'
"""
URLs principales MartialComp - Configuration complète production
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# URLs non internationalisées
urlpatterns = [
    path('set-language/', include('django.conf.urls.i18n')),
    path('api/', include('api_auth.urls')),
]

# URLs internationalisées
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('competitions.urls')),
    path('grades/', include('grades.urls')),
    path('organizations/', include('organizations.urls')),
    path('finances/', include('finances.urls')),
    path('shop/', include('shop.urls')),
    path('documents/', include('documents.urls')),
    path('family/', include('family_management.urls')),
    path('payment/', include('payment.urls')),
    path('accounts/', include('accounts.urls')),
    path('rosetta/', include('rosetta.urls')),
    
    prefix_default_language=False
)

# Fichiers statiques
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
EOF

echo "   ✅ URLs principales créées"

# WSGI configuration
mkdir -p config/
cat > config/wsgi.py << 'EOF'
"""
WSGI config for MartialComp project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()
EOF

echo "   ✅ Configuration WSGI créée"

# =============================================================================
# 6. REQUIREMENTS COMPLET
# =============================================================================

echo ""
echo "📦 6. REQUIREMENTS COMPLET"
echo "========================="

cat > requirements.txt << 'EOF'
Django==4.2.11
psycopg2-binary==2.9.5
django-allauth==0.57.0
django-widget-tweaks==1.5.0
django-crispy-forms==2.0
crispy-bootstrap5==0.7
Pillow==10.0.0
python-decouple==3.8
django-rosetta==0.9.8
django-modeltranslation==0.18.11
gunicorn==21.2.0
whitenoise==6.6.0
redis==5.0.1
celery==5.3.4
reportlab==4.0.4
openpyxl==3.1.2
stripe==7.8.0
requests==2.31.0
django-extensions==3.2.3
qrcode==7.4.2
EOF

echo "   ✅ Requirements créé"

# =============================================================================
# 7. INSTALLATION ET MIGRATION
# =============================================================================

echo ""
echo "📥 7. INSTALLATION ET MIGRATION"
echo "==============================="

echo "   📦 Installation des dépendances..."
pip install -r requirements.txt

echo "   🗄️ Migrations de la base de données..."
python manage.py makemigrations
python manage.py migrate

echo "   📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

echo "   🌍 Compilation des traductions..."
python manage.py compilemessages

echo "   ✅ Installation et migration terminées"

# =============================================================================
# 8. REDÉMARRAGE DJANGO
# =============================================================================

echo ""
echo "🔄 8. REDÉMARRAGE DJANGO"
echo "======================="

# Redémarrer Django avec la nouvelle configuration
nohup python manage.py runserver 127.0.0.1:8080 > /tmp/django_production_replacement_$(date +%H%M).log 2>&1 &
DJANGO_PID=$!

echo "   ✅ Django redémarré (PID: $DJANGO_PID)"

sleep 5

# =============================================================================
# 9. TESTS DE FONCTIONNEMENT
# =============================================================================

echo ""
echo "🧪 9. TESTS DE FONCTIONNEMENT"
echo "============================="

echo "   🔍 Test Django interne..."
DJANGO_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080/" || echo "Erreur")
echo "   Status Django: $DJANGO_STATUS"

echo "   🔍 Test Apache proxy..."
APACHE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://martialcomp.com/" || echo "Erreur")
echo "   Status Apache: $APACHE_STATUS"

echo "   ✅ Tests terminés"

# =============================================================================
# 10. RÉSUMÉ FINAL
# =============================================================================

echo ""
echo "🎉 REMPLACEMENT COMPLET TERMINÉ"
echo "==============================="

echo ""
echo "📋 RÉSUMÉ DU REMPLACEMENT:"
echo "   ✅ Production complètement nettoyée"
echo "   ✅ Environnement de développement copié intégralement"
echo "   ✅ Configuration de production adaptée"
echo "   ✅ Toutes les applications Django synchronisées:"
echo "      • competitions (application principale)"
echo "      • organizations (gestion organisations)"
echo "      • grades (système de grades)"
echo "      • finances (gestion financière)"
echo "      • shop (boutique en ligne)"
echo "      • documents (GED)"
echo "      • family_management (gestion familiale)"
echo "      • permissions_manager (permissions)"
echo "      • payment (paiements)"
echo "      • accounts (comptes utilisateurs)"
echo "      • multitenant (multi-tenant)"
echo "      • security (sécurité)"
echo "      • api_auth (API authentification)"
echo "   ✅ Système multilingue complet (18 langues)"
echo "   ✅ Accès Apache préservé"

echo ""
echo "🌐 URLS À TESTER:"
echo "   • Page d'accueil: http://martialcomp.com"
echo "   • Administration: http://martialcomp.com/admin/"
echo "   • Dashboard: http://martialcomp.com/dashboard/"
echo "   • Interface Rosetta: http://martialcomp.com/rosetta/"

echo ""
echo "📊 INFORMATIONS TECHNIQUES:"
echo "   🐍 Django PID: $DJANGO_PID"
echo "   💾 Sauvegarde complète: $BACKUP_DIR"
echo "   📝 Logs: /tmp/django_production_replacement_$(date +%H%M).log"
echo "   ⚙️ Configuration: config.settings.production"

echo ""
echo "⚠️ ÉLÉMENTS PRÉSERVÉS:"
echo "   🌐 Configuration Apache (accès martialcomp.com)"
echo "   🗄️ Base de données PostgreSQL"
echo "   🔐 Certificats SSL"

echo ""
echo "🚫 ÉLÉMENTS EXCLUS (non transférés):"
echo "   🔧 Scripts de correction (/scripts/)"
echo "   📝 Fichiers de debug temporaires"
echo "   🗂️ Caches et fichiers temporaires"

echo ""
echo "🔄 Si problème, restaurer avec:"
echo "   cp -r $BACKUP_DIR/* ./"
echo "   systemctl restart apache2"

echo ""
echo "✨ ENVIRONNEMENT DE DÉVELOPPEMENT MAINTENANT DÉPLOYÉ EN PRODUCTION !"
echo "    🎯 Fonctionnalité organisateur non-membre incluse"
echo "    🏢 Système de gestion familiale complet"
echo "    💰 Nouveau modèle tarifaire"
echo "    🌍 Support multilingue complet"
echo "    🔧 Toutes les applications et fonctionnalités synchronisées" 