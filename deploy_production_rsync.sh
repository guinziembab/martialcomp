#!/bin/bash
# Script de déploiement optimisé avec rsync
# Date: 2024-11-10

set -e

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$PROJECT_ROOT"

echo "=========================================="
echo "Déploiement en production avec rsync"
echo "Date: $(date)"
echo "=========================================="

# Étape 1: Identifier les fichiers à transférer
echo -e "\n${YELLOW}Étape 1: Identification des fichiers modifiés...${NC}"

# Créer une liste propre des fichiers Python, HTML, JS, CSS et JSON modifiés
git diff --name-only $(git merge-base HEAD origin/main) HEAD | \
    grep -E '\.(py|html|js|css|json)$' | \
    grep -v '\.html\.py$' | \
    grep -v -E '(\.backup_|\.modified_|\.production_|\.broken_|test_|fix_|deploy_|patch_|\.md$|\.txt\.py$|\.sh$|\.tar\.gz$|/fixtures/|__pycache__|\.corrupted$|\.pyc$)' | \
    grep -E '^apps/|^locale/' | \
    sort | uniq > /tmp/rsync_files_list.txt

TOTAL=$(wc -l < /tmp/rsync_files_list.txt)
echo -e "${GREEN}✓ $TOTAL fichiers identifiés${NC}"

# Étape 2: Créer les répertoires nécessaires sur le serveur
echo -e "\n${YELLOW}Étape 2: Création des répertoires...${NC}"
cat /tmp/rsync_files_list.txt | xargs -I {} dirname {} | sort | uniq | while read dir; do
    ssh "$PRODUCTION_SERVER" "mkdir -p $PRODUCTION_PATH/$dir" 2>/dev/null || true
done
echo -e "${GREEN}✓ Répertoires créés${NC}"

# Étape 3: Transférer avec rsync
echo -e "\n${YELLOW}Étape 3: Transfert des fichiers avec rsync...${NC}"
rsync -avz --files-from=/tmp/rsync_files_list.txt \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='*.backup_*' \
    --exclude='*.modified_*' \
    --exclude='*.production_*' \
    --exclude='fixtures/' \
    "$PROJECT_ROOT/" \
    "$PRODUCTION_SERVER:$PRODUCTION_PATH/"

echo -e "${GREEN}✓ Fichiers transférés${NC}"

# Étape 4: Appliquer les migrations
echo -e "\n${YELLOW}Étape 4: Vérification des migrations...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py showmigrations --plan | grep '\[ \]' | head -5" || true

echo -e "${YELLOW}Application des migrations...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py migrate --noinput" && \
    echo -e "${GREEN}✓ Migrations appliquées${NC}" || \
    echo -e "${YELLOW}⚠ Aucune migration à appliquer${NC}"

# Étape 5: Collectstatic
echo -e "\n${YELLOW}Étape 5: Collecte des fichiers statiques...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py collectstatic --noinput --clear" && \
    echo -e "${GREEN}✓ Fichiers statiques collectés${NC}" || \
    echo -e "${RED}✗ Erreur lors de collectstatic${NC}"

# Étape 6: Compilation des messages
echo -e "\n${YELLOW}Étape 6: Compilation des messages de traduction...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 manage.py compilemessages" && \
    echo -e "${GREEN}✓ Messages compilés${NC}" || \
    echo -e "${YELLOW}⚠ Pas de messages à compiler${NC}"

# Étape 7: Redémarrage des services
echo -e "\n${YELLOW}Étape 7: Redémarrage des services...${NC}"
ssh "$PRODUCTION_SERVER" "sudo systemctl restart httpd" && \
    echo -e "${GREEN}✓ Apache redémarré${NC}" || \
    echo -e "${RED}✗ Erreur lors du redémarrage d'Apache${NC}"

# Vérification finale
echo -e "\n${YELLOW}Vérification finale...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ || echo "000")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Site accessible (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}✗ Site inaccessible (HTTP $HTTP_STATUS)${NC}"
fi

echo -e "\n${GREEN}=========================================="
echo "Déploiement terminé!"
echo "==========================================${NC}"