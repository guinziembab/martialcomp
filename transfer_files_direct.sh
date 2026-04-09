#!/bin/bash
# Script simple pour transférer tous les fichiers directement

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

cd "$PROJECT_ROOT"

# Générer la liste des fichiers
FILES_LIST="/tmp/files_essential_direct_$$.txt"
git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
    grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
    grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
    grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
    grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
    grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"

TOTAL=$(wc -l < "$FILES_LIST")
echo "Transfert de $TOTAL fichiers..."

COPIED=0
FAILED=0

# Lire le fichier ligne par ligne
exec 3< "$FILES_LIST"
while IFS= read -r file <&3; do
    if [ -n "$file" ] && [ -f "$file" ]; then
        # Créer le répertoire
        ssh -q "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/$(dirname "$file")" 2>/dev/null || true
        
        # Transférer
        if scp -q "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" 2>/dev/null; then
            COPIED=$((COPIED + 1))
            if [ $((COPIED % 20)) -eq 0 ]; then
                echo "✓ $COPIED/$TOTAL fichiers transférés..."
            fi
        else
            FAILED=$((FAILED + 1))
            echo "✗ Échec: $file"
        fi
    fi
done
exec 3<&-

echo ""
echo "=========================================="
echo "Transfert terminé: $COPIED/$TOTAL fichiers"
if [ $FAILED -gt 0 ]; then
    echo "Échecs: $FAILED"
fi
echo "=========================================="

rm -f "$FILES_LIST"
