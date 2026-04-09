#!/bin/bash
# =============================================================================
# DEPLOIEMENT CORRECTION - Upload Banniere/Galerie (Fix 302 redirect)
# =============================================================================
#
# PROBLEME RESOLU:
#   Les decorateurs @login_required retournaient un 302 redirect au lieu
#   de JSON, causant "Unexpected end of JSON input" dans le navigateur.
#
# SOLUTION:
#   Les vues API verifient maintenant l'authentification manuellement
#   et retournent JsonResponse 401 au lieu de rediriger.
#
# UTILISATION DEPUIS WINDOWS (PowerShell):
#
#   1. Copier les fichiers:
#      scp apps/competitions/views/organization_sites.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/
#      scp apps/competitions/templates/organizations/admin/site_management.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/admin/
#
#   2. Redemarrer gunicorn:
#      ssh martialcomp-production "pkill -HUP -f 'gunicorn.*config.wsgi'"
#
# =============================================================================

# Si execute directement sur le serveur:
echo "==========================================="
echo "  DEPLOIEMENT FIX UPLOAD BANNIERE"
echo "==========================================="
echo ""
echo "Probleme corrige:"
echo "  - Les vues API retournent JSON 401 au lieu de 302 redirect"
echo "  - Le JavaScript gere correctement les erreurs 401"
echo ""

VENV_PYTHON="/var/www/vhosts/martialcomp.com/venv/bin/python"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

cd "${PROJECT_PATH}"

echo "[1/2] Verification des fichiers..."
if [ -f "apps/competitions/views/organization_sites.py" ]; then
    echo "  OK: organization_sites.py"
else
    echo "  ERREUR: organization_sites.py non trouve"
    exit 1
fi

if [ -f "apps/competitions/templates/organizations/admin/site_management.html" ]; then
    echo "  OK: site_management.html"
else
    echo "  ERREUR: site_management.html non trouve"
    exit 1
fi

echo ""
echo "[2/2] Redemarrage de gunicorn..."
pkill -HUP -f 'gunicorn.*config.wsgi' 2>/dev/null || true
sleep 2

if pgrep -f 'gunicorn.*config.wsgi' > /dev/null; then
    echo ""
    echo "==========================================="
    echo "  DEPLOIEMENT TERMINE AVEC SUCCES!"
    echo "==========================================="
    echo ""
    echo "Test: /org/khiphap/admin/site/"
    echo "Uploadez une banniere pour verifier"
else
    echo "ATTENTION: Gunicorn ne repond pas"
fi
