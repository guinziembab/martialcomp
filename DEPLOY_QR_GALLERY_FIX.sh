#!/bin/bash
# =============================================================================
# DEPLOIEMENT - Corrections QR Codes et Galerie
# =============================================================================
#
# CORRECTIONS APPLIQUEES:
#   1. QR Codes: Ajout de {{ MEDIA_URL }} devant le chemin de l'image
#   2. Galerie: object-fit: contain au lieu de cover pour afficher l'image entiere
#
# UTILISATION DEPUIS WINDOWS (PowerShell):
#
#   1. Copier le template corrige:
#      scp apps/competitions/templates/organizations/sites/club_template.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/sites/
#
#   2. Redemarrer gunicorn:
#      ssh martialcomp-production "pkill -HUP -f 'gunicorn.*config.wsgi'"
#
# =============================================================================

# Si execute directement sur le serveur:
echo "==========================================="
echo "  DEPLOIEMENT FIX QR CODES & GALERIE"
echo "==========================================="
echo ""
echo "Corrections appliquees:"
echo "  1. QR Codes: {{ MEDIA_URL }}{{ qr_data.1 }}"
echo "  2. Galerie: object-fit: contain (image complete)"
echo ""

VENV_PYTHON="/var/www/vhosts/martialcomp.com/venv/bin/python"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

cd "${PROJECT_PATH}"

echo "[1/2] Verification du fichier template..."
if [ -f "apps/competitions/templates/organizations/sites/club_template.html" ]; then
    echo "  OK: club_template.html present"
else
    echo "  ERREUR: club_template.html non trouve"
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
    echo "Testez sur: https://martialcomp.com/org/khiphap/"
    echo "  - Les QR codes doivent maintenant s'afficher"
    echo "  - Les images galerie sont affichees en entier"
else
    echo "ATTENTION: Gunicorn ne repond pas"
fi
