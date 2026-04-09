#!/bin/bash
# =============================================================================
# DEPLOIEMENT FINAL - Banniere et Galerie avec limites corrigees
# =============================================================================
# Limites de taille:
#   - Banniere: 5 Mo max
#   - Images galerie: 3 Mo max par image
#
# UTILISATION DEPUIS WINDOWS (PowerShell ou Git Bash):
#
#   1. Copier les fichiers:
#      scp apps/organizations/models.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/
#      scp apps/organizations/migrations/0004_add_banner_gallery.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/migrations/
#      scp apps/competitions/views/organization_sites.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/
#      scp apps/competitions/organization_sites.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/
#      scp apps/competitions/templates/organizations/admin/site_management.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/admin/
#      scp apps/competitions/templates/organizations/sites/club_template.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/sites/
#
#   2. Appliquer la migration et redemarrer:
#      ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py migrate organizations && pkill -HUP -f 'gunicorn.*config.wsgi'"
#
# =============================================================================

# Si execute sur le serveur directement:
VENV_PYTHON="/var/www/vhosts/martialcomp.com/venv/bin/python"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=========================================="
echo "  DEPLOIEMENT BANNIERE & GALERIE"
echo "=========================================="
echo ""
echo "Limites de taille:"
echo "  - Banniere: 5 Mo max"
echo "  - Images galerie: 3 Mo max"
echo ""

cd "${PROJECT_PATH}"

echo "[1/3] Application de la migration organizations..."
${VENV_PYTHON} manage.py migrate organizations --verbosity=1

echo "[2/3] Collection des fichiers statiques..."
${VENV_PYTHON} manage.py collectstatic --noinput --verbosity=0 2>/dev/null || true

echo "[3/3] Redemarrage de gunicorn..."
pkill -HUP -f 'gunicorn.*config.wsgi' 2>/dev/null || true
sleep 2

if pgrep -f 'gunicorn.*config.wsgi' > /dev/null; then
    echo ""
    echo "=========================================="
    echo "  DEPLOIEMENT TERMINE AVEC SUCCES!"
    echo "=========================================="
    echo ""
    echo "Testez sur: /org/{slug}/admin/site/"
else
    echo "ATTENTION: Gunicorn ne repond pas. Verification..."
fi
