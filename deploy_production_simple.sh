#!/bin/bash
# Script de déploiement simple et direct sur la production
# Ce script crée un backup, transfère et déploie les fichiers

set -e

# Configuration
PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

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
FILES_LIST="/tmp/files_essential_$$.txt"
git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
    grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
    grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
    grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
    grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
    grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"

FILE_COUNT=$(wc -l < "$FILES_LIST")
echo -e "${GREEN}✓ ${FILE_COUNT} fichiers identifiés${NC}\n"

# Étape 2: Créer un backup sur le serveur de production
echo -e "${YELLOW}Étape 2: Création du backup sur le serveur de production...${NC}"

# Transférer la liste des fichiers d'abord
scp "$FILES_LIST" "$PRODUCTION_SERVER:/tmp/files_to_backup.txt" > /dev/null 2>&1

# Créer le backup sur le serveur
ssh "$PRODUCTION_SERVER" bash << 'BACKUP_SCRIPT'
set -e
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="backup_production_$(date +%Y%m%d_%H%M%S)"

if [ ! -d "$PRODUCTION_PATH" ]; then
    echo "Erreur: Répertoire de production non trouvé: $PRODUCTION_PATH"
    exit 1
fi

cd "$PRODUCTION_PATH"
mkdir -p "../$BACKUP_DIR"

# Sauvegarder tous les fichiers qui seront remplacés
if [ -f /tmp/files_to_backup.txt ]; then
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            dir=$(dirname "../$BACKUP_DIR/$file")
            mkdir -p "$dir"
            cp "$file" "../$BACKUP_DIR/$file"
            echo "  ✓ Sauvegardé: $file"
        fi
    done < /tmp/files_to_backup.txt
fi

echo "Backup créé dans: ../$BACKUP_DIR"
BACKUP_SCRIPT

echo -e "${GREEN}✓ Backup créé${NC}\n"

# Étape 3: Transférer et déployer les fichiers
echo -e "${YELLOW}Étape 3: Transfert et déploiement des fichiers...${NC}"

COPIED=0
SKIPPED=0

while IFS= read -r file; do
    if [ -f "$file" ]; then
        # Transférer le fichier directement vers sa destination
        if scp "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" > /dev/null 2>&1; then
            ((COPIED++))
            if [ $((COPIED % 10)) -eq 0 ]; then
                echo -e "  ${GREEN}✓${NC} $COPIED fichiers transférés..."
            fi
        else
            ((SKIPPED++))
            echo -e "  ${YELLOW}⚠${NC} Échec: $file"
        fi
    else
        ((SKIPPED++))
    fi
done < "$FILES_LIST"

echo -e "\n${GREEN}Fichiers déployés: $COPIED${NC}"
if [ $SKIPPED -gt 0 ]; then
    echo -e "${YELLOW}Fichiers ignorés: $SKIPPED${NC}"
fi

# Nettoyer le fichier temporaire
rm -f "$FILES_LIST"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement terminé!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Étapes post-déploiement:${NC}"
echo -e "1. Vérifier les permissions des fichiers"
echo -e "2. Exécuter les migrations: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py migrate'"
echo -e "3. Collecter les fichiers statiques: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py collectstatic --noinput'"
echo -e "4. Redémarrer l'application"
echo -e "5. Vérifier les logs\n"
