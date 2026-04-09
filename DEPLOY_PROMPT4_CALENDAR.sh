#!/bin/bash
# =============================================================
# DEPLOIEMENT PROMPT 4 - CALENDRIER UNIFIE DES EVENEMENTS
# Date: 17 Decembre 2025
# =============================================================

# Configuration
PRODUCTION_HOST="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=============================================="
echo "DEPLOIEMENT PROMPT 4 - CALENDRIER UNIFIE"
echo "=============================================="

# 1. Deployer le service CalendarService
echo ""
echo "[1/6] Deploiement du CalendarService..."
scp apps/competitions/services/calendar_service.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/services/

# 2. Deployer les fichiers API
echo ""
echo "[2/6] Deploiement des fichiers API..."
# Creer le dossier api/ et supprimer l'ancien api.py si present
ssh ${PRODUCTION_HOST} "mkdir -p ${PRODUCTION_PATH}/apps/competitions/api && rm -f ${PRODUCTION_PATH}/apps/competitions/api.py"
scp apps/competitions/api/__init__.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/api/
scp apps/competitions/api/calendar.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/api/

# 3. Deployer les templates
echo ""
echo "[3/6] Deploiement des templates..."
ssh ${PRODUCTION_HOST} "mkdir -p ${PRODUCTION_PATH}/apps/competitions/templates/competitions/components"
scp apps/competitions/templates/competitions/components/unified_calendar.html ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/templates/competitions/components/
scp apps/competitions/templates/competitions/dashboard/participant_calendar.html ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/templates/competitions/dashboard/
scp apps/competitions/templates/competitions/dashboard/participant_modern.html ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/templates/competitions/dashboard/

# 4. Deployer les vues et URLs
echo ""
echo "[4/6] Deploiement des vues et URLs..."
scp apps/competitions/views/dashboard/participant.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/views/dashboard/
scp apps/competitions/urls/dashboard.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/urls/

# 5. Mettre a jour le __init__.py des services si necessaire
echo ""
echo "[5/6] Mise a jour du services/__init__.py..."
scp apps/competitions/services/__init__.py ${PRODUCTION_HOST}:${PRODUCTION_PATH}/apps/competitions/services/

# 6. Redemarrer le serveur
echo ""
echo "[6/6] Redemarrage du serveur..."
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
echo "  - apps/competitions/services/calendar_service.py"
echo "  - apps/competitions/api/__init__.py (remplace api.py)"
echo "  - apps/competitions/api/calendar.py"
echo "  - apps/competitions/templates/competitions/components/unified_calendar.html"
echo "  - apps/competitions/templates/competitions/dashboard/participant_calendar.html"
echo "  - apps/competitions/templates/competitions/dashboard/participant_modern.html"
echo "  - apps/competitions/views/dashboard/participant.py"
echo "  - apps/competitions/urls/dashboard.py"
echo "  - apps/competitions/services/__init__.py"
echo ""
echo "Pour tester:"
echo "  1. Allez sur https://martialcomp.com/dashboard/participant/"
echo "  2. Verifiez le MINI WIDGET CALENDRIER dans la colonne principale"
echo "     (affiche les 6 prochains evenements avec couleurs par type)"
echo "  3. Cliquez sur 'Calendrier' dans le menu rapide (ou 'Voir tout')"
echo "  4. Verifiez que le calendrier complet s'affiche avec les filtres"
echo ""
