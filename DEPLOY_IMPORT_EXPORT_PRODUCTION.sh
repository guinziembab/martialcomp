#!/bin/bash
# Script de déploiement pour la fonctionnalité d'import/export de pratiquants
# Date: $(date +%Y-%m-%d)
# Description: Déploiement de l'import Excel avec gestion CSRF et dates améliorées

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "Déploiement Import/Export - Production"
echo "=========================================="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SSH_TARGET="$REMOTE_USER@$REMOTE_HOST"

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Liste des fichiers à déployer
FILES=(
    "apps/competitions/views/club/import_export.py"
    "apps/competitions/templates/competitions/club/import_export.html"
    "config/settings/production.py"
)

echo "Fichiers à déployer:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Vérifier que tous les fichiers existent localement
info "Vérification des fichiers locaux..."
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        error "Le fichier $file n'existe pas localement"
        exit 1
    fi
    info "  ✓ $file"
done
echo ""

# Vérifier les modifications importantes
info "Vérification des modifications importantes..."

# Vérifier import_export.py
if grep -q "def import_practitioners_from_excel" "apps/competitions/views/club/import_export.py"; then
    info "  ✓ Fonction import_practitioners_from_excel trouvée"
else
    error "  ✗ Fonction import_practitioners_from_excel non trouvée"
    exit 1
fi

if grep -q "date_formats = \[" "apps/competitions/views/club/import_export.py"; then
    info "  ✓ Gestion des dates améliorée trouvée"
else
    error "  ✗ Gestion des dates améliorée non trouvée"
    exit 1
fi

# Vérifier production.py
if grep -q "CSRF_TRUSTED_ORIGINS" "config/settings/production.py"; then
    info "  ✓ Configuration CSRF trouvée"
else
    error "  ✗ Configuration CSRF non trouvée"
    exit 1
fi

# Vérifier le template
if grep -q "id=\"import-form\"" "apps/competitions/templates/competitions/club/import_export.html"; then
    info "  ✓ Template amélioré trouvé"
else
    error "  ✗ Template amélioré non trouvé"
    exit 1
fi

echo ""
info "Toutes les vérifications sont OK. Déploiement vers la production..."
echo ""

# Créer une sauvegarde sur le serveur distant
info "Création d'une sauvegarde sur le serveur..."
ssh $SSH_TARGET "mkdir -p $REMOTE_PATH/backups/$(date +%Y%m%d_%H%M%S)_import_export" || {
    error "Impossible de créer le dossier de sauvegarde"
    exit 1
}

BACKUP_DIR=$(ssh $SSH_TARGET "echo $REMOTE_PATH/backups/$(date +%Y%m%d_%H%M%S)_import_export")

for file in "${FILES[@]}"; do
    REMOTE_FILE="$REMOTE_PATH/$file"
    BACKUP_FILE="$BACKUP_DIR/$(basename $file)"
    
    # Sauvegarder le fichier existant
    ssh $SSH_TARGET "if [ -f '$REMOTE_FILE' ]; then cp '$REMOTE_FILE' '$BACKUP_FILE'; fi" || {
        warning "Impossible de sauvegarder $file (fichier peut-être nouveau)"
    }
done

info "Sauvegarde créée dans: $BACKUP_DIR"
echo ""

# Copier les fichiers vers la production
info "Copie des fichiers vers la production..."
for file in "${FILES[@]}"; do
    REMOTE_FILE="$REMOTE_PATH/$file"
    REMOTE_DIR=$(dirname "$REMOTE_FILE")
    
    # Créer le répertoire si nécessaire
    ssh $SSH_TARGET "mkdir -p '$REMOTE_DIR'" || {
        error "Impossible de créer le répertoire $REMOTE_DIR"
        exit 1
    }
    
    # Copier le fichier
    info "  Copie de $file..."
    scp "$file" "$SSH_TARGET:$REMOTE_FILE" || {
        error "Impossible de copier $file"
        exit 1
    }
done

echo ""
info "Tous les fichiers ont été copiés avec succès!"
echo ""

# Redémarrer le serveur Django
warning "Redémarrage du serveur Django nécessaire..."
echo ""
echo "Options de redémarrage:"
echo "  1. Redémarrer Gunicorn (recommandé)"
echo "  2. Redémarrer via systemd"
echo "  3. Toucher le fichier WSGI pour rechargement automatique"
echo "  4. Passer cette étape (redémarrer manuellement)"
echo ""
read -p "Choisissez une option (1-4): " restart_option

case $restart_option in
    1)
        info "Redémarrage de Gunicorn..."
        ssh $SSH_TARGET "sudo systemctl restart gunicorn" || {
            warning "Impossible de redémarrer Gunicorn via systemctl"
            warning "Essayez manuellement: sudo systemctl restart gunicorn"
        }
        ;;
    2)
        info "Redémarrage via systemd..."
        ssh $SSH_TARGET "sudo systemctl restart martialcomp" || {
            warning "Service 'martialcomp' non trouvé"
            warning "Vérifiez le nom du service avec: sudo systemctl list-units | grep martial"
        }
        ;;
    3)
        info "Toucher le fichier WSGI pour rechargement..."
        ssh $SSH_TARGET "touch $REMOTE_PATH/config/wsgi.py" || {
            warning "Impossible de toucher wsgi.py"
        }
        ;;
    4)
        warning "Redémarrage ignoré. N'oubliez pas de redémarrer manuellement!"
        ;;
    *)
        warning "Option invalide. Redémarrage ignoré."
        ;;
esac

echo ""
echo "=========================================="
info "Déploiement terminé avec succès!"
echo "=========================================="
echo ""
echo "Résumé:"
echo "  - Fichiers déployés: ${#FILES[@]}"
echo "  - Sauvegarde créée dans: $BACKUP_DIR"
echo ""
echo "Prochaines étapes:"
echo "  1. Tester l'import sur: https://martialcomp.com/fr/competitions/club/import-export/"
echo "  2. Vérifier les logs en cas d'erreur:"
echo "     ssh $SSH_TARGET 'tail -f /var/log/django/martialcomp.log'"
echo "  3. Vérifier que le serveur fonctionne correctement"
echo ""
echo "En cas de problème, restaurer depuis la sauvegarde:"
echo "  ssh $SSH_TARGET 'cp $BACKUP_DIR/* $REMOTE_PATH/apps/competitions/views/club/'"
echo ""
