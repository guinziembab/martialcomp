#!/bin/bash
# =============================================================================
# DIAGNOSTIC ET CORRECTION - SYSTÈME JUGES AD-HOC
# Date: 2025-12-03
# Description: Script à exécuter sur le serveur de production pour diagnostiquer
#              et corriger le problème "Chargement..." infini
# =============================================================================

# Configuration
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH="/var/www/vhosts/martialcomp.com/venv"

echo "=========================================="
echo "DIAGNOSTIC SYSTÈME JUGES AD-HOC"
echo "=========================================="

# Se placer dans le bon répertoire
cd ${REMOTE_PATH}
source ${VENV_PATH}/bin/activate

echo ""
echo "[1/6] Test d'import des modules..."
python3 manage.py shell -c "
from apps.competitions.views.adhoc_judges import eligible_practitioners, adhoc_judges_list
print('✓ Import adhoc_judges views: OK')

from apps.competitions.models.adhoc_judges import AdHocJudge
print('✓ Import AdHocJudge model: OK')

from apps.competitions.utils.decorators import manager_required
print('✓ Import manager_required decorator: OK')
"

echo ""
echo "[2/6] Vérification de la migration AdHocJudge..."
python3 manage.py showmigrations competitions | grep adhoc

echo ""
echo "[3/6] Vérification des URLs..."
python3 manage.py shell -c "
from django.urls import reverse
try:
    url = reverse('competitions:adhoc_judges:eligible', kwargs={'competition_id': 1})
    print(f'✓ URL eligible: {url}')
except Exception as e:
    print(f'✗ Erreur URL eligible: {e}')

try:
    url = reverse('competitions:adhoc_judges:list', kwargs={'competition_id': 1})
    print(f'✓ URL list: {url}')
except Exception as e:
    print(f'✗ Erreur URL list: {e}')
"

echo ""
echo "[4/6] Test de la vue avec un utilisateur admin..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.competitions.models import Competition
User = get_user_model()

# Récupérer un admin
admin = User.objects.filter(is_staff=True).first()
if admin:
    print(f'✓ Utilisateur admin trouvé: {admin.username}')
else:
    print('✗ Aucun utilisateur admin trouvé')

# Récupérer une compétition
comp = Competition.objects.first()
if comp:
    print(f'✓ Compétition trouvée: {comp.title} (id={comp.id})')
else:
    print('✗ Aucune compétition trouvée')
"

echo ""
echo "[5/6] Vérification des logs d'erreur récents..."
if [ -f "${REMOTE_PATH}/logs/gunicorn_error.log" ]; then
    echo "Dernières 20 lignes du log d'erreur:"
    tail -20 ${REMOTE_PATH}/logs/gunicorn_error.log | grep -i "adhoc\|error\|exception" || echo "(aucune erreur liée aux ad-hoc)"
else
    echo "Log d'erreur non trouvé"
fi

echo ""
echo "[6/6] Vérification du fichier adhoc_judges.py sur le serveur..."
if [ -f "${REMOTE_PATH}/apps/competitions/views/adhoc_judges.py" ]; then
    echo "✓ Fichier adhoc_judges.py présent"
    head -20 ${REMOTE_PATH}/apps/competitions/views/adhoc_judges.py
else
    echo "✗ Fichier adhoc_judges.py MANQUANT!"
fi

if [ -f "${REMOTE_PATH}/apps/competitions/urls/adhoc_judges.py" ]; then
    echo "✓ Fichier urls/adhoc_judges.py présent"
else
    echo "✗ Fichier urls/adhoc_judges.py MANQUANT!"
fi

echo ""
echo "=========================================="
echo "COMMANDES POUR TESTER L'API MANUELLEMENT"
echo "=========================================="
echo ""
echo "# Tester l'API avec curl (remplacer COMPETITION_ID par l'ID réel):"
echo "curl -v -H 'Cookie: sessionid=VOTRE_SESSION' 'https://martialcomp.com/fr/competitions/adhoc-judges/competition/COMPETITION_ID/eligible/'"
echo ""
echo "# Ou via le shell Django:"
echo "python3 manage.py shell"
echo ">>> from apps.competitions.models import Competition"
echo ">>> from apps.competitions.models.adhoc_judges import AdHocJudge"
echo ">>> comp = Competition.objects.get(id=COMPETITION_ID)"
echo ">>> eligible = AdHocJudge.get_eligible_participants(comp)"
echo ">>> print(f'Registered: {eligible[\"registered_participants\"].count()}')"
echo ">>> print(f'Discipline: {eligible[\"discipline_practitioners\"].count()}')"

echo ""
echo "=========================================="
echo "SOLUTION SI LE PROBLÈME PERSISTE"
echo "=========================================="
echo ""
echo "1. Redéployer le décorateur manager_required corrigé:"
echo "   scp decorators.py martialcomp:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/utils/"
echo ""
echo "2. Vider le cache et redémarrer:"
echo "   rm -rf ${REMOTE_PATH}/__pycache__"
echo "   find ${REMOTE_PATH}/apps -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null"
echo "   pkill -f gunicorn"
echo "   ${VENV_PATH}/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8888 --workers 3 --daemon"
echo ""
echo "=========================================="
echo "FIN DU DIAGNOSTIC"
echo "=========================================="
