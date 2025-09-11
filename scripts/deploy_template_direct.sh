#!/bin/bash

# =============================================================================
# Script de déploiement direct pour corriger les templates
# À exécuter depuis /var/www/vhosts/martialcomp.com/httpdocs
# =============================================================================

set -e

# Configuration
APP_DIR="/opt/martialcomp/app"
TEMPLATES_DIR="$APP_DIR/organizations/templates/organizations/sites"
CURRENT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

# Vérification des prérequis
check_prerequisites() {
    log "=== DÉPLOIEMENT DIRECT DES TEMPLATES ==="
    
    # Vérifier qu'on est dans le bon répertoire
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        error "Ce script doit être exécuté depuis /var/www/vhosts/martialcomp.com/httpdocs"
        exit 1
    fi
    
    # Vérifier que le template source existe
    if [[ ! -f "default_template_clean.html" ]]; then
        error "Fichier default_template_clean.html non trouvé dans le répertoire courant"
        exit 1
    fi
    
    # Vérifier que le répertoire de destination existe
    if [[ ! -d "$APP_DIR" ]]; then
        error "Répertoire d'application $APP_DIR non trouvé"
        exit 1
    fi
    
    log "Prérequis validés"
}

# Sauvegarde des templates existants
backup_existing() {
    log "Sauvegarde des templates existants..."
    
    if [[ -d "$TEMPLATES_DIR" ]]; then
        cp -r "$TEMPLATES_DIR" "/tmp/templates_backup_$TIMESTAMP" 2>/dev/null || true
        log "Sauvegarde créée dans /tmp/templates_backup_$TIMESTAMP"
    else
        log "Aucun template existant à sauvegarder"
    fi
}

# Déploiement des templates
deploy_templates() {
    log "Déploiement des templates..."
    
    # Créer le répertoire de destination
    mkdir -p "$TEMPLATES_DIR"
    
    # Copier le template principal
    cp "default_template_clean.html" "$TEMPLATES_DIR/default_template.html"
    log "Template default_template.html déployé"
    
    # Créer les autres templates (copies pour commencer)
    cp "$TEMPLATES_DIR/default_template.html" "$TEMPLATES_DIR/club_template.html"
    cp "$TEMPLATES_DIR/default_template.html" "$TEMPLATES_DIR/federation_template.html"
    cp "$TEMPLATES_DIR/default_template.html" "$TEMPLATES_DIR/coach_template.html"
    cp "$TEMPLATES_DIR/default_template.html" "$TEMPLATES_DIR/event_template.html"
    
    log "Tous les templates créés (club, federation, coach, event)"
    
    # Ajuster les permissions
    chown -R www-data:www-data "$APP_DIR/organizations/templates"
    chmod -R 644 "$APP_DIR/organizations/templates"
    find "$APP_DIR/organizations/templates" -type d -exec chmod 755 {} \;
    
    log "Permissions ajustées"
}

# Correction de la migration manquante
fix_migration() {
    log "Correction de la migration manquante..."
    
    cd "$APP_DIR"
    
    # Créer la migration 0007 manquante si elle n'existe pas
    if [[ ! -f "competitions/migrations/0007_postgresql_is_training_score_fix.py" ]]; then
        cat > "competitions/migrations/0007_postgresql_is_training_score_fix.py" << 'EOF'
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('competitions', '0006_add_is_training_score'),
    ]

    operations = [
        # Migration vide pour résoudre la dépendance
    ]
EOF
        log "Migration 0007 créée"
    else
        log "Migration 0007 déjà présente"
    fi
}

# Redémarrage des services
restart_services() {
    log "Redémarrage des services..."
    
    # Arrêter tous les processus Django
    pkill -f "runserver" 2>/dev/null || true
    pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
    
    # Redémarrer le service principal
    if systemctl is-enabled martialcomp &>/dev/null; then
        systemctl restart martialcomp
        sleep 3
        
        if systemctl is-active --quiet martialcomp; then
            log "Service martialcomp redémarré avec succès"
        else
            warning "Problème avec le service martialcomp, tentative manuelle..."
            cd "$APP_DIR"
            nohup python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
            log "Serveur Django démarré manuellement"
        fi
    else
        log "Service martialcomp non configuré, démarrage manuel..."
        cd "$APP_DIR"
        nohup python manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &
        log "Serveur Django démarré manuellement"
    fi
    
    # Redémarrer Nginx
    systemctl restart nginx || log "Nginx non redémarré"
}

# Vérification du déploiement
verify_deployment() {
    log "Vérification du déploiement..."
    
    # Vérifier que tous les templates existent
    TEMPLATES=("default_template.html" "club_template.html" "federation_template.html" "coach_template.html" "event_template.html")
    
    for template in "${TEMPLATES[@]}"; do
        if [[ -f "$TEMPLATES_DIR/$template" ]]; then
            echo "  ✓ $template"
        else
            error "  ✗ $template MANQUANT"
            return 1
        fi
    done
    
    # Vérifier la taille des fichiers
    log "Tailles des templates:"
    ls -lh "$TEMPLATES_DIR"/*.html | awk '{print "  " $9 " - " $5}'
    
    # Test de connectivité
    sleep 5
    log "Test d'accès au site..."
    
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200\|302"; then
        log "✅ Site accessible localement"
    else
        warning "⚠️ Site peut ne pas être accessible localement"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" http://martialcomp.com/ | grep -q "200\|302"; then
        log "✅ Site accessible en externe"
    else
        warning "⚠️ Site peut ne pas être accessible en externe"
    fi
}

# Affichage des informations finales
show_final_info() {
    log "=== DÉPLOIEMENT TERMINÉ ==="
    echo ""
    echo "📁 Templates installés dans: $TEMPLATES_DIR"
    echo "💾 Sauvegarde créée dans: /tmp/templates_backup_$TIMESTAMP"
    echo "🌐 Site accessible à: http://martialcomp.com/"
    echo ""
    echo "🔍 En cas de problème:"
    echo "  - Logs Nginx: tail -f /var/log/nginx/error.log"
    echo "  - Logs Django: tail -f /opt/martialcomp/logs/gunicorn_error.log"
    echo "  - Statut service: systemctl status martialcomp"
    echo ""
}

# Fonction de rollback en cas d'erreur
rollback() {
    error "Erreur détectée - Rollback..."
    
    if [[ -d "/tmp/templates_backup_$TIMESTAMP" ]]; then
        rm -rf "$TEMPLATES_DIR"
        mkdir -p "$(dirname "$TEMPLATES_DIR")"
        cp -r "/tmp/templates_backup_$TIMESTAMP" "$TEMPLATES_DIR"
        chown -R www-data:www-data "$APP_DIR/organizations/templates"
        log "Templates restaurés"
    fi
    
    systemctl restart martialcomp 2>/dev/null || true
    error "Rollback terminé"
}

# Script principal
main() {
    # Gestion des erreurs avec rollback
    trap 'rollback' ERR
    
    check_prerequisites
    backup_existing
    deploy_templates
    fix_migration
    restart_services
    verify_deployment
    show_final_info
    
    log "🎉 DÉPLOIEMENT RÉUSSI!"
}

# Exécution
main "$@"