#!/bin/bash
# =============================================================================
# DEPLOIEMENT - Couleurs Dynamiques du Thème
# =============================================================================
#
# FONCTIONNALITES:
#   1. Les couleurs (primary, secondary, accent) sont sauvegardées en base
#   2. Le template public utilise les couleurs dynamiques de l'organisation
#   3. Le hero, les boutons, les badges utilisent les couleurs personnalisées
#
# FICHIERS A DEPLOYER:
#   - apps/organizations/models.py (champs couleurs)
#   - apps/organizations/migrations/0005_add_theme_colors.py
#   - apps/competitions/views/organization_sites.py (API customize)
#   - apps/competitions/templates/organizations/sites/club_template.html
#   - config/urls.py (route API)
#
# UTILISATION DEPUIS WINDOWS (PowerShell):
#
#   1. Copier tous les fichiers:
scp apps/organizations/models.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/
scp apps/organizations/migrations/0005_add_theme_colors.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/organizations/migrations/
scp apps/competitions/views/organization_sites.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/
scp apps/competitions/templates/organizations/sites/club_template.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/sites/
scp config/urls.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/config/

#   2. Appliquer la migration et redémarrer:
ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && /var/www/vhosts/martialcomp.com/venv/bin/python manage.py migrate organizations && pkill -HUP -f 'gunicorn.*config.wsgi'"

# =============================================================================
# Si exécuté directement sur le serveur:

VENV_PYTHON="/var/www/vhosts/martialcomp.com/venv/bin/python"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "==========================================="
echo "  DEPLOIEMENT COULEURS DYNAMIQUES"
echo "==========================================="
echo ""
echo "Modifications:"
echo "  - Champs primary_color, secondary_color, accent_color"
echo "  - API /api/organizations/{id}/customize/"
echo "  - Template avec couleurs CSS dynamiques"
echo ""

cd "${PROJECT_PATH}"

echo "[1/3] Application de la migration..."
${VENV_PYTHON} manage.py migrate organizations --verbosity=1

echo ""
echo "[2/3] Vérification syntaxe..."
${VENV_PYTHON} -m py_compile apps/competitions/views/organization_sites.py
${VENV_PYTHON} -m py_compile config/urls.py
echo "  OK"

echo ""
echo "[3/3] Redémarrage gunicorn..."
pkill -HUP -f 'gunicorn.*config.wsgi' 2>/dev/null || true
sleep 2

if pgrep -f 'gunicorn.*config.wsgi' > /dev/null; then
    echo ""
    echo "==========================================="
    echo "  DEPLOIEMENT TERMINE!"
    echo "==========================================="
    echo ""
    echo "Test:"
    echo "  1. Allez sur /org/khiphap/admin/site/"
    echo "  2. Changez la couleur d'accent (ex: vert #22c55e)"
    echo "  3. Cliquez 'Sauvegarder les modifications'"
    echo "  4. Visitez /org/khiphap/ - le hero devrait être vert"
else
    echo "ERREUR: Gunicorn ne répond pas"
fi
