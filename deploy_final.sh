#!/bin/bash
# Script de déploiement final - Transfert et déploiement des fichiers

set -e

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$PROJECT_ROOT"

# Trouver le dernier fichier de liste
FILES_LIST=$(ls -t /tmp/files_essential_*.txt 2>/dev/null | head -1)

if [ -z "$FILES_LIST" ]; then
    echo "Création de la liste des fichiers..."
    FILES_LIST="/tmp/files_essential_$$.txt"
    git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
        grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
        grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
        grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
        grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
        grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"
fi

echo -e "${GREEN}Transfert et déploiement des fichiers...${NC}\n"

COPIED=0
SKIPPED=0
TOTAL=$(wc -l < "$FILES_LIST")

while IFS= read -r file; do
    if [ -f "$file" ]; then
        # Créer le répertoire de destination si nécessaire
        ssh "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/$(dirname $file)" > /dev/null 2>&1
        
        # Transférer le fichier
        if scp "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" > /dev/null 2>&1; then
            ((COPIED++))
            if [ $((COPIED % 20)) -eq 0 ]; then
                echo -e "${GREEN}✓${NC} $COPIED/$TOTAL fichiers transférés..."
            fi
        else
            ((SKIPPED++))
            echo -e "${YELLOW}⚠${NC} Échec: $file"
        fi
    else
        ((SKIPPED++))
    fi
done < "$FILES_LIST"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement terminé!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Fichiers déployés: ${GREEN}$COPIED${NC}"
if [ $SKIPPED -gt 0 ]; then
    echo -e "Fichiers ignorés: ${YELLOW}$SKIPPED${NC}"
fi
echo -e "\n${YELLOW}Étapes post-déploiement:${NC}"
echo -e "1. Exécuter les migrations: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py migrate'"
echo -e "2. Collecter les fichiers statiques: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py collectstatic --noinput'"
echo -e "3. Redémarrer l'application"
echo -e "4. Vérifier les logs\n"
