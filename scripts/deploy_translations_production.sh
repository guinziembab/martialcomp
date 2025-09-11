#!/bin/bash

################################################################################
# Script de déploiement des traductions MartialComp en production
# Compatible avec l'infrastructure existante (Nginx + Gunicorn + PostgreSQL)
################################################################################

set -e  # Arrêt en cas d'erreur

# =============================================================================
# CONFIGURATION
# =============================================================================

PRODUCTION_PATH="/opt/martialcomp/app"
BACKUP_PATH="/opt/martialcomp/backups/translations"
LOG_FILE="/opt/martialcomp/logs/translation_deployment.log"
DJANGO_SETTINGS_MODULE="config.settings_production_final"

# Couleurs pour affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
    log "SUCCESS: $1"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
    log "WARNING: $1"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    log "ERROR: $1"
    exit 1
}

info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
    log "INFO: $1"
}

# =============================================================================
# VÉRIFICATIONS PRÉALABLES
# =============================================================================

check_prerequisites() {
    info "🔍 Vérification des prérequis..."
    
    # Vérifier les droits d'accès
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root"
    fi
    
    # Vérifier l'environnement de production
    if [ ! -d "$PRODUCTION_PATH" ]; then
        error "Répertoire de production non trouvé: $PRODUCTION_PATH"
    fi
    
    # Vérifier que les services sont en cours d'exécution
    if ! systemctl is-active --quiet nginx; then
        warning "Nginx n'est pas actif - tentative de démarrage..."
        systemctl start nginx || error "Impossible de démarrer Nginx"
    fi
    
    if ! systemctl is-active --quiet gunicorn; then
        warning "Gunicorn n'est pas actif - tentative de démarrage..."
        systemctl start gunicorn || error "Impossible de démarrer Gunicorn"
    fi
    
    # Vérifier PostgreSQL
    if ! systemctl is-active --quiet postgresql; then
        error "PostgreSQL n'est pas actif"
    fi
    
    success "Prérequis vérifiés avec succès"
}

# =============================================================================
# SAUVEGARDE
# =============================================================================

create_backup() {
    info "💾 Création de la sauvegarde..."
    
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$BACKUP_PATH/$TIMESTAMP"
    
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder les fichiers de traduction actuels
    if [ -d "$PRODUCTION_PATH/locale" ]; then
        cp -r "$PRODUCTION_PATH/locale" "$BACKUP_DIR/"
        success "Fichiers de traduction sauvegardés dans $BACKUP_DIR"
    fi
    
    # Sauvegarder les settings de production
    if [ -f "$PRODUCTION_PATH/config/settings_production_final.py" ]; then
        cp "$PRODUCTION_PATH/config/settings_production_final.py" "$BACKUP_DIR/"
        success "Settings de production sauvegardés"
    fi
    
    # Sauvegarder les fichiers statiques
    if [ -d "/opt/martialcomp/staticfiles" ]; then
        cp -r "/opt/martialcomp/staticfiles" "$BACKUP_DIR/staticfiles_backup"
        success "Fichiers statiques sauvegardés"
    fi
    
    echo "$BACKUP_DIR" > /tmp/martialcomp_backup_path
    success "Sauvegarde créée: $BACKUP_DIR"
}

# =============================================================================
# MISE À JOUR DE LA CONFIGURATION
# =============================================================================

update_production_settings() {
    info "⚙️ Mise à jour de la configuration de production..."
    
    SETTINGS_FILE="$PRODUCTION_PATH/config/settings_production_final.py"
    
    # Créer un fichier temporaire avec les ajouts d'internationalisation
    cat >> "$SETTINGS_FILE" << 'EOF'

# ===========================================
# INTERNATIONALISATION - SYSTÈME MULTILINGUE
# ===========================================

# Middleware pour la détection de langue (ajouté après SessionMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'multitenant.middleware.TenantMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # ← AJOUTÉ pour i18n
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'competitions.middleware.auto_language.AutoLanguageMiddleware',
]

# Activation de l'internationalisation
USE_I18N = True
USE_L10N = True

# Langue par défaut
LANGUAGE_CODE = 'fr'

# Langues supportées (16 langues)
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

# Chemins des fichiers de traduction
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Apps de traduction ajoutées
INSTALLED_APPS += [
    'rosetta',
    'modeltranslation',
]

# Configuration Rosetta pour production
ROSETTA_MESSAGES_PER_PAGE = 25
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = True
ROSETTA_SHOW_AT_ADMIN_PANEL = True

# Cache spécifique pour les traductions
CACHES['translations'] = {
    'BACKEND': 'django_redis.cache.RedisCache',
    'LOCATION': REDIS_URL + '/4',
    'OPTIONS': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    },
    'TIMEOUT': 3600,  # 1 heure
}

EOF

    success "Configuration de production mise à jour pour l'internationalisation"
}

# =============================================================================
# DÉPLOIEMENT DES FICHIERS DE TRADUCTION
# =============================================================================

deploy_translation_files() {
    info "📁 Déploiement des fichiers de traduction..."
    
    # Copier les fichiers de traduction depuis le développement
    if [ -d "./locale" ]; then
        cp -r ./locale "$PRODUCTION_PATH/"
        success "Fichiers de traduction copiés"
    else
        error "Répertoire locale non trouvé dans le répertoire courant"
    fi
    
    # S'assurer que les permissions sont correctes
    chown -R martialcomp:martialcomp "$PRODUCTION_PATH/locale"
    chmod -R 755 "$PRODUCTION_PATH/locale"
    
    success "Permissions des fichiers de traduction configurées"
}

# =============================================================================
# COMPILATION ET OPTIMISATION
# =============================================================================

compile_translations() {
    info "🔨 Compilation des traductions..."
    
    cd "$PRODUCTION_PATH"
    
    # Activer l'environnement virtuel
    source /opt/martialcomp/venv/bin/activate
    
    # Exporter les variables d'environnement
    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"
    
    # Compiler toutes les traductions
    python manage.py compilemessages || error "Erreur lors de la compilation des traductions"
    
    success "Traductions compilées avec succès"
}

collect_static_files() {
    info "📦 Collection des fichiers statiques..."
    
    cd "$PRODUCTION_PATH"
    source /opt/martialcomp/venv/bin/activate
    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"
    
    # Collecter les fichiers statiques (inclut les traductions JS)
    python manage.py collectstatic --noinput || error "Erreur lors de la collection des fichiers statiques"
    
    success "Fichiers statiques collectés"
}

# =============================================================================
# REDÉMARRAGE DES SERVICES
# =============================================================================

restart_services() {
    info "🔄 Redémarrage des services..."
    
    # Redémarrer Gunicorn pour recharger Django
    systemctl restart gunicorn || error "Erreur lors du redémarrage de Gunicorn"
    sleep 3
    
    # Vérifier que Gunicorn est actif
    if systemctl is-active --quiet gunicorn; then
        success "Gunicorn redémarré avec succès"
    else
        error "Gunicorn n'a pas pu redémarrer"
    fi
    
    # Recharger Nginx (sans redémarrage)
    systemctl reload nginx || warning "Erreur lors du rechargement de Nginx"
    
    # Vider le cache Redis si disponible
    if command -v redis-cli &> /dev/null; then
        redis-cli -n 1 FLUSHDB || warning "Impossible de vider le cache Redis"
        success "Cache Redis vidé"
    fi
    
    success "Services redémarrés"
}

# =============================================================================
# TESTS DE VALIDATION
# =============================================================================

validate_deployment() {
    info "🧪 Validation du déploiement..."
    
    # Test de base - vérifier que le site répond
    if curl -s -f -o /dev/null "https://martialcomp.com/"; then
        success "Site principal accessible"
    else
        error "Site principal non accessible"
    fi
    
    # Test des URLs multilingues
    for lang in fr en es it; do
        if curl -s -f -o /dev/null "https://martialcomp.com/$lang/"; then
            success "URL $lang accessible"
        else
            warning "URL $lang non accessible"
        fi
    done
    
    # Test de l'interface Rosetta
    if curl -s -f -o /dev/null "https://martialcomp.com/rosetta/"; then
        success "Interface Rosetta accessible"
    else
        warning "Interface Rosetta non accessible"
    fi
    
    success "Validation terminée"
}

# =============================================================================
# FONCTION DE ROLLBACK
# =============================================================================

rollback() {
    error "Déploiement échoué - Rollback en cours..."
    
    if [ -f /tmp/martialcomp_backup_path ]; then
        BACKUP_DIR=$(cat /tmp/martialcomp_backup_path)
        
        if [ -d "$BACKUP_DIR" ]; then
            info "Restauration depuis $BACKUP_DIR"
            
            # Restaurer les fichiers
            if [ -d "$BACKUP_DIR/locale" ]; then
                rm -rf "$PRODUCTION_PATH/locale"
                cp -r "$BACKUP_DIR/locale" "$PRODUCTION_PATH/"
            fi
            
            if [ -f "$BACKUP_DIR/settings_production_final.py" ]; then
                cp "$BACKUP_DIR/settings_production_final.py" "$PRODUCTION_PATH/config/"
            fi
            
            # Redémarrer les services
            systemctl restart gunicorn
            
            success "Rollback terminé"
        fi
    fi
    
    exit 1
}

# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

main() {
    info "🚀 DÉBUT DU DÉPLOIEMENT DES TRADUCTIONS MARTIALCOMP"
    info "================================================="
    
    # Configurer le piège pour le rollback en cas d'erreur
    trap rollback ERR
    
    # Étapes du déploiement
    check_prerequisites
    create_backup
    update_production_settings
    deploy_translation_files
    compile_translations
    collect_static_files
    restart_services
    validate_deployment
    
    success "🎉 DÉPLOIEMENT DES TRADUCTIONS TERMINÉ AVEC SUCCÈS !"
    info "================================================="
    info "URLs à tester:"
    info "• Site principal: https://martialcomp.com/"
    info "• Interface anglaise: https://martialcomp.com/en/"
    info "• Interface espagnole: https://martialcomp.com/es/"
    info "• Gestion traductions: https://martialcomp.com/rosetta/"
    
    # Nettoyer le fichier temporaire
    rm -f /tmp/martialcomp_backup_path
}

# =============================================================================
# EXÉCUTION
# =============================================================================

# Créer le répertoire de logs s'il n'existe pas
mkdir -p "/opt/martialcomp/logs"
mkdir -p "$BACKUP_PATH"

# Exécuter le script principal
main "$@"