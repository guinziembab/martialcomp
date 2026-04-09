#!/bin/bash
# =============================================================================
# DEPLOIEMENT - Fonctionnalité Couleurs du Thème
# =============================================================================
#
# NOUVELLES FONCTIONNALITES:
#   - Champs primary_color, secondary_color, accent_color dans Organization
#   - API endpoint /api/organizations/{id}/customize/ pour sauvegarder
#   - Validation des couleurs hexadécimales
#
# UTILISATION DEPUIS WINDOWS (PowerShell):
#
#   1. Copier les fichiers modifiés:
#      scp apps/organizations/models.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/
#      scp apps/organizations/migrations/0005_add_theme_colors.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/migrations/
#      scp apps/competitions/views/organization_sites.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/
#      scp config/urls.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/config/
#
#   2. Appliquer la migration et redémarrer:
#      ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py migrate organizations && pkill -HUP -f 'gunicorn.*config.wsgi'"
#
# =============================================================================

# Si exécuté sur le serveur directement:
VENV_PYTHON="/var/www/vhosts/martialcomp.com/venv/bin/python"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "==========================================="
echo "  DEPLOIEMENT COULEURS DU THEME"
echo "==========================================="
echo ""
echo "Fonctionnalités ajoutées:"
echo "  - Couleur principale (primary_color)"
echo "  - Couleur secondaire (secondary_color)"
echo "  - Couleur d'accent (accent_color)"
echo "  - API de personnalisation"
echo ""

cd "${PROJECT_PATH}"

echo "[1/3] Application de la migration organizations..."
${VENV_PYTHON} manage.py migrate organizations --verbosity=1

echo ""
echo "[2/3] Vérification de la syntaxe Python..."
${VENV_PYTHON} -m py_compile apps/competitions/views/organization_sites.py
${VENV_PYTHON} -m py_compile config/urls.py
echo "  OK: Pas d'erreurs de syntaxe"

echo ""
echo "[3/3] Redémarrage de gunicorn..."
pkill -HUP -f 'gunicorn.*config.wsgi' 2>/dev/null || true
sleep 2

if pgrep -f 'gunicorn.*config.wsgi' > /dev/null; then
    echo ""
    echo "==========================================="
    echo "  DEPLOIEMENT TERMINE AVEC SUCCES!"
    echo "==========================================="
    echo ""
    echo "Testez sur: /org/khiphap/admin/site/"
    echo "  1. Changez une couleur avec le color picker"
    echo "  2. Cliquez 'Sauvegarder les modifications'"
    echo "  3. Vérifiez que le message de succès s'affiche"
else
    echo "ATTENTION: Gunicorn ne répond pas"
fi
