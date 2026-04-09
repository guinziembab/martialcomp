#!/bin/bash
# =============================================================================
# DEPLOIEMENT PROMPT 3 - PALMARES ET RESULTATS (PRODUCTION)
# Date: 17 decembre 2025
# =============================================================================

REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SSH_HOST="martialcomp-production"

echo "========================================"
echo "DEPLOIEMENT PROMPT 3 - PALMARES"
echo "========================================"

# -----------------------------------------------------------------------------
# 1. FICHIERS CREES (nouveaux)
# -----------------------------------------------------------------------------

echo ""
echo "[1/4] Transfert du service ResultsService..."
scp apps/competitions/services/results_service.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/services/

echo ""
echo "[2/4] Transfert des templates..."
scp apps/competitions/templates/competitions/dashboard/participant_results.html ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/
scp apps/competitions/templates/competitions/dashboard/palmares_pdf.html ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/dashboard/

# -----------------------------------------------------------------------------
# 2. FICHIERS MODIFIES
# -----------------------------------------------------------------------------

echo ""
echo "[3/4] Transfert des fichiers modifies..."

# Vue participant avec ResultsService
scp apps/competitions/views/dashboard/participant.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/views/dashboard/

# Services __init__.py avec export ResultsService
scp apps/competitions/services/__init__.py ${SSH_HOST}:${REMOTE_PATH}/apps/competitions/services/

# -----------------------------------------------------------------------------
# 3. REDEMARRAGE SERVICES
# -----------------------------------------------------------------------------

echo ""
echo "[4/4] Redemarrage des services..."

# Redemarrer gunicorn
ssh ${SSH_HOST} "kill -HUP \$(pgrep -f 'gunicorn.*config.wsgi')"

# Vider le cache Django si Redis est configure
ssh ${SSH_HOST} "cd ${REMOTE_PATH} && source ../venv/bin/activate && python manage.py shell -c \"from django.core.cache import cache; cache.clear()\" 2>/dev/null || true"

echo ""
echo "========================================"
echo "DEPLOIEMENT TERMINE"
echo "========================================"
echo ""
echo "FONCTIONNALITES DEPLOYEES:"
echo "  - Compteur de medailles (or, argent, bronze)"
echo "  - Timeline des dernieres medailles"
echo "  - Statistiques de competition (taux victoire, combats)"
echo "  - Graphiques Chart.js (evolution points, medailles par discipline)"
echo "  - Points par discipline"
echo "  - Historique des grades"
echo "  - Export PDF du palmares"
echo "  - Filtres par annee et discipline"
echo ""
echo "TESTER:"
echo "  1. Se connecter en tant que participant"
echo "  2. Aller sur Dashboard > Mes resultats"
echo "  3. Verifier les medailles, graphiques et statistiques"
echo "  4. Tester les filtres par annee/discipline"
echo "  5. Tester l'export PDF"
echo ""
echo "NOTE: Si WeasyPrint n'est pas installe, l'export PDF"
echo "      affichera une version HTML imprimable."
echo ""
