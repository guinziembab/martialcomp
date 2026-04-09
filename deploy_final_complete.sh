#!/bin/bash
# Script de déploiement complet et final

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$PROJECT_ROOT"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement complet en production${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Étape 1: Générer la liste des fichiers
echo -e "${YELLOW}Étape 1: Génération de la liste des fichiers...${NC}"
FILES_LIST="/tmp/files_essential_deploy_$$.txt"
git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
    grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
    grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
    grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
    grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
    grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"

TOTAL=$(wc -l < "$FILES_LIST")
echo -e "${GREEN}✓ $TOTAL fichiers identifiés${NC}\n"

# Étape 2: Créer un backup
echo -e "${YELLOW}Étape 2: Création du backup...${NC}"
BACKUP_DIR="backup_production_$(date +%Y%m%d_%H%M%S)"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && mkdir -p ../$BACKUP_DIR" || true

# Étape 3: Transférer les fichiers
echo -e "${YELLOW}Étape 3: Transfert des fichiers...${NC}"

# Utiliser des fichiers temporaires pour suivre la progression
PROGRESS_FILE="/tmp/transfer_progress_$$.txt"
FAILED_FILE="/tmp/transfer_failed_$$.txt"
echo "0" > "$PROGRESS_FILE"
echo "0" > "$FAILED_FILE"

while IFS= read -r file || [ -n "$file" ]; do
    if [ -n "$file" ] && [ -f "$file" ]; then
        # Créer le répertoire
        ssh -q "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/$(dirname "$file")" 2>/dev/null || true
        
        # Sauvegarder si le fichier existe
        ssh -q "$PRODUCTION_SERVER" "if [ -f $PRODUCTION_PATH/$file ]; then mkdir -p $PRODUCTION_PATH/../$BACKUP_DIR/$(dirname "$file") && cp $PRODUCTION_PATH/$file $PRODUCTION_PATH/../$BACKUP_DIR/$file; fi" 2>/dev/null || true
        
        # Transférer
        if scp -q "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" 2>/dev/null; then
            COPIED=$(($(cat "$PROGRESS_FILE") + 1))
            echo "$COPIED" > "$PROGRESS_FILE"
            if [ $((COPIED % 20)) -eq 0 ]; then
                echo -e "  ${GREEN}✓${NC} $COPIED/$TOTAL fichiers transférés..."
            fi
        else
            FAILED=$(($(cat "$FAILED_FILE") + 1))
            echo "$FAILED" > "$FAILED_FILE"
            echo -e "  ${RED}✗${NC} Échec: $file"
        fi
    fi
done < "$FILES_LIST"

COPIED=$(cat "$PROGRESS_FILE")
FAILED=$(cat "$FAILED_FILE")

rm -f "$PROGRESS_FILE" "$FAILED_FILE"

echo -e "\n${GREEN}✓ Transfert terminé: $COPIED/$TOTAL fichiers${NC}"
if [ "$FAILED" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Échecs: $FAILED${NC}"
fi

# Étape 4: Migrations
echo -e "\n${YELLOW}Étape 4: Vérification des migrations...${NC}"
MIGRATIONS=$(ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py showmigrations --plan 2>/dev/null | grep '\[ \]' | wc -l" || echo "0")
if [ "$MIGRATIONS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ $MIGRATIONS migration(s) en attente${NC}"
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py migrate --noinput" && \
        echo -e "${GREEN}✓ Migrations appliquées${NC}" || \
        echo -e "${RED}✗ Erreur lors des migrations${NC}"
else
    echo -e "${GREEN}✓ Aucune migration en attente${NC}"
fi

# Étape 5: Collectstatic
echo -e "\n${YELLOW}Étape 5: Collecte des fichiers statiques...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py collectstatic --noinput" && \
    echo -e "${GREEN}✓ Fichiers statiques collectés${NC}" || \
    echo -e "${YELLOW}⚠ Erreur lors de collectstatic${NC}"

# Étape 6: Redémarrage
echo -e "\n${YELLOW}Étape 6: Redémarrage des services...${NC}"
if ssh "$PRODUCTION_SERVER" "systemctl restart gunicorn" 2>/dev/null; then
    echo -e "${GREEN}✓ Gunicorn redémarré${NC}"
elif ssh "$PRODUCTION_SERVER" "touch $PRODUCTION_PATH/wsgi.py" 2>/dev/null; then
    echo -e "${GREEN}✓ Application rechargée${NC}"
else
    echo -e "${YELLOW}⚠ Redémarrage manuel requis${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement terminé!${NC}"
echo -e "${GREEN}========================================${NC}\n"

rm -f "$FILES_LIST"
