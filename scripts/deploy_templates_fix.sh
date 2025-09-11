#!/bin/bash

# =============================================================================
# Script de déploiement d'urgence pour corriger les templates manquants
# Résout l'erreur TemplateDoesNotExist sur le serveur de production
# =============================================================================

set -e

# Configuration
PRODUCTION_SERVER="martialcomp.com"
PRODUCTION_USER="root"
REMOTE_DIR="/var/www/martialcomp"
LOCAL_PROJECT_DIR="/mnt/c/martial_hub_django/martialcomp"
BACKUP_DIR="/var/backups/martialcomp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonction de logging
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Vérification des prérequis
check_prerequisites() {
    log "Vérification des prérequis..."
    
    # Vérifier SSH
    if ! command -v ssh &> /dev/null; then
        error "SSH n'est pas installé"
        exit 1
    fi
    
    # Vérifier rsync
    if ! command -v rsync &> /dev/null; then
        error "rsync n'est pas installé"
        exit 1
    fi
    
    # Vérifier la connectivité SSH
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes $PRODUCTION_USER@$PRODUCTION_SERVER exit 2>/dev/null; then
        error "Impossible de se connecter au serveur de production"
        exit 1
    fi
    
    # Vérifier que les templates existent localement
    if [ ! -d "$LOCAL_PROJECT_DIR/organizations/templates/organizations/sites" ]; then
        error "Répertoire des templates sites non trouvé localement"
        exit 1
    fi
    
    # Vérifier les templates requis
    REQUIRED_TEMPLATES=(
        "default_template.html"
        "club_template.html" 
        "federation_template.html"
        "coach_template.html"
        "event_template.html"
    )
    
    for template in "${REQUIRED_TEMPLATES[@]}"; do
        if [ ! -f "$LOCAL_PROJECT_DIR/organizations/templates/organizations/sites/$template" ]; then
            error "Template manquant: $template"
            exit 1
        fi
    done
    
    log "Tous les prérequis sont remplis"
}

# Création de la sauvegarde
create_backup() {
    log "Création de la sauvegarde des templates existants..."
    
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER << EOF
        # Créer le répertoire de sauvegarde
        mkdir -p $BACKUP_DIR/templates_backup_$TIMESTAMP
        
        # Sauvegarder les templates existants s'ils existent
        if [ -d "$REMOTE_DIR/organizations/templates" ]; then
            cp -r $REMOTE_DIR/organizations/templates/* $BACKUP_DIR/templates_backup_$TIMESTAMP/ 2>/dev/null || true
            echo "Sauvegarde créée dans $BACKUP_DIR/templates_backup_$TIMESTAMP"
        else
            echo "Aucun template existant à sauvegarder"
        fi
EOF
    
    log "Sauvegarde terminée"
}

# Déploiement des templates
deploy_templates() {
    log "Déploiement des nouveaux templates..."
    
    # Créer le répertoire sur le serveur de production
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER << EOF
        # Créer les répertoires nécessaires
        mkdir -p $REMOTE_DIR/organizations/templates/organizations/sites
        chown -R www-data:www-data $REMOTE_DIR/organizations/templates
EOF
    
    # Copier les templates
    log "Copie des templates vers le serveur..."
    rsync -avz --delete \
        $LOCAL_PROJECT_DIR/organizations/templates/organizations/sites/ \
        $PRODUCTION_USER@$PRODUCTION_SERVER:$REMOTE_DIR/organizations/templates/organizations/sites/
    
    # Ajuster les permissions
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER << EOF
        # Ajuster les permissions
        chown -R www-data:www-data $REMOTE_DIR/organizations/templates
        chmod -R 644 $REMOTE_DIR/organizations/templates
        find $REMOTE_DIR/organizations/templates -type d -exec chmod 755 {} \;
        
        echo "Templates déployés avec succès"
EOF
    
    log "Déploiement des templates terminé"
}

# Vérification du déploiement
verify_deployment() {
    log "Vérification du déploiement..."
    
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER << EOF
        echo "Vérification des templates déployés:"
        
        TEMPLATES_DIR="$REMOTE_DIR/organizations/templates/organizations/sites"
        
        if [ ! -d "\$TEMPLATES_DIR" ]; then
            echo "ERREUR: Répertoire des templates non trouvé"
            exit 1
        fi
        
        # Vérifier chaque template requis
        TEMPLATES=(
            "default_template.html"
            "club_template.html"
            "federation_template.html" 
            "coach_template.html"
            "event_template.html"
        )
        
        ALL_OK=true
        for template in "\${TEMPLATES[@]}"; do
            if [ -f "\$TEMPLATES_DIR/\$template" ]; then
                echo "✓ \$template trouvé"
            else
                echo "✗ \$template MANQUANT"
                ALL_OK=false
            fi
        done
        
        if [ "\$ALL_OK" = true ]; then
            echo "✅ Tous les templates sont présents"
        else
            echo "❌ Certains templates sont manquants"
            exit 1
        fi
EOF
    
    log "Vérification terminée avec succès"
}

# Redémarrage des services
restart_services() {
    log "Redémarrage des services Django..."
    
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER << EOF
        # Redémarrer Gunicorn
        systemctl restart gunicorn
        
        # Vérifier le statut
        if systemctl is-active --quiet gunicorn; then
            echo "✅ Gunicorn redémarré avec succès"
        else
            echo "❌ Erreur lors du redémarrage de Gunicorn"
            systemctl status gunicorn
        fi
        
        # Redémarrer Nginx
        systemctl restart nginx
        
        # Vérifier le statut
        if systemctl is-active --quiet nginx; then
            echo "✅ Nginx redémarré avec succès"
        else
            echo "❌ Erreur lors du redémarrage de Nginx"
            systemctl status nginx
        fi
EOF
    
    log "Services redémarrés"
}

# Test de connectivité
test_site() {
    log "Test de l'accès au site..."
    
    # Attendre que les services redémarrent
    sleep 5
    
    # Test simple de connectivité
    if curl -s -o /dev/null -w "%{http_code}" http://martialcomp.com/ | grep -q "200\|302"; then
        log "✅ Site accessible - Test réussi"
    else
        warning "⚠️  Site peut ne pas être complètement fonctionnel"
        info "Vérifiez manuellement : http://martialcomp.com/"
    fi
}

# Fonction de rollback en cas d'erreur
rollback() {
    error "Erreur détectée - Lancement du rollback..."
    
    ssh $PRODUCTION_USER@$PRODUCTION_SERVER << EOF
        # Restaurer la sauvegarde si elle existe
        if [ -d "$BACKUP_DIR/templates_backup_$TIMESTAMP" ]; then
            rm -rf $REMOTE_DIR/organizations/templates
            mkdir -p $REMOTE_DIR/organizations/templates/organizations
            cp -r $BACKUP_DIR/templates_backup_$TIMESTAMP/* $REMOTE_DIR/organizations/templates/organizations/ 2>/dev/null || true
            chown -R www-data:www-data $REMOTE_DIR/organizations/templates
            
            # Redémarrer les services
            systemctl restart gunicorn nginx
            
            echo "Rollback terminé"
        else
            echo "Aucune sauvegarde trouvée pour le rollback"
        fi
EOF
}

# Script principal
main() {
    log "=========================================="
    log "DÉPLOIEMENT D'URGENCE - TEMPLATES SITES"
    log "=========================================="
    
    # Gestion des erreurs avec rollback automatique
    trap 'rollback' ERR
    
    check_prerequisites
    create_backup
    deploy_templates
    verify_deployment
    restart_services
    test_site
    
    log "=========================================="
    log "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS"
    log "=========================================="
    
    echo ""
    info "Le site devrait maintenant être accessible à:"
    info "https://martialcomp.com/"
    echo ""
    info "Sauvegarde créée dans: $BACKUP_DIR/templates_backup_$TIMESTAMP"
    echo ""
}

# Exécution du script
main "$@"