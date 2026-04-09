#!/bin/bash
# Script optimisé pour compléter le transfert des fichiers

set -e

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$PROJECT_ROOT"

# Trouver la liste des fichiers
FILES_LIST=$(ls -t /tmp/files_essential_*.txt 2>/dev/null | head -1)

if [ -z "$FILES_LIST" ]; then
    echo "Génération de la liste des fichiers..."
    FILES_LIST="/tmp/files_essential_$$.txt"
    git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
        grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
        grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
        grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
        grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
        grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"
fi

TOTAL=$(wc -l < "$FILES_LIST")
echo -e "${GREEN}Transfert de $TOTAL fichiers...${NC}\n"

COPIED=0
FAILED=0
FAILED_FILES=()

while IFS= read -r file; do
    if [ -f "$file" ]; then
        # Vérifier si le fichier existe déjà en production
        if ssh -q "$PRODUCTION_SERVER" "test -f $PRODUCTION_PATH/$file" 2>/dev/null; then
            ((COPIED++))
        else
            # Créer le répertoire si nécessaire
            ssh -q "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/$(dirname "$file")" 2>/dev/null || true
            
            # Transférer le fichier
            if scp -q "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" 2>/dev/null; then
                ((COPIED++))
            else
                ((FAILED++))
                FAILED_FILES+=("$file")
            fi
        fi
        
        # Afficher la progression tous les 10 fichiers
        if [ $((COPIED % 10)) -eq 0 ] && [ $COPIED -gt 0 ]; then
            echo -e "${GREEN}✓${NC} $COPIED/$TOTAL fichiers transférés..."
        fi
    fi
done < "$FILES_LIST"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Transfert terminé!${NC}"
echo -e "${GREEN}========================================${NC}\n"
echo -e "Fichiers transférés: ${GREEN}$COPIED/$TOTAL${NC}"

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Fichiers en échec: $FAILED${NC}"
    echo -e "${YELLOW}Fichiers en échec:${NC}"
    for file in "${FAILED_FILES[@]}"; do
        echo -e "  - $file"
    done
fi
