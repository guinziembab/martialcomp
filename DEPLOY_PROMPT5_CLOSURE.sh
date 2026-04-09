#!/bin/bash
# =============================================================
# DEPLOIEMENT PROMPT 5 - CLOTURE COMPETITION & PERFORMANCE COMBAT
# Date: 17 Decembre 2025
# =============================================================

# Configuration
PRODUCTION_HOST="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=============================================="
echo "DEPLOIEMENT PROMPT 5 - CLOTURE COMPETITION"
echo "=============================================="

# 1. Deployer le service CompetitionClosureService
echo ""
echo "[1/7] Deploiement du CompetitionClosureService..."
scp apps/competitions/services/competition_closure_service.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/services/

# 2. Mettre a jour le __init__.py des services
echo ""
echo "[2/7] Mise a jour du services/__init__.py..."
scp apps/competitions/services/__init__.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/services/

# 3. Deployer les vues management mises a jour
echo ""
echo "[3/7] Deploiement des vues management..."
scp apps/competitions/views/management/dashboard.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/views/management/

# 4. Deployer les URLs management mises a jour
echo ""
echo "[4/7] Deploiement des URLs management..."
scp apps/competitions/urls/management.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/urls/

# 5. Deployer le template dashboard management avec modal cloture
echo ""
echo "[5/7] Deploiement du template dashboard management..."
scp apps/competitions/templates/competitions/management/dashboard.html ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/templates/competitions/management/

# 6. Deployer les fichiers dashboard participant
echo ""
echo "[6/7] Deploiement des fichiers dashboard participant..."
scp apps/competitions/views/dashboard/participant.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/views/dashboard/
scp apps/competitions/templates/competitions/dashboard/participant_modern.html ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/templates/competitions/dashboard/

# 7. Redemarrer le serveur
echo ""
echo "[7/7] Redemarrage du serveur..."
ssh ${PRODUCTION_HOST} "cd /var/www/vhosts/martialcomp.com/httpdocs && \
    VENV_PATH=\$(ls -d venv .venv env 2>/dev/null | head -1); \
    if [ -n \"\$VENV_PATH\" ]; then \
        source \$VENV_PATH/bin/activate 2>/dev/null || true; \
    fi; \
    /usr/bin/python3 manage.py collectstatic --noinput 2>/dev/null || python3 manage.py collectstatic --noinput 2>/dev/null || true; \
    PID=\$(pgrep -f 'gunicorn.*martialcomp' | head -1); \
    if [ -n \"\$PID\" ]; then \
        echo 'Redemarrage Gunicorn (PID: '\$PID')'; \
        kill -HUP \$PID; \
        sleep 2; \
        echo 'OK'; \
    else \
        echo 'PID Gunicorn non trouve - tentative systemctl'; \
        systemctl restart gunicorn 2>/dev/null || service gunicorn restart 2>/dev/null || echo 'Impossible de redemarrer'; \
    fi"

echo ""
echo "=============================================="
echo "DEPLOIEMENT TERMINE"
echo "=============================================="
echo ""
echo "Fichiers deployes:"
echo "  - apps/competitions/services/competition_closure_service.py (nouveau)"
echo "  - apps/competitions/services/__init__.py (mis a jour)"
echo "  - apps/competitions/views/management/dashboard.py (mis a jour)"
echo "  - apps/competitions/urls/management.py (mis a jour)"
echo "  - apps/competitions/templates/competitions/management/dashboard.html (mis a jour)"
echo "  - apps/competitions/views/dashboard/participant.py (mis a jour)"
echo "  - apps/competitions/templates/competitions/dashboard/participant_modern.html (mis a jour)"
echo ""
echo "FONCTIONNALITES AJOUTEES:"
echo ""
echo "1. BOUTON CLOTURE COMPETITION (Organisateur):"
echo "   - Dans le dashboard de gestion de competition"
echo "   - Bouton 'Cloturer la competition' visible quand status = 'ongoing'"
echo "   - Modal avec verification des prerequis (categories, combats)"
echo "   - Generation automatique des resultats depuis les combats"
echo ""
echo "2. WIDGET PERFORMANCE COMBAT (Participant):"
echo "   - Affiche dans le dashboard participant"
echo "   - Statistiques: combats, victoires, defaites, nuls"
echo "   - Taux de victoire avec barre de progression"
echo "   - Points marques/encaisses"
echo "   - Liste des 3 derniers combats"
echo ""
echo "Pour tester:"
echo "  1. Organisateur: Allez sur la page de gestion d'une competition"
echo "     - Verifiez le bouton 'Cloturer la competition'"
echo "     - Cliquez pour voir le modal avec les avertissements"
echo "  2. Participant: Allez sur le dashboard participant"
echo "     - Le widget 'Mes combats' s'affiche si le pratiquant a des combats"
echo ""
