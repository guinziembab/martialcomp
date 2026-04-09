#!/bin/bash
# =============================================================================
# DÉPLOIEMENT CORRECTIONS COMPLÈTES - 26 NOVEMBRE 2025
# =============================================================================
#
# PROBLÈMES CORRIGÉS:
# -------------------
# 1. Bug AIKIDO assignée par défaut dans l'onboarding club (template)
# 2. Bug AIKIDO dans _get_default_grade() pour les juges (judge.py)
# 3. Erreur 500 sur /dashboard/manager/ (template manager.html)
# 4. Ajout vue update_club_settings pour éditer nom/disciplines/logo
#
# =============================================================================

# Configuration
LOCAL_PATH="c:/martial_hub_django/martialcomp"
REMOTE_HOST="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== DÉPLOIEMENT CORRECTIONS - $(date) ==="
echo ""

# Liste des fichiers à transférer
FILES_TO_TRANSFER=(
    "apps/competitions/templates/competitions/onboarding/club_creation.html"
    "apps/competitions/templates/competitions/dashboard/manager.html"
    "apps/competitions/views/onboarding/judge.py"
    "apps/competitions/views/dashboard/club.py"
    "apps/competitions/urls/dashboard.py"
)

echo "=== Fichiers à transférer ==="
for file in "${FILES_TO_TRANSFER[@]}"; do
    echo "  - $file"
done
echo ""

# Commandes SCP à exécuter
echo "=== COMMANDES SCP À EXÉCUTER ==="
echo ""

for file in "${FILES_TO_TRANSFER[@]}"; do
    echo "scp \"$LOCAL_PATH/$file\" $REMOTE_HOST:$REMOTE_PATH/$file"
done

echo ""
echo "=== OU UTILISER RSYNC ==="
echo "rsync -avz --progress \\"
for file in "${FILES_TO_TRANSFER[@]}"; do
    echo "  \"$LOCAL_PATH/$file\" \\"
done
echo "  $REMOTE_HOST:$REMOTE_PATH/"

echo ""
echo "=== APRÈS TRANSFERT - REDÉMARRER GUNICORN ==="
echo "ssh $REMOTE_HOST 'cd $REMOTE_PATH && pkill -f gunicorn && /var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 config.wsgi:application --daemon'"

echo ""
echo "=============================================================================
COMMANDES COMPLÈTES À COPIER-COLLER (depuis le poste local Windows):
=============================================================================
"

cat << 'EOF'
# Option 1: SCP fichier par fichier (PowerShell/Git Bash)

scp "c:/martial_hub_django/martialcomp/apps/competitions/templates/competitions/onboarding/club_creation.html" martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/onboarding/

scp "c:/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/manager.html" martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/

scp "c:/martial_hub_django/martialcomp/apps/competitions/views/onboarding/judge.py" martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/onboarding/

scp "c:/martial_hub_django/martialcomp/apps/competitions/views/dashboard/club.py" martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/dashboard/

scp "c:/martial_hub_django/martialcomp/apps/competitions/urls/dashboard.py" martialcomp-production:/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/urls/


# Option 2: Après transfert, redémarrer gunicorn sur le serveur

ssh martialcomp-production "cd /var/www/vhosts/martialcomp.com/httpdocs && pkill -f gunicorn && /var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 config.wsgi:application --daemon && ps aux | grep gunicorn | head -3"

EOF

echo ""
echo "=============================================================================
RÉSUMÉ DES CORRECTIONS:
=============================================================================

1. club_creation.html
   - Suppression de la condition 'checked' problématique qui assignait AIKIDO

2. manager.html
   - Ajout de {% if club %} autour des liens site web (évite NoneType error)
   - Ajout de |default:\"-\" pour discipline.name (évite NoneType error)

3. judge.py
   - Modification de _get_default_grade() pour ne plus créer de grade
     avec une discipline par défaut si aucune n'est sélectionnée

4. club.py (views/dashboard/)
   - Ajout de la vue update_club_settings() pour éditer:
     * Nom du club
     * Disciplines
     * Description, email, téléphone, adresse, etc.

5. dashboard.py (urls/)
   - Ajout de l'URL 'club/update-settings/' pour la nouvelle vue

"
