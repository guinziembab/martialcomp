#!/bin/bash
# Script de synchronisation complète de l'application
# Sans toucher à la base de données

set -e

PROJECT_ROOT="/mnt/c/martial_hub_django/martialcomp"
PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="/tmp/production_backup_$(date +%Y%m%d_%H%M%S)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Synchronisation complète de l'application"
echo "Date: $(date)"
echo "=========================================="

# 1. Sauvegarder les fichiers de configuration en production
echo -e "\n${YELLOW}1. Sauvegarde des configurations de production...${NC}"
ssh "$PRODUCTION_SERVER" "mkdir -p $BACKUP_DIR/config && \
    cp -r $PRODUCTION_PATH/config/settings/production.py $BACKUP_DIR/config/ 2>/dev/null || true && \
    cp $PRODUCTION_PATH/.env $BACKUP_DIR/ 2>/dev/null || true && \
    cp $PRODUCTION_PATH/config/wsgi.py $BACKUP_DIR/config/ 2>/dev/null || true && \
    echo 'Configurations sauvegardées dans $BACKUP_DIR'"

# 2. Arrêter Gunicorn
echo -e "\n${YELLOW}2. Arrêt de Gunicorn...${NC}"
ssh "$PRODUCTION_SERVER" "pkill -f gunicorn || true"
sleep 2

# 3. Synchroniser l'application complète
echo -e "\n${YELLOW}3. Synchronisation complète de l'application...${NC}"
echo "Exclusions: base de données, media, logs, cache, venv"

rsync -avz --delete \
    --exclude='*.pyc' \
    --exclude='__pycache__/' \
    --exclude='.git/' \
    --exclude='.gitignore' \
    --exclude='venv/' \
    --exclude='env/' \
    --exclude='media/' \
    --exclude='staticfiles/' \
    --exclude='logs/' \
    --exclude='*.log' \
    --exclude='*.sqlite3' \
    --exclude='*.db' \
    --exclude='.env' \
    --exclude='*.backup*' \
    --exclude='*.sh' \
    --exclude='*.md' \
    --exclude='*.txt.py' \
    --exclude='*.tar.gz' \
    --exclude='fix_*' \
    --exclude='deploy_*' \
    --exclude='patch_*' \
    --exclude='test_*' \
    --exclude='*_backup_*' \
    --exclude='*_modified_*' \
    --exclude='*_production_*' \
    --exclude='*_corrupted*' \
    --exclude='fixtures/' \
    --exclude='migrations/*.pyc' \
    --exclude='AJOUT_*' \
    --exclude='AMELIORATION_*' \
    --exclude='AUDIT_*' \
    --exclude='BIG FIXING*' \
    --exclude='CORRECTIONS_*' \
    --exclude='DEBUG_*' \
    --exclude='DEMO_*' \
    --exclude='DEPLOIEMENT_*' \
    --exclude='ETAPE*' \
    --exclude='FONCTIONNALITES_*' \
    --exclude='INDEX_*' \
    --exclude='MIGRATIONS_*' \
    --exclude='NOUVEAU_*' \
    --exclude='PACKAGE_*' \
    --exclude='PHASE*' \
    --exclude='POINT_*' \
    --exclude='PRODUCTION_*' \
    --exclude='PROGRESSION_*' \
    --exclude='RAPPORT_*' \
    --exclude='RECAPITULATIF_*' \
    --exclude='REDIRECTION_*' \
    --exclude='RESOLUTION_*' \
    --exclude='RESTAURATION_*' \
    --exclude='STATUT_*' \
    --exclude='STRUCTURE_*' \
    --exclude='TEST_*' \
    --exclude='TODOLIST_*' \
    --exclude='UNIFORMISATION_*' \
    --exclude='production_update_*' \
    "$PROJECT_ROOT/" \
    "$PRODUCTION_SERVER:$PRODUCTION_PATH/"

echo -e "${GREEN}✓ Synchronisation terminée${NC}"

# 4. Restaurer les configurations de production
echo -e "\n${YELLOW}4. Restauration des configurations de production...${NC}"
ssh "$PRODUCTION_SERVER" "\
    cp $BACKUP_DIR/config/production.py $PRODUCTION_PATH/config/settings/production.py 2>/dev/null || true && \
    cp $BACKUP_DIR/.env $PRODUCTION_PATH/.env 2>/dev/null || true && \
    cp $BACKUP_DIR/config/wsgi.py $PRODUCTION_PATH/config/wsgi.py 2>/dev/null || true && \
    echo '✓ Configurations restaurées'"

# 5. Définir les permissions
echo -e "\n${YELLOW}5. Configuration des permissions...${NC}"
ssh "$PRODUCTION_SERVER" "\
    chown -R www-data:www-data $PRODUCTION_PATH && \
    find $PRODUCTION_PATH -type f -name '*.py' -exec chmod 644 {} \; && \
    find $PRODUCTION_PATH -type d -exec chmod 755 {} \;"

# 6. Collecter les fichiers statiques
echo -e "\n${YELLOW}6. Collecte des fichiers statiques...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && \
    /var/www/vhosts/martialcomp.com/venv/bin/python manage.py collectstatic --noinput"

# 7. Compiler les messages
echo -e "\n${YELLOW}7. Compilation des messages...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && \
    /var/www/vhosts/martialcomp.com/venv/bin/python manage.py compilemessages || echo 'Pas de messages à compiler'"

# 8. Redémarrer Gunicorn
echo -e "\n${YELLOW}8. Redémarrage de Gunicorn...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && \
    /var/www/vhosts/martialcomp.com/venv/bin/python -m gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8888 \
    --daemon \
    --pid /tmp/gunicorn.pid \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    --timeout 300 \
    config.wsgi:application"

sleep 3

# 9. Redémarrer nginx
echo -e "\n${YELLOW}9. Redémarrage de nginx...${NC}"
ssh "$PRODUCTION_SERVER" "sudo systemctl reload nginx"

# 10. Test final
echo -e "\n${YELLOW}10. Test du site...${NC}"
sleep 5

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/)
echo "Statut HTTP: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "301" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "${GREEN}✓ Site accessible!${NC}"
    echo -e "${GREEN}✓ Synchronisation complète réussie!${NC}"
else
    echo -e "${RED}✗ Site toujours en erreur (HTTP $HTTP_STATUS)${NC}"
    echo "Vérification des logs..."
    ssh "$PRODUCTION_SERVER" "tail -20 $PRODUCTION_PATH/logs/gunicorn_error.log | grep -E '(Error|Exception)' -A 3 || echo 'Pas d erreur dans les logs'"
fi

echo -e "\n${GREEN}=========================================="
echo "Synchronisation terminée!"
echo "==========================================${NC}"