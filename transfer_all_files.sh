#!/bin/bash
# Script pour transférer tous les fichiers en production

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

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
COPIED=0
FAILED=0
COUNTER=0

echo "Transfert de $TOTAL fichiers..."
echo ""

# Utiliser un fichier temporaire pour suivre la progression
PROGRESS_FILE="/tmp/transfer_progress_$$.txt"
echo "0" > "$PROGRESS_FILE"
echo "0" > "${PROGRESS_FILE}.failed"

while IFS= read -r file; do
    if [ -f "$file" ]; then
        ((COUNTER++))
        
        # Créer le répertoire si nécessaire
        ssh -q "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/$(dirname "$file")" 2>/dev/null || true
        
        # Transférer le fichier
        if scp -q "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" 2>/dev/null; then
            COPIED=$(($(cat "$PROGRESS_FILE") + 1))
            echo "$COPIED" > "$PROGRESS_FILE"
            
            if [ $((COPIED % 20)) -eq 0 ]; then
                echo "✓ $COPIED/$TOTAL fichiers transférés..."
            fi
        else
            FAILED=$(($(cat "${PROGRESS_FILE}.failed") + 1))
            echo "$FAILED" > "${PROGRESS_FILE}.failed"
            echo "✗ Échec: $file"
        fi
    fi
done < "$FILES_LIST"

COPIED=$(cat "$PROGRESS_FILE")
FAILED=$(cat "${PROGRESS_FILE}.failed" 2>/dev/null || echo "0")

rm -f "$PROGRESS_FILE" "${PROGRESS_FILE}.failed"

echo ""
echo "=========================================="
echo "Transfert terminé: $COPIED/$TOTAL fichiers"
if [ "$FAILED" -gt 0 ]; then
    echo "Échecs: $FAILED"
fi
echo "=========================================="
