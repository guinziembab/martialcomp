#!/bin/bash

# =============================================================================
# Script de déploiement de la modernisation de l'authentification
# Déploie les nouvelles fonctionnalités d'authentification sur le serveur de production
# =============================================================================

set -e  # Arrêter le script en cas d'erreur

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
NC='\033[0m' # No Color

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
    
    # Vérifier la connexion SSH
    if ! ssh -o ConnectTimeout=5 -o BatchMode=yes "$PRODUCTION_USER@$PRODUCTION_SERVER" exit &> /dev/null; then
        error "Impossible de se connecter au serveur de production via SSH"
        error "Vérifiez vos clés SSH et la connectivité"
        exit 1
    fi
    
    log "Prérequis vérifiés avec succès"
}

# Créer une sauvegarde de sécurité
create_backup() {
    log "Création d'une sauvegarde de sécurité..."
    
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" << EOF
        # Créer le répertoire de backup s'il n'existe pas
        mkdir -p $BACKUP_DIR
        
        # Sauvegarder les fichiers modifiés
        echo "Sauvegarde des templates d'authentification..."
        cp -r $REMOTE_DIR/competitions/templates/registration $BACKUP_DIR/registration_backup_$TIMESTAMP || true
        
        echo "Sauvegarde des vues d'authentification..."
        cp $REMOTE_DIR/competitions/views/auth.py $BACKUP_DIR/auth_views_backup_$TIMESTAMP.py || true
        
        echo "Sauvegarde des fichiers statiques..."
        mkdir -p $BACKUP_DIR/static_backup_$TIMESTAMP
        cp -r $REMOTE_DIR/competitions/static/css $BACKUP_DIR/static_backup_$TIMESTAMP/ || true
        
        echo "Sauvegarde créée dans $BACKUP_DIR avec timestamp $TIMESTAMP"
EOF
    
    log "Sauvegarde créée avec succès"
}

# Synchroniser les fichiers modifiés
sync_files() {
    log "Synchronisation des fichiers vers la production..."
    
    # Copier les templates d'authentification
    info "Synchronisation des templates..."
    rsync -avz --progress \
        "$LOCAL_PROJECT_DIR/competitions/templates/registration/" \
        "$PRODUCTION_USER@$PRODUCTION_SERVER:$REMOTE_DIR/competitions/templates/registration/"
    
    # Copier les vues d'authentification
    info "Synchronisation des vues..."
    rsync -avz --progress \
        "$LOCAL_PROJECT_DIR/competitions/views/auth.py" \
        "$PRODUCTION_USER@$PRODUCTION_SERVER:$REMOTE_DIR/competitions/views/auth.py"
    
    # Copier les fichiers CSS
    info "Synchronisation des fichiers CSS..."
    rsync -avz --progress \
        "$LOCAL_PROJECT_DIR/competitions/static/css/auth.css" \
        "$PRODUCTION_USER@$PRODUCTION_SERVER:$REMOTE_DIR/competitions/static/css/auth.css"
    
    log "Synchronisation des fichiers terminée"
}

# Collecter les fichiers statiques
collect_static() {
    log "Collecte des fichiers statiques en production..."
    
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" << EOF
        cd $REMOTE_DIR
        
        # Activer l'environnement virtuel
        source venv/bin/activate
        
        # Collecter les fichiers statiques
        python manage.py collectstatic --noinput
        
        echo "Fichiers statiques collectés avec succès"
EOF
    
    log "Collecte des fichiers statiques terminée"
}

# Redémarrer les services
restart_services() {
    log "Redémarrage des services en production..."
    
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" << EOF
        # Redémarrer Gunicorn
        echo "Redémarrage de Gunicorn..."
        systemctl restart gunicorn || service gunicorn restart
        
        # Redémarrer Nginx
        echo "Redémarrage de Nginx..."
        systemctl restart nginx || service nginx restart
        
        echo "Services redémarrés avec succès"
EOF
    
    log "Services redémarrés"
}

# Vérifier le déploiement
verify_deployment() {
    log "Vérification du déploiement..."
    
    # Test de connectivité
    info "Test de connectivité HTTP..."
    if curl -f -s -o /dev/null "https://$PRODUCTION_SERVER/"; then
        log "Site accessible via HTTPS"
    else
        warning "Problème d'accès HTTPS détecté"
    fi
    
    # Vérifier les logs d'erreur
    info "Vérification des logs d'erreur récents..."
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" << 'EOF'
        echo "Dernières erreurs Nginx:"
        tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "Aucun log d'erreur Nginx trouvé"
        
        echo "Dernières erreurs Gunicorn:"
        tail -n 5 /var/log/gunicorn/error.log 2>/dev/null || echo "Aucun log d'erreur Gunicorn trouvé"
        
        echo "Status des services:"
        systemctl is-active gunicorn nginx || true
EOF
    
    log "Vérification du déploiement terminée"
}

# Fonction de rollback en cas de problème
rollback() {
    error "Rollback en cours..."
    
    ssh "$PRODUCTION_USER@$PRODUCTION_SERVER" << EOF
        cd $REMOTE_DIR
        
        # Restaurer les fichiers depuis la sauvegarde
        if [ -d "$BACKUP_DIR/registration_backup_$TIMESTAMP" ]; then
            echo "Restauration des templates..."
            cp -r $BACKUP_DIR/registration_backup_$TIMESTAMP/* competitions/templates/registration/
        fi
        
        if [ -f "$BACKUP_DIR/auth_views_backup_$TIMESTAMP.py" ]; then
            echo "Restauration des vues..."
            cp $BACKUP_DIR/auth_views_backup_$TIMESTAMP.py competitions/views/auth.py
        fi
        
        if [ -d "$BACKUP_DIR/static_backup_$TIMESTAMP" ]; then
            echo "Restauration des fichiers statiques..."
            cp -r $BACKUP_DIR/static_backup_$TIMESTAMP/css/* competitions/static/css/
        fi
        
        # Recollector les statiques
        source venv/bin/activate
        python manage.py collectstatic --noinput
        
        # Redémarrer les services
        systemctl restart gunicorn nginx
        
        # Vérifier que l'authentification sociale est configurée
        cd $REMOTE_DIR
        source venv/bin/activate
        
        # Vérifier les variables d'environnement d'authentification sociale
        if [ -z "\$(grep GOOGLE_CLIENT_ID .env.production)" ]; then
            echo "⚠️  Variables d'authentification sociale non configurées"
            echo "Veuillez configurer les clés API dans .env.production"
        fi
        
        echo "Rollback terminé"
EOF
    
    error "Rollback effectué. Vérifiez le site manuellement."
}

# Script principal
main() {
    log "=== DÉBUT DU DÉPLOIEMENT DE L'AUTHENTIFICATION MODERNISÉE ==="
    log "Serveur: $PRODUCTION_SERVER"
    log "Timestamp: $TIMESTAMP"
    
    # Piège pour capturer les erreurs et effectuer un rollback
    trap 'error "Erreur détectée!"; rollback; exit 1' ERR
    
    # Étapes du déploiement
    check_prerequisites
    create_backup
    sync_files
    collect_static
    restart_services
    verify_deployment
    
    log "=== DÉPLOIEMENT TERMINÉ AVEC SUCCÈS ==="
    log "Les nouvelles fonctionnalités d'authentification sont maintenant en ligne"
    log "Backup sauvegardé dans: $BACKUP_DIR avec timestamp $TIMESTAMP"
    
    info "URLs à tester:"
    info "- https://$PRODUCTION_SERVER/login/ (nouveau design)"
    info "- https://$PRODUCTION_SERVER/signup/ (nouveau design)"
    info "- Authentification sociale (Google, Facebook, Apple)"
    info "- Accès via sous-domaines d'organisations"
}

# Demander confirmation avant de continuer
echo -e "${YELLOW}ATTENTION: Ce script va déployer les modifications d'authentification sur la production.${NC}"
echo -e "${YELLOW}Serveur cible: $PRODUCTION_USER@$PRODUCTION_SERVER${NC}"
echo ""
read -p "Voulez-vous continuer? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Déploiement annulé."
    exit 0
fi

# Exécuter le déploiement
main "$@"