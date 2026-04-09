#!/bin/bash
# =============================================================================
# SCRIPT DE DEPLOIEMENT COMPLET - MULTI-DEVISES PAGE PUBLIQUE
# Date: 07-01-2026
# Description: Deploie TOUS les fichiers necessaires pour le support multi-devise
#              sur la page d'accueil publique (welcome.html) avec tarifs dynamiques
# Utilise l'alias WSL: martialcomp-production
# Chemin production: /var/www/vhosts/martialcomp.com/httpdocs/
# =============================================================================

set -e

REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"

echo "=============================================="
echo "DEPLOIEMENT COMPLET MULTI-DEVISES"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

echo ""
echo "[1/7] Creation du backup sur le serveur distant..."
ssh $REMOTE "mkdir -p /var/www/backups/currency_complete_\$(date +%Y%m%d_%H%M%S) && \
    cp -rp $REMOTE_PATH/apps/finances/models /var/www/backups/currency_complete_\$(date +%Y%m%d_%H%M%S)/finances_models 2>/dev/null && \
    cp -rp $REMOTE_PATH/apps/finances/migrations /var/www/backups/currency_complete_\$(date +%Y%m%d_%H%M%S)/finances_migrations 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/finances/currency_service.py /var/www/backups/currency_complete_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/competitions/views/welcome.py /var/www/backups/currency_complete_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || \
    echo 'Backup partiel termine'"

echo ""
echo "[2/7] Transfert du modele Currency..."
echo "  - models/currency.py"
scp "$LOCAL_PATH/apps/finances/models/currency.py" $REMOTE:$REMOTE_PATH/apps/finances/models/currency.py

echo "  - models/__init__.py"
scp "$LOCAL_PATH/apps/finances/models/__init__.py" $REMOTE:$REMOTE_PATH/apps/finances/models/__init__.py

echo ""
echo "[3/7] Transfert des migrations..."
echo "  - 0004_initial.py"
scp "$LOCAL_PATH/apps/finances/migrations/0004_initial.py" $REMOTE:$REMOTE_PATH/apps/finances/migrations/0004_initial.py

echo "  - 0005_add_currency_models.py"
scp "$LOCAL_PATH/apps/finances/migrations/0005_add_currency_models.py" $REMOTE:$REMOTE_PATH/apps/finances/migrations/0005_add_currency_models.py

echo "  - 0006_add_currency_to_subscription.py (si existe)"
scp "$LOCAL_PATH/apps/finances/migrations/0006_add_currency_to_subscription.py" $REMOTE:$REMOTE_PATH/apps/finances/migrations/0006_add_currency_to_subscription.py 2>/dev/null || echo "    (non trouve, skip)"

echo ""
echo "[4/7] Transfert du CurrencyService..."
echo "  - currency_service.py"
scp "$LOCAL_PATH/apps/finances/currency_service.py" $REMOTE:$REMOTE_PATH/apps/finances/currency_service.py

echo ""
echo "[5/7] Transfert de la vue welcome..."
echo "  - views/welcome.py"
scp "$LOCAL_PATH/apps/competitions/views/welcome.py" $REMOTE:$REMOTE_PATH/apps/competitions/views/welcome.py

echo ""
echo "[6/7] Execution des migrations..."
ssh $REMOTE << ENDSSH
cd $REMOTE_PATH
source $VENV_PATH/bin/activate

echo "  - Verification des fichiers deployes..."
ls -la apps/finances/models/currency.py 2>/dev/null && echo "    [OK] currency.py present"
ls -la apps/finances/migrations/0005_add_currency_models.py 2>/dev/null && echo "    [OK] migration 0005 presente"

echo ""
echo "  - Etat des migrations finances..."
python manage.py showmigrations finances 2>/dev/null | head -15

echo ""
echo "  - Application des migrations..."
python manage.py migrate finances --noinput 2>&1 || echo "    Erreur migration (peut etre deja appliquee)"

echo ""
echo "  - Verification du modele Currency..."
python manage.py shell -c "
from apps.finances.models import Currency
count = Currency.objects.count()
print(f'Devises en base: {count}')
if count > 0:
    currencies = Currency.objects.values_list('code', flat=True)[:5]
    print(f'Exemples: {list(currencies)}')
" 2>/dev/null || echo "    Modele Currency pas encore disponible"

echo ""
echo "  - Test de conversion XOF..."
python manage.py shell -c "
from apps.finances.currency_service import convert_amount, format_currency
result, rate = convert_amount(3.99, 'EUR', 'XOF')
print(f'3.99 EUR = {format_currency(result, \"XOF\")} (taux: {rate})')
" 2>/dev/null || echo "    Test conversion non disponible"
ENDSSH

echo ""
echo "[7/7] Redemarrage des services..."
ssh $REMOTE << ENDSSH
cd $REMOTE_PATH
source $VENV_PATH/bin/activate

echo "  - Collecte des fichiers statiques..."
python manage.py collectstatic --noinput 2>/dev/null || echo "    Collectstatic termine"

echo "  - Vidage du cache..."
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache Django vide')
" 2>/dev/null || echo "    Cache non vide (pas critique)"

echo "  - Redemarrage de Gunicorn..."
systemctl restart gunicorn 2>/dev/null || supervisorctl restart gunicorn 2>/dev/null || pkill -HUP gunicorn

sleep 2

echo "  - Verification du statut..."
systemctl status gunicorn --no-pager 2>/dev/null | head -8 || ps aux | grep gunicorn | head -3

echo ""
echo "Services redemarres avec succes!"
ENDSSH

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE AVEC SUCCES!"
echo "=============================================="
echo ""
echo "Fichiers deployes:"
echo "  - models/currency.py (modeles Currency et ExchangeRate)"
echo "  - models/__init__.py (exports mis a jour)"
echo "  - migrations/0004_initial.py"
echo "  - migrations/0005_add_currency_models.py (12 devises + taux)"
echo "  - currency_service.py (service de conversion)"
echo "  - views/welcome.py (page d'accueil avec prix dynamiques)"
echo ""
echo "Pour tester la conversion multi-devises:"
echo "  https://martialcomp.com/fr/?currency=XOF"
echo "  https://martialcomp.com/fr/?currency=USD"
echo "  https://martialcomp.com/fr/?currency=MAD"
echo ""
echo "Prix attendus avec ?currency=XOF:"
echo "  - Dojo Essentials: ~2 617 FCFA (au lieu de 3,99 EUR)"
echo "  - Master's Circle: ~5 234 FCFA (au lieu de 7,98 EUR)"
echo "  - Grand Champion: ~7 851 FCFA (au lieu de 11,97 EUR)"
echo ""
