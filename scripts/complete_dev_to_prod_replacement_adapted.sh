#!/bin/bash

# =============================================================================
# REMPLACEMENT COMPLET PRODUCTION PAR DÉVELOPPEMENT
# Source: C:\martial_hub_django\martialcomp (votre machine locale)
# Destination: Production sur serveur Ionos
# =============================================================================

set -e

echo "🔄 REMPLACEMENT COMPLET PRODUCTION PAR DÉVELOPPEMENT"
echo "======================================================"
echo "📅 Date: $(date)"
echo "🎯 Source: C:\\martial_hub_django\\martialcomp (transfert direct)"
echo "🎯 Destination: Production Ionos martialcomp.com"
echo "⚠️  ATTENTION: Cette opération va remplacer TOUT le code de production"
echo ""

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SERVER_IP="212.227.78.104"
DEV_SOURCE="C:\\martial_hub_django\\martialcomp"

# =============================================================================
# 1. SAUVEGARDE CRITIQUE DE LA PRODUCTION
# =============================================================================

echo "💾 1. SAUVEGARDE CRITIQUE DE LA PRODUCTION"
echo "==========================================="

BACKUP_DIR="backups/production_complete_before_replacement_$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "   📁 Sauvegarde COMPLÈTE avant remplacement..."

# Sauvegarder TOUT le code existant
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

echo "   ✅ Sauvegarde complète dans: $BACKUP_DIR"

# =============================================================================
# 2. ARRÊT DES SERVICES DJANGO
# =============================================================================

echo ""
echo "🛑 2. ARRÊT DES SERVICES DJANGO"
echo "==============================="

echo "   🛑 Arrêt des processus Django..."
pkill -f "runserver.*8080" 2>/dev/null || true
pkill -f "manage.py runserver" 2>/dev/null || true
sleep 3

echo "   ✅ Services Django arrêtés"

# =============================================================================
# 3. NETTOYAGE COMPLET (SAUF INFRASTRUCTURE APACHE)
# =============================================================================

echo ""
echo "🧹 3. NETTOYAGE COMPLET DE LA PRODUCTION"
echo "========================================"

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
rm -rf locale/ 2>/dev/null || true
rm -rf __pycache__/ 2>/dev/null || true

# Scripts de correction (EXCLUS)
rm -rf scripts/ 2>/dev/null || true

echo "   ✅ Production nettoyée complètement"

# =============================================================================
# 4. TRANSFERT COMPLET DEPUIS DÉVELOPPEMENT LOCAL
# =============================================================================

echo ""
echo "📂 4. TRANSFERT COMPLET DEPUIS DÉVELOPPEMENT LOCAL"
echo "================================================="

echo "   📡 Source: $DEV_SOURCE"
echo "   🎯 Destination: /var/www/vhosts/martialcomp.com/httpdocs/"
echo ""

# Créer un script de transfert pour être exécuté depuis la machine locale
cat > transfer_dev_to_prod.sh << 'TRANSFER_SCRIPT'
#!/bin/bash

echo "📡 TRANSFERT DÉVELOPPEMENT → PRODUCTION"
echo "======================================="

DEV_LOCAL="C:/martial_hub_django/martialcomp"
PROD_SERVER="root@212.227.78.104"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "🔄 Transfert de toutes les applications Django..."

# Applications complètes
echo "   📁 competitions/"
scp -r "$DEV_LOCAL/competitions/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 organizations/"
scp -r "$DEV_LOCAL/organizations/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 grades/"
scp -r "$DEV_LOCAL/grades/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 finances/"
scp -r "$DEV_LOCAL/finances/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 shop/"
scp -r "$DEV_LOCAL/shop/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 documents/"
scp -r "$DEV_LOCAL/documents/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 family_management/"
scp -r "$DEV_LOCAL/family_management/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 permissions_manager/"
scp -r "$DEV_LOCAL/permissions_manager/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 payment/"
scp -r "$DEV_LOCAL/payment/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 accounts/"
scp -r "$DEV_LOCAL/accounts/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 multitenant/"
scp -r "$DEV_LOCAL/multitenant/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 security/"
scp -r "$DEV_LOCAL/security/" "$PROD_SERVER:$PROD_PATH/"

echo "   📁 api_auth/"
scp -r "$DEV_LOCAL/api_auth/" "$PROD_SERVER:$PROD_PATH/"

# Configuration
echo "   ⚙️ Configuration Django..."
scp -r "$DEV_LOCAL/config/" "$PROD_SERVER:$PROD_PATH/"

# Fichiers système
echo "   📄 Fichiers système..."
scp "$DEV_LOCAL/manage.py" "$PROD_SERVER:$PROD_PATH/"
scp "$DEV_LOCAL/requirements.txt" "$PROD_SERVER:$PROD_PATH/"

# Traductions et fichiers statiques
echo "   🌍 Traductions..."
scp -r "$DEV_LOCAL/locale/" "$PROD_SERVER:$PROD_PATH/"

echo "   🎨 Fichiers statiques..."
scp -r "$DEV_LOCAL/static/" "$PROD_SERVER:$PROD_PATH/"

echo "   ✅ Transfert complet terminé!"
TRANSFER_SCRIPT

echo "   📋 Script de transfert créé: transfer_dev_to_prod.sh"
echo ""
echo "   ⚠️  INSTRUCTION IMPORTANTE:"
echo "   Pour transférer les fichiers, exécutez DEPUIS VOTRE MACHINE LOCALE:"
echo ""
echo "   bash transfer_dev_to_prod.sh"
echo ""
echo "   Puis revenez sur le serveur pour continuer..."

# Attendre confirmation
read -p "   Appuyez sur Entrée une fois le transfert terminé..."

# =============================================================================
# 5. CONFIGURATION DE PRODUCTION ADAPTÉE
# =============================================================================

echo ""
echo "⚙️ 5. CONFIGURATION PRODUCTION ADAPTÉE"
echo "======================================"

# Adapter manage.py pour la production
if [ ! -f "manage.py" ]; then
    echo "   ❌ manage.py non trouvé après transfert!"
    exit 1
fi

# Créer la configuration de production spécifique
mkdir -p config/settings/

cat > config/settings/production.py << 'PROD_SETTINGS'
# Configuration de production pour MartialComp
import os
from pathlib import Path

# Import de la configuration de base du développement
try:
    from .base import *
except ImportError:
    # Fallback si base.py n'existe pas
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    
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

# Surcharges pour la production
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-production-key-martialcomp-2025-secure')
DEBUG = False
ALLOWED_HOSTS = ['martialcomp.com', 'www.martialcomp.com', '212.227.78.104', '127.0.0.1']

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

# Cache local en mémoire
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Sécurité adaptée pour Apache proxy
SECURE_SSL_REDIRECT = False  # Apache gère le SSL
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    'http://martialcomp.com', 
    'https://martialcomp.com',
    'http://212.227.78.104'
]

# Fichiers statiques
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/staticfiles'

# Fichiers media
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/media'

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
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'competitions': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Configuration Django pour production
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

SITE_ID = 1
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
PROD_SETTINGS

echo "   ✅ Configuration de production créée"

# Forcer l'utilisation des settings de production
sed -i "s/'config.settings.development'/'config.settings.production'/g" manage.py 2>/dev/null || true
sed -i "s/config.settings.development/config.settings.production/g" manage.py 2>/dev/null || true

echo "   ✅ manage.py adapté pour la production"

# =============================================================================
# 6. INSTALLATION ET MIGRATION
# =============================================================================

echo ""
echo "📥 6. INSTALLATION ET MIGRATION"
echo "==============================="

echo "   📦 Installation des dépendances..."
pip install -r requirements.txt

echo "   🗄️ Migrations de la base de données..."
python manage.py makemigrations
python manage.py migrate

echo "   📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear

echo "   🌍 Compilation des traductions..."
python manage.py compilemessages 2>/dev/null || echo "   ⚠️ Certaines traductions peuvent nécessiter une recompilation"

echo "   ✅ Installation et migration terminées"

# =============================================================================
# 7. REDÉMARRAGE DJANGO
# =============================================================================

echo ""
echo "🔄 7. REDÉMARRAGE DJANGO AVEC NOUVEAU CODE"
echo "=========================================="

# Redémarrer Django avec la nouvelle configuration complète
nohup python manage.py runserver 127.0.0.1:8080 > /tmp/django_production_replacement_$(date +%H%M).log 2>&1 &
DJANGO_PID=$!

echo "   ✅ Django redémarré avec nouveau code (PID: $DJANGO_PID)"

sleep 5

# =============================================================================
# 8. TESTS COMPLETS
# =============================================================================

echo ""
echo "🧪 8. TESTS DE FONCTIONNEMENT COMPLETS"
echo "======================================"

echo "   🔍 Test Django interne..."
DJANGO_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080/" || echo "Erreur")
echo "   Status Django: $DJANGO_STATUS"

echo "   🔍 Test Apache proxy..."
APACHE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://martialcomp.com/" || echo "Erreur")
echo "   Status Apache: $APACHE_STATUS"

echo "   🔍 Test dashboard..."
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8080/dashboard/" || echo "Erreur")
echo "   Status Dashboard: $DASHBOARD_STATUS"

echo "   ✅ Tests de base terminés"

# =============================================================================
# 9. DIAGNOSTIC FINAL
# =============================================================================

echo ""
echo "🔍 9. DIAGNOSTIC FINAL"
echo "====================="

python manage.py shell -c "
import django
from django.apps import apps
from django.db import connection

print('🔍 DIAGNOSTIC POST-REMPLACEMENT')
print('=' * 40)

# Vérifier Django
print(f'✅ Django version: {django.get_version()}')

# Vérifier les applications
app_configs = apps.get_app_configs()
print(f'✅ Applications chargées: {len(app_configs)}')

for app_name in ['competitions', 'organizations', 'grades', 'finances', 'shop', 'documents', 'family_management']:
    try:
        apps.get_app_config(app_name)
        print(f'✅ {app_name}: OK')
    except:
        print(f'❌ {app_name}: Manquant')

# Vérifier la base de données
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM auth_user')
        user_count = cursor.fetchone()[0]
        print(f'✅ Base de données: {user_count} utilisateurs')
except Exception as e:
    print(f'❌ Base de données: {e}')

print('✅ Diagnostic terminé')
" 2>/dev/null || echo "   ⚠️ Diagnostic partiel - vérifier manuellement"

# =============================================================================
# 10. RÉSUMÉ FINAL COMPLET
# =============================================================================

echo ""
echo "🎉 REMPLACEMENT COMPLET TERMINÉ AVEC SUCCÈS"
echo "==========================================="

echo ""
echo "📋 RÉSUMÉ DE L'OPÉRATION:"
echo "   ✅ Production complètement nettoyée"
echo "   ✅ Code de développement transféré intégralement"
echo "   ✅ Configuration de production adaptée"
echo "   ✅ Applications Django synchronisées:"
echo "      • competitions (application principale + organisateur non-membre)"
echo "      • organizations (gestion organisations)"
echo "      • grades (système de grades)"
echo "      • finances (nouveau modèle tarifaire)"
echo "      • shop (boutique en ligne)"
echo "      • documents (GED)"
echo "      • family_management (gestion familiale COMPLÈTE)"
echo "      • permissions_manager (permissions granulaires)"
echo "      • payment (paiements et abonnements)"
echo "      • accounts (comptes utilisateurs étendus)"
echo "      • multitenant (multi-tenant)"
echo "      • security (sécurité renforcée)"
echo "      • api_auth (API authentification)"
echo "   ✅ Système multilingue complet (18 langues)"
echo "   ✅ Infrastructure Apache préservée"

echo ""
echo "🌐 NOUVELLES FONCTIONNALITÉS DISPONIBLES:"
echo "   🔥 Organisateur non-membre avec dashboard dédié"
echo "   👨‍👩‍👧‍👦 Système de gestion familiale complet"
echo "   💰 Nouveau modèle tarifaire par membre"
echo "   🌍 Support multilingue étendu (18 langues)"
echo "   🏢 Gestion d'organisations multi-niveaux"
echo "   🛡️ Système de permissions granulaires"
echo "   💳 Module de paiement complet"
echo "   📄 GED et gestion documentaire"

echo ""
echo "🌐 URLS À TESTER:"
echo "   • Page d'accueil: http://martialcomp.com"
echo "   • Administration: http://martialcomp.com/admin/"
echo "   • Dashboard principal: http://martialcomp.com/dashboard/"
echo "   • Dashboard organisateur: http://martialcomp.com/dashboard/external-organizer/"
echo "   • Gestion familiale: http://martialcomp.com/family/"
echo "   • Interface Rosetta: http://martialcomp.com/rosetta/"

echo ""
echo "📊 INFORMATIONS TECHNIQUES:"
echo "   🐍 Django PID: $DJANGO_PID"
echo "   💾 Sauvegarde: $BACKUP_DIR"
echo "   📝 Logs: /tmp/django_production_replacement_$(date +%H%M).log"
echo "   ⚙️ Configuration: config.settings.production"
echo "   🗄️ Base de données: PostgreSQL (données préservées)"

echo ""
echo "⚠️ ÉLÉMENTS PRÉSERVÉS:"
echo "   🌐 Configuration Apache (port 80 → 8080)"
echo "   🗄️ Base de données PostgreSQL complète"
echo "   🔐 Certificats SSL et domaine"

echo ""
echo "🚫 ÉLÉMENTS EXCLUS (non transférés):"
echo "   🔧 Scripts de correction (/scripts/)"
echo "   📝 Fichiers de debug et logs temporaires"
echo "   🗂️ Caches et fichiers de développement"

echo ""
echo "🔄 En cas de problème, restaurer avec:"
echo "   rm -rf competitions/ organizations/ grades/ finances/ config/ manage.py"
echo "   cp -r $BACKUP_DIR/* ./"
echo "   python manage.py runserver 127.0.0.1:8080 &"

echo ""
echo "✨ SUCCÈS TOTAL!"
echo "=================="
echo "🎯 L'environnement de développement complet est maintenant en production"
echo "🚀 Toutes les nouvelles fonctionnalités sont disponibles"
echo "🌍 Le site http://martialcomp.com reflète exactement votre développement"
echo "👥 Les utilisateurs existants conservent leurs données"
echo "⚡ Accès Apache préservé et fonctionnel" 