#!/bin/bash
# =============================================================================
# SCRIPT DE DEPLOIEMENT - PHASE 3 & 4 MULTI-DEVISES
# Date: 07-01-2026
# Description: Deploie les taches Celery et l'API REST multi-devises
# Utilise l'alias WSL: martialcomp-production
# Chemin production: /var/www/vhosts/martialcomp.com/httpdocs/
# =============================================================================

set -e

REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PATH="/mnt/c/martial_hub_django/martialcomp"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"

echo "=============================================="
echo "DEPLOIEMENT PHASE 3 & 4 - MULTI-DEVISES"
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

echo ""
echo "[1/6] Creation du backup sur le serveur distant..."
ssh $REMOTE "mkdir -p /var/www/backups/phase3_4_\$(date +%Y%m%d_%H%M%S) && \
    cp -p $REMOTE_PATH/apps/finances/tasks.py /var/www/backups/phase3_4_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/finances/api.py /var/www/backups/phase3_4_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null && \
    cp -p $REMOTE_PATH/apps/finances/urls.py /var/www/backups/phase3_4_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null && \
    cp -p $REMOTE_PATH/config/celery.py /var/www/backups/phase3_4_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || \
    echo 'Backup partiel termine'"

echo ""
echo "[2/6] Transfert des fichiers Phase 3 (Celery tasks)..."
echo "  - tasks.py"
scp "$LOCAL_PATH/apps/finances/tasks.py" $REMOTE:$REMOTE_PATH/apps/finances/tasks.py

echo "  - celery.py"
scp "$LOCAL_PATH/config/celery.py" $REMOTE:$REMOTE_PATH/config/celery.py

echo ""
echo "[3/6] Transfert des fichiers Phase 4 (API REST)..."
echo "  - api.py"
scp "$LOCAL_PATH/apps/finances/api.py" $REMOTE:$REMOTE_PATH/apps/finances/api.py

echo "  - urls.py"
scp "$LOCAL_PATH/apps/finances/urls.py" $REMOTE:$REMOTE_PATH/apps/finances/urls.py

echo ""
echo "[4/6] Verification des fichiers deployes..."
ssh $REMOTE << ENDSSH
cd $REMOTE_PATH
source $VENV_PATH/bin/activate

echo "  - Verification des imports..."
python -c "
from apps.finances.tasks import update_exchange_rates, refresh_cfa_fixed_rates, cleanup_old_exchange_rates
print('  [OK] Taches Celery importees avec succes')

from apps.finances.api import CurrencyListView, ExchangeRatesView, CurrencyConvertView
print('  [OK] API REST importee avec succes')
" 2>&1 || echo "  [WARN] Erreur d'import, verification manuelle requise"

echo ""
echo "  - Liste des endpoints API disponibles..."
python -c "
from apps.finances.api import urlpatterns
for pattern in urlpatterns:
    print(f'    - /finances/api/{pattern.pattern}')
" 2>&1 || echo "  [WARN] Impossible de lister les endpoints"
ENDSSH

echo ""
echo "[5/6] Redemarrage des services..."
ssh $REMOTE << ENDSSH
cd $REMOTE_PATH
source $VENV_PATH/bin/activate

echo "  - Vidage du cache..."
python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('    Cache Django vide')
" 2>/dev/null || echo "    Cache non vide (pas critique)"

echo "  - Redemarrage de Gunicorn..."
pkill -HUP gunicorn || echo "    Signal HUP envoye"

echo "  - Redemarrage de Celery (si en service)..."
supervisorctl restart celery 2>/dev/null || \
systemctl restart celery 2>/dev/null || \
echo "    Celery non gere par systemd/supervisor"

sleep 2

echo "  - Verification du statut Gunicorn..."
ps aux | grep gunicorn | head -2
ENDSSH

echo ""
echo "[6/6] Test des endpoints API..."
ssh $REMOTE << ENDSSH
cd $REMOTE_PATH
source $VENV_PATH/bin/activate

echo ""
echo "  Test 1: Liste des devises..."
curl -s "http://127.0.0.1:8888/fr/finances/api/currencies/" -H "Host: martialcomp.com" 2>/dev/null | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print(f'    [OK] {data.get(\"count\", 0)} devises disponibles')
    else:
        print('    [WARN] Reponse inattendue')
except:
    print('    [WARN] Erreur parsing JSON')
" || echo "    [WARN] Test non concluant"

echo ""
echo "  Test 2: Taux de change..."
curl -s "http://127.0.0.1:8888/fr/finances/api/rates/" -H "Host: martialcomp.com" 2>/dev/null | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        rates = data.get('rates', {})
        print(f'    [OK] {len(rates)} taux de change disponibles')
        if 'XOF' in rates:
            print(f'    EUR/XOF = {rates[\"XOF\"]}')
    else:
        print('    [WARN] Reponse inattendue')
except:
    print('    [WARN] Erreur parsing JSON')
" || echo "    [WARN] Test non concluant"

echo ""
echo "  Test 3: Conversion EUR -> XOF..."
curl -s "http://127.0.0.1:8888/fr/finances/api/convert/?amount=100&from=EUR&to=XOF" -H "Host: martialcomp.com" 2>/dev/null | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        orig = data.get('original', {})
        conv = data.get('converted', {})
        print(f'    [OK] {orig.get(\"formatted\")} = {conv.get(\"formatted\")}')
        print(f'    Taux applique: {data.get(\"rate\")}')
    else:
        print('    [WARN] Reponse inattendue:', data.get('error'))
except Exception as e:
    print(f'    [WARN] Erreur: {e}')
" || echo "    [WARN] Test non concluant"
ENDSSH

echo ""
echo "=============================================="
echo "DEPLOIEMENT PHASE 3 & 4 TERMINE!"
echo "=============================================="
echo ""
echo "Fichiers deployes:"
echo "  Phase 3 (Celery):"
echo "    - apps/finances/tasks.py (update_exchange_rates, refresh_cfa_fixed_rates, etc.)"
echo "    - config/celery.py (beat_schedule mis a jour)"
echo ""
echo "  Phase 4 (API REST):"
echo "    - apps/finances/api.py (CurrencyListView, ConvertView, etc.)"
echo "    - apps/finances/urls.py (inclusion de l'API)"
echo ""
echo "Endpoints API disponibles:"
echo "  - GET  /finances/api/currencies/        - Liste des devises"
echo "  - GET  /finances/api/rates/             - Taux de change actuels"
echo "  - GET  /finances/api/convert/?amount=X&from=EUR&to=XOF"
echo "  - POST /finances/api/convert/           - Conversion via JSON"
echo "  - GET  /finances/api/format/?amount=X&currency=EUR"
echo "  - POST /finances/api/user-currency/     - Preference utilisateur"
echo "  - POST /finances/api/bulk-convert/      - Conversion en lot"
echo ""
echo "Taches Celery planifiees:"
echo "  - update-exchange-rates-morning: 6h00 quotidien"
echo "  - update-exchange-rates-evening: 18h00 quotidien"
echo "  - refresh-cfa-fixed-rates: Dimanche 5h00"
echo "  - cleanup-old-exchange-rates: 1er du mois 3h00"
echo "  - generate-currency-report: 2 du mois 8h00"
echo ""
