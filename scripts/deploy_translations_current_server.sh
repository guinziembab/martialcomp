#!/bin/bash

################################################################################
# Script de déploiement des traductions MartialComp - Serveur actuel
# Adapté pour /var/www/vhosts/martialcomp.com/httpdocs/
################################################################################

set -e  # Arrêt en cas d'erreur

# =============================================================================
# CONFIGURATION - ADAPTÉE À L'ENVIRONNEMENT ACTUEL
# =============================================================================

PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_PATH="/var/www/vhosts/martialcomp.com/backups/translations"
LOG_FILE="/var/www/vhosts/martialcomp.com/logs/translation_deployment.log"
VENV_PATH="/var/www/vhosts/martialcomp.com/httpdocs/venv"

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
    info "🔍 Vérification des prérequis sur le serveur actuel..."
    
    # Vérifier les droits d'accès
    if [[ $EUID -ne 0 ]]; then
        error "Ce script doit être exécuté en tant que root"
    fi
    
    # Vérifier l'environnement de production actuel
    if [ ! -d "$PRODUCTION_PATH" ]; then
        error "Répertoire de production non trouvé: $PRODUCTION_PATH"
    fi
    
    # Vérifier l'environnement virtuel
    if [ ! -d "$VENV_PATH" ]; then
        error "Environnement virtuel non trouvé: $VENV_PATH"
    fi
    
    # Vérifier que manage.py existe
    if [ ! -f "$PRODUCTION_PATH/manage.py" ]; then
        error "manage.py non trouvé dans $PRODUCTION_PATH"
    fi
    
    # Vérifier les services
    if ! systemctl is-active --quiet nginx; then
        warning "Nginx n'est pas actif"
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
    
    # Sauvegarder les settings actuels
    if [ -f "$PRODUCTION_PATH/config/settings.py" ]; then
        cp "$PRODUCTION_PATH/config/settings.py" "$BACKUP_DIR/"
        success "Settings sauvegardés"
    fi
    
    echo "$BACKUP_DIR" > /tmp/martialcomp_backup_path
    success "Sauvegarde créée: $BACKUP_DIR"
}

# =============================================================================
# MISE À JOUR DE LA CONFIGURATION
# =============================================================================

update_current_settings() {
    info "⚙️ Mise à jour de la configuration actuelle..."
    
    SETTINGS_FILE="$PRODUCTION_PATH/config/settings.py"
    
    # Vérifier si les paramètres i18n sont déjà présents
    if grep -q "USE_I18N = True" "$SETTINGS_FILE"; then
        success "Configuration i18n déjà présente"
    else
        # Ajouter la configuration i18n
        cat >> "$SETTINGS_FILE" << 'EOF'

# ===========================================
# INTERNATIONALISATION - SYSTÈME MULTILINGUE  
# ===========================================

# Activation de l'internationalisation
USE_I18N = True
USE_L10N = True

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

EOF
        success "Configuration i18n ajoutée à settings.py"
    fi
    
    # Mettre à jour INSTALLED_APPS si nécessaire
    if ! grep -q "rosetta" "$SETTINGS_FILE"; then
        # Ajouter rosetta et modeltranslation aux INSTALLED_APPS
        sed -i '/INSTALLED_APPS = \[/,/\]/ {
            /\]/i\    '"'"'rosetta'"'"',
            /\]/i\    '"'"'modeltranslation'"'"',
        }' "$SETTINGS_FILE"
        success "Applications de traduction ajoutées"
    fi
    
    # Mettre à jour MIDDLEWARE si nécessaire  
    if ! grep -q "django.middleware.locale.LocaleMiddleware" "$SETTINGS_FILE"; then
        sed -i '/django.contrib.sessions.middleware.SessionMiddleware/a\    '"'"'django.middleware.locale.LocaleMiddleware'"'"',' "$SETTINGS_FILE"
        success "LocaleMiddleware ajouté"
    fi
}

# =============================================================================
# COMPILATION ET OPTIMISATION
# =============================================================================

compile_translations() {
    info "🔨 Compilation des traductions..."
    
    cd "$PRODUCTION_PATH"
    
    # Activer l'environnement virtuel
    source "$VENV_PATH/bin/activate"
    
    # Compiler toutes les traductions
    python manage.py compilemessages || error "Erreur lors de la compilation des traductions"
    
    success "Traductions compilées avec succès"
}

collect_static_files() {
    info "📦 Collection des fichiers statiques..."
    
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    
    # Collecter les fichiers statiques
    python manage.py collectstatic --noinput || warning "Erreur lors de la collection des fichiers statiques"
    
    success "Fichiers statiques collectés"
}

# =============================================================================
# REDÉMARRAGE DES SERVICES
# =============================================================================

restart_services() {
    info "🔄 Redémarrage des services..."
    
    # Si un serveur Django tourne en arrière-plan, le redémarrer
    pkill -f "python.*manage.py.*runserver" || true
    sleep 2
    
    # Redémarrer le serveur Django en arrière-plan
    cd "$PRODUCTION_PATH"
    source "$VENV_PATH/bin/activate"
    nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &
    
    success "Serveur Django redémarré"
    
    # Recharger Nginx si disponible
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx || warning "Erreur lors du rechargement de Nginx"
        success "Nginx rechargé"
    fi
}

# =============================================================================
# TESTS DE VALIDATION
# =============================================================================

validate_deployment() {
    info "🧪 Validation du déploiement..."
    
    # Attendre que le serveur démarre
    sleep 5
    
    # Test de base - vérifier que le serveur Django répond
    if curl -s -f -o /dev/null "http://localhost:8000/"; then
        success "Serveur Django accessible"
    else
        warning "Serveur Django non accessible sur le port 8000"
    fi
    
    # Test des URLs multilingues via le serveur externe
    for lang in fr en es it; do
        if curl -s -f -o /dev/null "https://martialcomp.com/$lang/"; then
            success "URL $lang accessible"
        else
            warning "URL $lang non accessible"
        fi
    done
    
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
            
            if [ -f "$BACKUP_DIR/settings.py" ]; then
                cp "$BACKUP_DIR/settings.py" "$PRODUCTION_PATH/config/"
            fi
            
            # Redémarrer le serveur
            pkill -f "python.*manage.py.*runserver" || true
            cd "$PRODUCTION_PATH"
            source "$VENV_PATH/bin/activate"
            nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &
            
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
    info "Environment: $PRODUCTION_PATH"
    info "================================================="
    
    # Configurer le piège pour le rollback en cas d'erreur
    trap rollback ERR
    
    # Étapes du déploiement
    check_prerequisites
    create_backup
    update_current_settings
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
    info "• Serveur Django local: http://localhost:8000/"
    
    # Nettoyer le fichier temporaire
    rm -f /tmp/martialcomp_backup_path
}

# =============================================================================
# EXÉCUTION
# =============================================================================

# Créer les répertoires de logs et backup s'ils n'existent pas
mkdir -p "/var/www/vhosts/martialcomp.com/logs"
mkdir -p "$BACKUP_PATH"

# Exécuter le script principal
main "$@"