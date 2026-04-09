#!/bin/bash
# =============================================================================
# DEPLOIEMENT - Corrections Couleurs Dynamiques + Calendrier
# =============================================================================
#
# CORRECTIONS APPLIQUEES:
#   1. Couleurs dynamiques: Le template utilise maintenant les variables CSS
#      dynamiques {{ organization.primary_color }}, {{ organization.secondary_color }},
#      {{ organization.accent_color }} au lieu des couleurs hardcodées
#   2. Calendrier: La requête ne filtre plus par is_published et status
#      pour afficher toutes les compétitions futures
#
# UTILISATION DEPUIS WINDOWS (PowerShell):
#
#   1. Copier les fichiers modifiés:
scp apps/competitions/templates/organizations/sites/club_template.html martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/organizations/sites/
scp apps/competitions/views/organization_sites.py martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/

#   2. Redémarrer gunicorn et vider les caches:
ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && pkill -HUP -f 'gunicorn.*config.wsgi'"

# =============================================================================
# Si exécuté directement sur le serveur:

VENV_PYTHON="/var/www/vhosts/martialcomp.com/venv/bin/python"
PROJECT_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "==========================================="
echo "  DEPLOIEMENT COULEURS + CALENDRIER"
echo "==========================================="
echo ""
echo "Corrections appliquées:"
echo "  1. Couleurs dynamiques CSS (primary_color, secondary_color, accent_color)"
echo "  2. Calendrier: affiche toutes les compétitions futures"
echo ""

cd "${PROJECT_PATH}"

echo "[1/3] Vérification syntaxe Python..."
${VENV_PYTHON} -m py_compile apps/competitions/views/organization_sites.py
if [ $? -eq 0 ]; then
    echo "  OK: Pas d'erreurs de syntaxe"
else
    echo "  ERREUR: Erreur de syntaxe dans organization_sites.py"
    exit 1
fi

echo ""
echo "[2/3] Vérification du fichier template..."
if [ -f "apps/competitions/templates/organizations/sites/club_template.html" ]; then
    # Vérifier que les variables dynamiques sont présentes
    if grep -q "organization.primary_color" apps/competitions/templates/organizations/sites/club_template.html; then
        echo "  OK: Template avec couleurs dynamiques présent"
    else
        echo "  ATTENTION: Variables de couleurs non trouvées dans le template"
    fi
else
    echo "  ERREUR: club_template.html non trouvé"
    exit 1
fi

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
    echo "IMPORTANT - Pour voir les changements:"
    echo ""
    echo "  1. Videz le cache Cloudflare:"
    echo "     - Connectez-vous à Cloudflare Dashboard"
    echo "     - Allez dans Caching > Configuration"
    echo "     - Cliquez 'Purge Everything'"
    echo ""
    echo "  2. Videz le cache du navigateur:"
    echo "     - Ctrl+Shift+R (hard refresh)"
    echo "     - Ou ouvrez en navigation privée"
    echo ""
    echo "  3. Testez sur: https://martialcomp.com/org/khiphap/"
    echo "     - Les couleurs doivent correspondre à celles de l'admin"
    echo "     - Le calendrier doit afficher les compétitions futures"
else
    echo "ATTENTION: Gunicorn ne répond pas"
fi
