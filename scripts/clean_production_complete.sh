#!/bin/bash

# Script de Nettoyage Complet de la Production
# MartialComp - Suppression des "Casseroles" Avant Sync

set -e

# Configuration
PROJECT_NAME="martialcomp"
PROD_USER="root"
PROD_HOST="martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com"
BACKUP_DIR="/root/martialcomp_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Fonction d'analyse de la structure actuelle
analyze_current_structure() {
    log "=== ANALYSE DE LA STRUCTURE ACTUELLE ==="
    
    log "Structure actuelle de la production:"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && find . -maxdepth 2 -type d | sort"
    
    log "Fichiers de configuration actuels:"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && ls -la *.py *.sh *.conf *.env 2>/dev/null || echo 'Aucun fichier de config trouvé'"
    
    log "Taille des dossiers:"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && du -sh * 2>/dev/null || echo 'Impossible de calculer la taille'"
}

# Fonction de création du backup de sauvegarde
create_safety_backup() {
    log "=== CRÉATION DU BACKUP DE SAUVEGARDE ==="
    
    # Création du backup complet
    ssh $PROD_USER@$PROD_HOST "mkdir -p $BACKUP_DIR/$TIMESTAMP"
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/$TIMESTAMP/production_complete_backup.tar.gz ."
    
    success "Backup de sauvegarde créé: $BACKUP_DIR/$TIMESTAMP/production_complete_backup.tar.gz"
}

# Fonction d'identification des éléments à conserver
identify_preserve_elements() {
    log "=== IDENTIFICATION DES ÉLÉMENTS À CONSERVER ==="
    
    # Création de la liste des éléments à conserver
    cat > /tmp/preserve_list.txt << 'EOF'
# ÉLÉMENTS À CONSERVER (Configurations Production)
config/production.py
config/local.py
production.env
.env
vhost.conf
passenger_wsgi.py
*.sh
*.sql
*.log
logs/
backups/
production_*/

# ÉLÉMENTS À CONSERVER (Données Importantes)
media/
uploads/
user_uploads/
documents/
certificates/
images/
videos/

# ÉLÉMENTS À CONSERVER (Base de Données)
*.sql
*.json
database_backup.*

# ÉLÉMENTS À CONSERVER (Logs et Monitoring)
logs/
*.log
nginx.conf
gunicorn.conf

# ÉLÉMENTS À CONSERVER (Sécurité)
.htaccess
.htpasswd
ssl/
certificates/

# ÉLÉMENTS À CONSERVER (Backups)
backups/
production_*/
martialcomp_backup*
EOF

    log "Liste des éléments à conserver créée:"
    cat /tmp/preserve_list.txt
    
    # Sauvegarde des éléments à conserver
    log "Sauvegarde des éléments à conserver..."
    ssh $PROD_USER@$PROD_HOST "mkdir -p $BACKUP_DIR/$TIMESTAMP/preserved_elements"
    
    # Sauvegarde des fichiers de configuration
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/$TIMESTAMP/preserved_elements/config_files.tar.gz \
        config/production.py config/local.py production.env .env vhost.conf passenger_wsgi.py *.sh *.sql 2>/dev/null || true"
    
    # Sauvegarde des dossiers importants
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -czf $BACKUP_DIR/$TIMESTAMP/preserved_elements/important_dirs.tar.gz \
        media/ uploads/ user_uploads/ documents/ certificates/ images/ videos/ logs/ backups/ 2>/dev/null || true"
    
    success "Éléments à conserver identifiés et sauvegardés"
}

# Fonction de nettoyage complet
clean_production_complete() {
    log "=== NETTOYAGE COMPLET DE LA PRODUCTION ==="
    
    # Confirmation de l'utilisateur
    echo
    warning "ATTENTION: Cette opération va supprimer TOUS les fichiers de la production"
    echo "Seuls les éléments sauvegardés seront conservés"
    echo "Backup de sécurité: $BACKUP_DIR/$TIMESTAMP/production_complete_backup.tar.gz"
    echo
    read -p "Êtes-vous ABSOLUMENT sûr de vouloir continuer? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Nettoyage annulé par l'utilisateur"
        return 1
    fi
    
    # Arrêt des services
    log "Arrêt des services..."
    ssh $PROD_USER@$PROD_HOST "systemctl stop nginx"
    ssh $PROD_USER@$PROD_HOST "systemctl stop gunicorn" || true
    
    # Suppression complète (sauf les éléments sauvegardés)
    log "Suppression complète des fichiers..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && rm -rf * .* 2>/dev/null || true"
    
    # Vérification de la suppression
    log "Vérification de la suppression..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && ls -la" || success "Répertoire vide"
    
    success "Nettoyage complet terminé"
}

# Fonction de restauration des éléments conservés
restore_preserved_elements() {
    log "=== RESTAURATION DES ÉLÉMENTS CONSERVÉS ==="
    
    # Restauration des fichiers de configuration
    log "Restauration des fichiers de configuration..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -xzf $BACKUP_DIR/$TIMESTAMP/preserved_elements/config_files.tar.gz 2>/dev/null || true"
    
    # Restauration des dossiers importants
    log "Restauration des dossiers importants..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && tar -xzf $BACKUP_DIR/$TIMESTAMP/preserved_elements/important_dirs.tar.gz 2>/dev/null || true"
    
    # Vérification de la restauration
    log "Vérification de la restauration..."
    ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && ls -la"
    
    success "Restauration des éléments conservés terminée"
}

# Fonction de liste des dossiers à conserver
list_preserve_directories() {
    log "=== LISTE DES DOSSIERS À CONSERVER ==="
    
    echo
    echo "📁 DOSSIERS DE CONFIGURATION (À CONSERVER):"
    echo "  - config/production.py (Configuration production)"
    echo "  - config/local.py (Configuration locale)"
    echo "  - production.env (Variables d'environnement)"
    echo "  - .env (Variables d'environnement)"
    echo "  - vhost.conf (Configuration Nginx)"
    echo "  - passenger_wsgi.py (Configuration Passenger)"
    echo "  - *.sh (Scripts de maintenance)"
    echo "  - *.sql (Scripts de base de données)"
    echo
    echo "📁 DOSSIERS DE DONNÉES (À CONSERVER):"
    echo "  - media/ (Fichiers uploadés)"
    echo "  - uploads/ (Fichiers uploadés)"
    echo "  - user_uploads/ (Uploads utilisateurs)"
    echo "  - documents/ (Documents)"
    echo "  - certificates/ (Certificats)"
    echo "  - images/ (Images)"
    echo "  - videos/ (Vidéos)"
    echo
    echo "📁 DOSSIERS DE LOGS (À CONSERVER):"
    echo "  - logs/ (Logs de l'application)"
    echo "  - *.log (Fichiers de logs)"
    echo
    echo "📁 DOSSIERS DE BACKUP (À CONSERVER):"
    echo "  - backups/ (Backups de l'application)"
    echo "  - production_*/ (Backups de production)"
    echo "  - martialcomp_backup* (Backups spécifiques)"
    echo
    echo "📁 DOSSIERS DE SÉCURITÉ (À CONSERVER):"
    echo "  - ssl/ (Certificats SSL)"
    echo "  - certificates/ (Certificats)"
    echo "  - .htaccess (Configuration Apache)"
    echo "  - .htpasswd (Mots de passe Apache)"
    echo
    echo "🗑️  DOSSIERS À SUPPRIMER:"
    echo "  - __pycache__/ (Cache Python)"
    echo "  - *.pyc (Fichiers compilés Python)"
    echo "  - .venv/ (Environnement virtuel)"
    echo "  - venv/ (Environnement virtuel)"
    echo "  - node_modules/ (Modules Node.js)"
    echo "  - .git/ (Repository Git)"
    echo "  - temp_venv/ (Environnement temporaire)"
    echo "  - staticfiles/ (Fichiers statiques - seront régénérés)"
    echo "  - locale/ (Traductions - seront resynchronisées)"
    echo "  - Tous les fichiers de développement"
    echo "  - Tous les scripts de debug"
    echo "  - Tous les fichiers temporaires"
}

# Fonction de nettoyage sélectif (alternative)
clean_production_selective() {
    log "=== NETTOYAGE SÉLECTIF DE LA PRODUCTION ==="
    
    # Liste des éléments à supprimer
    local elements_to_remove=(
        "__pycache__"
        "*.pyc"
        ".venv"
        "venv"
        "temp_venv"
        "node_modules"
        ".git"
        "staticfiles"
        "locale"
        "*.log"
        "logs"
        "*.sh"
        "*.sql"
        "*.py"
        "*.md"
        "*.txt"
        "*.json"
        "*.yaml"
        "*.yml"
        "test_*"
        "debug_*"
        "fix_*"
        "cleanup_*"
        "sync_*"
        "rollback_*"
        "diagnostic_*"
        "execute_*"
        "GUIDE_*"
        "SYNC_*"
        "RAPPORT_*"
        "CLEANUP_*"
        "CONFIGURATION_*"
        "DEPLOY_*"
        "QUICK_FIX_*"
        "*.bat"
        "*.md"
        "docs/"
        "scripts/"
        "deployment/"
        "archive/"
        "packages/"
        "Princing Model/"
    )
    
    log "Suppression sélective des éléments..."
    
    for element in "${elements_to_remove[@]}"; do
        log "Suppression de: $element"
        ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && find . -name '$element' -type f -delete 2>/dev/null || true"
        ssh $PROD_USER@$PROD_HOST "cd $PROD_PATH && find . -name '$element' -type d -exec rm -rf {} + 2>/dev/null || true"
    done
    
    success "Nettoyage sélectif terminé"
}

# Fonction principale
main() {
    case "${1:-help}" in
        "analyze")
            analyze_current_structure
            ;;
        "list")
            list_preserve_directories
            ;;
        "backup")
            create_safety_backup
            identify_preserve_elements
            ;;
        "clean-complete")
            create_safety_backup
            identify_preserve_elements
            clean_production_complete
            restore_preserved_elements
            ;;
        "clean-selective")
            create_safety_backup
            clean_production_selective
            ;;
        "restore")
            restore_preserved_elements
            ;;
        "help"|*)
            echo "Usage: $0 [OPTION]"
            echo
            echo "Options:"
            echo "  analyze         Analyser la structure actuelle"
            echo "  list            Lister les dossiers à conserver"
            echo "  backup          Créer un backup de sécurité"
            echo "  clean-complete  Nettoyage complet (supprime tout)"
            echo "  clean-selective Nettoyage sélectif (supprime sélectivement)"
            echo "  restore         Restaurer les éléments conservés"
            echo "  help            Afficher cette aide"
            echo
            echo "Exemples:"
            echo "  $0 analyze"
            echo "  $0 list"
            echo "  $0 backup"
            echo "  $0 clean-complete"
            echo "  $0 clean-selective"
            ;;
    esac
}

# Exécution du script principal
main "$@" 