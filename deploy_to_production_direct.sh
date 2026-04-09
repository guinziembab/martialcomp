#!/bin/bash
# Script de déploiement direct sur la production
# Ce script crée le package, le transfère et le déploie sur le serveur de production

set -e

# Configuration
PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/martialcomp"  # À adapter selon votre configuration
FILES_LIST="/tmp/files_essential.txt"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement Production - Novembre 2024${NC}"
echo -e "${GREEN}========================================${NC}\n"

cd "$PROJECT_ROOT"

# Étape 1: Créer la liste des fichiers essentiels
echo -e "${YELLOW}Étape 1: Génération de la liste des fichiers...${NC}"
git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
    grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
    grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
    grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
    grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
    grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"

FILE_COUNT=$(wc -l < "$FILES_LIST")
echo -e "${GREEN}✓ ${FILE_COUNT} fichiers identifiés${NC}\n"

# Étape 2: Se connecter au serveur de production et créer un backup
echo -e "${YELLOW}Étape 2: Connexion au serveur de production et création du backup...${NC}"

# Créer un script de backup sur le serveur distant
ssh "$PRODUCTION_SERVER" << 'BACKUP_SCRIPT'
set -e
PRODUCTION_PATH="/var/www/martialcomp"  # À adapter
BACKUP_DIR="backup_production_$(date +%Y%m%d_%H%M%S)"

if [ ! -d "$PRODUCTION_PATH" ]; then
    echo "Erreur: Répertoire de production non trouvé: $PRODUCTION_PATH"
    exit 1
fi

cd "$PRODUCTION_PATH"

# Créer le répertoire de backup
mkdir -p "../$BACKUP_DIR"

# Liste des fichiers à sauvegarder (équivalents à ceux qui seront déployés)
FILES_TO_BACKUP=(
    "apps/competitions/forms/combat_forms.py"
    "apps/competitions/forms/practitioners.py"
    "apps/competitions/forms/standalone_scoring.py"
    "apps/competitions/models/combat.py"
    "apps/competitions/templatetags/custom_filters.py"
    "apps/competitions/urls/__init__.py"
    "apps/competitions/urls/club.py"
    "apps/competitions/urls/combat.py"
    "apps/competitions/urls/competitions.py"
    "apps/competitions/urls/dashboard.py"
    "apps/competitions/urls/notifications.py"
    "apps/competitions/views/club/competitions.py"
    "apps/competitions/views/club/import_export.py"
    "apps/competitions/views/club/practitioners.py"
    "apps/competitions/views/club/registrations.py"
    "apps/competitions/views/combat.py"
    "apps/competitions/views/combat_taekwondo.py"
    "apps/competitions/views/competition_management_pro.py"
    "apps/competitions/views/competitions.py"
    "apps/competitions/views/dashboard/base.py"
    "apps/competitions/views/dashboard/club.py"
    "apps/competitions/views/dashboard/participant.py"
    "apps/competitions/views/dashboard/referee.py"
    "apps/competitions/views/management/dashboard.py"
    "apps/competitions/views/management/judges.py"
    "apps/competitions/views/management/participants.py"
    "apps/competitions/views/management/results.py"
    "apps/competitions/views/management/schedule.py"
    "apps/competitions/views/management/scoring.py"
    "apps/competitions/views/notifications.py"
    "apps/competitions/views/standalone_scoring.py"
    "apps/competitions/utils/decorators.py"
    "apps/competitions/utils/permission_helpers.py"
)

echo "Création du backup dans ../$BACKUP_DIR..."

# Sauvegarder tous les fichiers qui existent
for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -f "$file" ]; then
        dir=$(dirname "../$BACKUP_DIR/$file")
        mkdir -p "$dir"
        cp "$file" "../$BACKUP_DIR/$file"
        echo "  ✓ Sauvegardé: $file"
    fi
done

# Sauvegarder tous les fichiers de la liste si elle existe
if [ -f "/tmp/files_essential.txt" ]; then
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            dir=$(dirname "../$BACKUP_DIR/$file")
            mkdir -p "$dir"
            cp "$file" "../$BACKUP_DIR/$file" 2>/dev/null || true
        fi
    done < /tmp/files_essential.txt
fi

echo "Backup créé dans: ../$BACKUP_DIR"
echo "BACKUP_DIR=$BACKUP_DIR"
BACKUP_SCRIPT

BACKUP_DIR=$(ssh "$PRODUCTION_SERVER" 'cd /var/www/martialcomp && BACKUP_DIR="backup_production_$(date +%Y%m%d_%H%M%S)" && echo "$BACKUP_DIR"')

echo -e "${GREEN}✓ Backup créé sur le serveur${NC}\n"

# Étape 3: Transférer les fichiers
echo -e "${YELLOW}Étape 3: Transfert des fichiers vers la production...${NC}"

# Créer un répertoire temporaire sur le serveur
ssh "$PRODUCTION_SERVER" "mkdir -p /tmp/production_update"

# Transférer les fichiers un par un
COPIED=0
SKIPPED=0

while IFS= read -r file; do
    if [ -f "$file" ]; then
        # Créer le répertoire de destination sur le serveur
        ssh "$PRODUCTION_SERVER" "mkdir -p /tmp/production_update/$(dirname $file)"
        
        # Transférer le fichier
        scp "$file" "$PRODUCTION_SERVER:/tmp/production_update/$file" > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            ((COPIED++))
            echo -e "  ${GREEN}✓${NC} $file"
        else
            ((SKIPPED++))
            echo -e "  ${YELLOW}⚠${NC} Échec: $file"
        fi
    else
        ((SKIPPED++))
        echo -e "  ${YELLOW}⚠${NC} Non trouvé: $file"
    fi
done < "$FILES_LIST"

echo -e "\n${GREEN}Fichiers transférés: $COPIED${NC}"
echo -e "${YELLOW}Fichiers ignorés: $SKIPPED${NC}\n"

# Étape 4: Déployer les fichiers sur le serveur
echo -e "${YELLOW}Étape 4: Déploiement des fichiers sur la production...${NC}"

ssh "$PRODUCTION_SERVER" << 'DEPLOY_SCRIPT'
set -e
PRODUCTION_PATH="/var/www/martialcomp"
UPDATE_DIR="/tmp/production_update"

if [ ! -d "$UPDATE_DIR" ]; then
    echo "Erreur: Répertoire de mise à jour non trouvé: $UPDATE_DIR"
    exit 1
fi

cd "$PRODUCTION_PATH"

# Copier les fichiers du répertoire de mise à jour vers la production
if [ -f "$UPDATE_DIR/apps/competitions/forms/combat_forms.py" ]; then
    mkdir -p apps/competitions/forms
    cp "$UPDATE_DIR/apps/competitions/forms/"*.py apps/competitions/forms/ 2>/dev/null || true
    echo "✓ Forms déployés"
fi

if [ -f "$UPDATE_DIR/apps/competitions/models/combat.py" ]; then
    mkdir -p apps/competitions/models
    cp "$UPDATE_DIR/apps/competitions/models/"*.py apps/competitions/models/ 2>/dev/null || true
    echo "✓ Models déployés"
fi

if [ -f "$UPDATE_DIR/apps/competitions/views/combat.py" ]; then
    mkdir -p apps/competitions/views
    cp -r "$UPDATE_DIR/apps/competitions/views/"* apps/competitions/views/ 2>/dev/null || true
    echo "✓ Views déployées"
fi

if [ -f "$UPDATE_DIR/apps/competitions/urls/__init__.py" ]; then
    mkdir -p apps/competitions/urls
    cp "$UPDATE_DIR/apps/competitions/urls/"*.py apps/competitions/urls/ 2>/dev/null || true
    echo "✓ URLs déployées"
fi

if [ -d "$UPDATE_DIR/apps/competitions/templates" ]; then
    mkdir -p apps/competitions/templates
    cp -r "$UPDATE_DIR/apps/competitions/templates/"* apps/competitions/templates/ 2>/dev/null || true
    echo "✓ Templates déployés"
fi

if [ -d "$UPDATE_DIR/apps/competitions/utils" ]; then
    mkdir -p apps/competitions/utils
    cp "$UPDATE_DIR/apps/competitions/utils/"*.py apps/competitions/utils/ 2>/dev/null || true
    echo "✓ Utils déployés"
fi

if [ -d "$UPDATE_DIR/apps/competitions/templatetags" ]; then
    mkdir -p apps/competitions/templatetags
    cp "$UPDATE_DIR/apps/competitions/templatetags/"*.py apps/competitions/templatetags/ 2>/dev/null || true
    echo "✓ Templatetags déployés"
fi

# Copier tous les fichiers récursivement
if [ -d "$UPDATE_DIR/apps" ]; then
    cp -r "$UPDATE_DIR/apps/"* "$PRODUCTION_PATH/apps/" 2>/dev/null || true
    echo "✓ Tous les fichiers déployés"
fi

echo "Déploiement terminé"
DEPLOY_SCRIPT

echo -e "${GREEN}✓ Déploiement terminé${NC}\n"

# Étape 5: Instructions post-déploiement
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Étapes post-déploiement:${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "1. Vérifier les permissions des fichiers"
echo -e "2. Exécuter les migrations si nécessaire:"
echo -e "   ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py migrate'"
echo -e "3. Collecter les fichiers statiques:"
echo -e "   ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py collectstatic --noinput'"
echo -e "4. Redémarrer l'application"
echo -e "5. Vérifier les logs pour détecter d'éventuelles erreurs"
echo -e "\n${GREEN}Déploiement terminé!${NC}"
