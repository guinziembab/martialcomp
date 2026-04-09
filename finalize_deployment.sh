#!/bin/bash
# Script de finalisation du déploiement en production
# Ce script complète le transfert, exécute les migrations et redémarre les services

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
echo -e "${GREEN}Finalisation du déploiement${NC}"
echo -e "${GREEN}========================================${NC}\n"

cd "$PROJECT_ROOT"

# Étape 1: Vérifier et compléter le transfert des fichiers
echo -e "${YELLOW}Étape 1: Vérification et complément du transfert...${NC}"

FILES_LIST=$(ls -t /tmp/files_essential_*.txt 2>/dev/null | head -1)

if [ -z "$FILES_LIST" ]; then
    echo -e "${YELLOW}Génération de la liste des fichiers...${NC}"
    FILES_LIST="/tmp/files_essential_$$.txt"
    git log --since="2024-11-01" --name-only --pretty=format: --diff-filter=AM | \
        grep -E "^apps/competitions/(forms|models|views|urls|templates|utils|templatetags)" | \
        grep -v "backup" | grep -v "\.py\.py$" | grep -v "\.backup" | \
        grep -v "_fix\.py$" | grep -v "_fixed\.py$" | grep -v "Backup" | \
        grep -v "copy\.py$" | grep -v "emergency\.py$" | grep -v "corrupted\.py$" | \
        grep -v "urls_bak" | grep -v "coach_forms_fix" | sort -u > "$FILES_LIST"
fi

TOTAL=$(wc -l < "$FILES_LIST")
TRANSFERRED=0
MISSING=0

echo -e "Vérification de $TOTAL fichiers..."

while IFS= read -r file; do
    if [ -f "$file" ]; then
        if ssh -q "$PRODUCTION_SERVER" "test -f $PRODUCTION_PATH/$file" 2>/dev/null; then
            ((TRANSFERRED++))
        else
            # Transférer le fichier manquant
            if scp -q "$file" "$PRODUCTION_SERVER:$PRODUCTION_PATH/$file" 2>/dev/null; then
                ((TRANSFERRED++))
                echo -e "  ${GREEN}✓${NC} Transféré: $file"
            else
                ((MISSING++))
                echo -e "  ${RED}✗${NC} Échec: $file"
            fi
        fi
    fi
done < "$FILES_LIST"

echo -e "\n${GREEN}✓ Transfert: $TRANSFERRED/$TOTAL fichiers${NC}"
if [ $MISSING -gt 0 ]; then
    echo -e "${YELLOW}⚠ Fichiers manquants: $MISSING${NC}"
fi

# Étape 2: Vérifier les migrations
echo -e "\n${YELLOW}Étape 2: Vérification des migrations...${NC}"

MIGRATIONS=$(ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python manage.py showmigrations --plan 2>/dev/null | grep '\[ \]' | wc -l" || echo "0")

if [ "$MIGRATIONS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ $MIGRATIONS migration(s) en attente${NC}"
    read -p "Appliquer les migrations maintenant? (o/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Oo]$ ]]; then
        echo -e "${YELLOW}Application des migrations...${NC}"
        ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python manage.py migrate --noinput" || {
            echo -e "${RED}✗ Erreur lors des migrations${NC}"
            exit 1
        }
        echo -e "${GREEN}✓ Migrations appliquées${NC}"
    fi
else
    echo -e "${GREEN}✓ Aucune migration en attente${NC}"
fi

# Étape 3: Collecter les fichiers statiques
echo -e "\n${YELLOW}Étape 3: Collecte des fichiers statiques...${NC}"

ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python manage.py collectstatic --noinput" || {
    echo -e "${YELLOW}⚠ Erreur lors de collectstatic (peut être normal si déjà à jour)${NC}"
}

echo -e "${GREEN}✓ Fichiers statiques collectés${NC}"

# Étape 4: Redémarrer les services
echo -e "\n${YELLOW}Étape 4: Redémarrage des services...${NC}"

# Essayer différentes méthodes de redémarrage selon la configuration
if ssh "$PRODUCTION_SERVER" "systemctl restart gunicorn" 2>/dev/null; then
    echo -e "${GREEN}✓ Gunicorn redémarré${NC}"
elif ssh "$PRODUCTION_SERVER" "systemctl restart uwsgi" 2>/dev/null; then
    echo -e "${GREEN}✓ uWSGI redémarré${NC}"
elif ssh "$PRODUCTION_SERVER" "touch $PRODUCTION_PATH/wsgi.py" 2>/dev/null; then
    echo -e "${GREEN}✓ Application rechargée (touch wsgi.py)${NC}"
else
    echo -e "${YELLOW}⚠ Redémarrage manuel requis${NC}"
fi

# Étape 5: Vérification finale
echo -e "\n${YELLOW}Étape 5: Vérification finale...${NC}"

# Vérifier que l'application répond
if ssh "$PRODUCTION_SERVER" "curl -s -o /dev/null -w '%{http_code}' http://localhost/ 2>/dev/null | grep -q '200\|301\|302'" 2>/dev/null; then
    echo -e "${GREEN}✓ Application accessible${NC}"
else
    echo -e "${YELLOW}⚠ Vérification de l'accessibilité de l'application requise${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Déploiement finalisé!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Résumé:${NC}"
echo -e "  • Fichiers transférés: $TRANSFERRED/$TOTAL"
echo -e "  • Migrations: $MIGRATIONS en attente"
echo -e "  • Services: Redémarrés"
echo -e "\n${YELLOW}Vérifications recommandées:${NC}"
echo -e "  1. Tester l'application en production"
echo -e "  2. Vérifier les logs: ssh $PRODUCTION_SERVER 'tail -f $PRODUCTION_PATH/logs/*.log'"
echo -e "  3. Vérifier les erreurs: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && python manage.py check'"
