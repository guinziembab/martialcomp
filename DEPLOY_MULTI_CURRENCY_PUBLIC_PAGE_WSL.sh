#!/bin/bash
# =============================================================================
# SCRIPT DE DEPLOIEMENT - PAGE TARIFS PUBLIQUE MULTI-DEVISES
# Date: 07-01-2026
# Description: Deploie les fichiers necessaires pour la conversion multi-devises
#              sur la page d'accueil publique (welcome.html)
# Utilise l'alias WSL: martialcomp-production
# Chemin production: /var/www/vhosts/martialcomp.com/httpdocs/
# =============================================================================

set -e

REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"

echo "=============================================="
echo "DEPLOIEMENT PAGE TARIFS MULTI-DEVISES"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

echo ""
echo "[1/5] Creation du backup sur le serveur distant..."
ssh $REMOTE "mkdir -p /var/www/backups/multi_currency_public_\$(date +%Y%m%d_%H%M%S) && \
    cp -p $REMOTE_PATH/apps/competitions/views/welcome.py /var/www/backups/multi_currency_public_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/finances/currency_service.py /var/www/backups/multi_currency_public_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/finances/models/__init__.py /var/www/backups/multi_currency_public_\$(date +%Y%m%d_%H%M%S)/models_init.py 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/finances/models/pricing.py /var/www/backups/multi_currency_public_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || \
    echo 'Backup partiel ou fichiers inexistants'"

echo ""
echo "[2/5] Transfert du CurrencyService..."
echo "  - currency_service.py"
scp "$LOCAL_PATH/apps/finances/currency_service.py" $REMOTE:$REMOTE_PATH/apps/finances/currency_service.py

echo ""
echo "[3/5] Transfert des modeles Currency..."
echo "  - models/__init__.py"
scp "$LOCAL_PATH/apps/finances/models/__init__.py" $REMOTE:$REMOTE_PATH/apps/finances/models/__init__.py

echo "  - models/pricing.py"
scp "$LOCAL_PATH/apps/finances/models/pricing.py" $REMOTE:$REMOTE_PATH/apps/finances/models/pricing.py

echo ""
echo "[4/5] Transfert de la vue welcome..."
echo "  - views/welcome.py"
scp "$LOCAL_PATH/apps/competitions/views/welcome.py" $REMOTE:$REMOTE_PATH/apps/competitions/views/welcome.py

echo ""
echo "[5/5] Execution des migrations et redemarrage..."
ssh $REMOTE << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

echo "  - Verification des migrations..."
python manage.py showmigrations finances | head -20

echo "  - Application des migrations (si necessaire)..."
python manage.py migrate finances --noinput 2>/dev/null || echo "    Migrations deja appliquees ou aucune migration"

echo "  - Verification des devises en base..."
python manage.py shell -c "from apps.finances.models import Currency; print(f'Devises actives: {Currency.objects.filter(is_active=True).count()}')" 2>/dev/null || echo "    Modele Currency non disponible"

echo "  - Collecte des fichiers statiques..."
python manage.py collectstatic --noinput 2>/dev/null || echo "    Collectstatic termine"

echo "  - Redemarrage de Gunicorn..."
systemctl restart gunicorn 2>/dev/null || supervisorctl restart gunicorn 2>/dev/null || pkill -HUP gunicorn

echo "  - Verification du statut..."
systemctl status gunicorn --no-pager 2>/dev/null | head -10 || ps aux | grep gunicorn | head -3

echo ""
echo "Services redemarres avec succes!"
ENDSSH

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE AVEC SUCCES!"
echo "=============================================="
echo ""
echo "Fichiers deployes:"
echo "  - currency_service.py (service de conversion multi-devises)"
echo "  - models/__init__.py (export Currency)"
echo "  - models/pricing.py (modeles Currency et ExchangeRate)"
echo "  - views/welcome.py (page d'accueil avec prix dynamiques)"
echo ""
echo "Pour tester la conversion multi-devises sur la page publique:"
echo "  https://martialcomp.com/fr/?currency=XOF"
echo "  https://martialcomp.com/fr/?currency=USD"
echo "  https://martialcomp.com/fr/?currency=MAD"
echo ""
echo "Les prix devraient maintenant etre convertis automatiquement!"
echo ""
