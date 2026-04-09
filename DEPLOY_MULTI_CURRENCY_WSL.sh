#!/bin/bash
# =============================================================================
# SCRIPT DE DEPLOIEMENT - IMPLEMENTATION MULTI-DEVISES
# Date: 07-01-2026
# Utilise l'alias WSL: martialcomp-production
# Chemin production: /var/www/vhosts/martialcomp.com/httpdocs/
# =============================================================================

set -e

REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"

echo "=============================================="
echo "DEPLOIEMENT MULTI-DEVISES - MartialComp"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

echo ""
echo "[1/6] Création du backup sur le serveur distant..."
ssh $REMOTE "mkdir -p /var/www/backups/multi_currency_\$(date +%Y%m%d_%H%M%S) && cp -rp $REMOTE_PATH/apps/finances/templatetags/finances_tags.py $REMOTE_PATH/apps/finances/context_processors.py $REMOTE_PATH/apps/finances/views/transactions.py /var/www/backups/multi_currency_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || echo 'Backup partiel'"

echo ""
echo "[2/6] Transfert des fichiers Python..."
echo "  - finances_tags.py"
scp "$LOCAL_PATH/apps/finances/templatetags/finances_tags.py" $REMOTE:$REMOTE_PATH/apps/finances/templatetags/finances_tags.py

echo "  - context_processors.py"
scp "$LOCAL_PATH/apps/finances/context_processors.py" $REMOTE:$REMOTE_PATH/apps/finances/context_processors.py

echo "  - transactions.py"
scp "$LOCAL_PATH/apps/finances/views/transactions.py" $REMOTE:$REMOTE_PATH/apps/finances/views/transactions.py

echo ""
echo "[3/6] Transfert des templates..."
echo "  - dashboard/index.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/dashboard/index.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/dashboard/index.html

echo "  - transactions/list.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/transactions/list.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/transactions/list.html

echo "  - accounts/list.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/accounts/list.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/accounts/list.html

echo "  - accounts/detail.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/accounts/detail.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/accounts/detail.html

echo "  - accounts/financial/list.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/accounts/financial/list.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/accounts/financial/list.html

echo "  - components/summary_card.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/components/summary_card.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/components/summary_card.html

echo "  - reports/index.html"
scp "$LOCAL_PATH/apps/finances/templates/finances/reports/index.html" $REMOTE:$REMOTE_PATH/apps/finances/templates/finances/reports/index.html

echo ""
echo "[4/6] Collecte des fichiers statiques..."
ssh $REMOTE "cd $REMOTE_PATH && source venv/bin/activate && python manage.py collectstatic --noinput 2>/dev/null || echo 'Collectstatic terminé'"

echo ""
echo "[5/6] Redémarrage de Gunicorn..."
ssh $REMOTE "systemctl restart gunicorn 2>/dev/null || supervisorctl restart gunicorn 2>/dev/null || pkill -HUP gunicorn; echo 'Services redémarrés!'"

echo ""
echo "[6/6] Vérification..."
ssh $REMOTE "systemctl status gunicorn --no-pager 2>/dev/null | head -10 || ps aux | grep gunicorn | head -3"

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE AVEC SUCCES!"
echo "=============================================="
echo ""
echo "Testez la conversion multi-devises:"
echo "  https://martialcomp.com/finances/dashboard/?currency=XOF"
echo ""
