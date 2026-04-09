#!/bin/bash
# Script de déploiement du template Create/Update Competition Dark/Gold Theme
# + Affichage bannière dans detail_enhanced + URLs scoring corrigées
# + Gestion des catégories (fix erreur 500)
# Date: 2024-12-01

REMOTE_HOST="root@87.106.162.45"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=== Déploiement Templates Competition Dark/Gold Theme ==="
echo ""

# 1. Backup des fichiers existants
echo "[1/6] Backup des fichiers existants..."
ssh $REMOTE_HOST "
    cd $REMOTE_PATH/apps/competitions/templates/competitions/competition/
    cp create.html create.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'create.html backup créé'
    cp detail_enhanced.html detail_enhanced.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'detail_enhanced.html backup créé'

    cd $REMOTE_PATH/apps/competitions/templates/competitions/categories/
    cp manage.html manage.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'manage.html backup créé'

    cd $REMOTE_PATH/apps/competitions/templates/competitions/management/
    cp scoring_dashboard.html scoring_dashboard.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'scoring_dashboard.html backup créé'
    cp judges.html judges.html.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'judges.html backup créé'

    cd $REMOTE_PATH/apps/competitions/urls/
    cp management.py management.py.backup_\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'management.py backup créé'
"

# 2. Copie des templates Competition
echo "[2/6] Copie des templates Competition..."
scp apps/competitions/templates/competitions/competition/create.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/competition/create.html

scp apps/competitions/templates/competitions/competition/detail_enhanced.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/competition/detail_enhanced.html

# 3. Copie du template Categories (fix erreur 500)
echo "[3/6] Copie du template Categories (fix erreur 500)..."
scp apps/competitions/templates/competitions/categories/manage.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/categories/manage.html

# 4. Copie des templates Management (scoring + judges)
echo "[4/6] Copie des templates Management..."
scp apps/competitions/templates/competitions/management/scoring_dashboard.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/scoring_dashboard.html

scp apps/competitions/templates/competitions/management/judges.html \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/management/judges.html

# 5. Copie des URLs corrigées
echo "[5/6] Copie des URLs Management corrigées..."
scp apps/competitions/urls/management.py \
    $REMOTE_HOST:$REMOTE_PATH/apps/competitions/urls/management.py

# 6. Redémarrage du service
echo "[6/6] Redémarrage de Gunicorn..."
ssh $REMOTE_HOST "systemctl restart martialcomp || supervisorctl restart martialcomp || pkill -HUP gunicorn"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Fichiers déployés:"
echo "  - create.html (Dark/Gold Theme - Create/Update Competition)"
echo "  - detail_enhanced.html (Affichage bannière compétition)"
echo "  - manage.html (Dark/Gold Theme - Gestion catégories - FIX ERREUR 500)"
echo "  - scoring_dashboard.html (Dark/Gold Theme)"
echo "  - judges.html (Fix JS onglets)"
echo "  - management.py (URLs scoring corrigées)"
echo ""
echo "URLs à tester:"
echo "  - https://martialcomp.com/fr/competitions/competitions/create/"
echo "  - https://martialcomp.com/fr/competitions/competitions/4/update/"
echo "  - https://martialcomp.com/fr/competitions/competitions/4/categories/ (FIX ERREUR 500)"
echo "  - https://martialcomp.com/fr/competitions/competitions/4/detail/"
echo "  - https://martialcomp.com/fr/competitions/management/scoring/4/"
echo "  - https://martialcomp.com/fr/competitions/management/scoring/4/category/33/setup/"
echo "  - https://martialcomp.com/fr/competitions/management/4/judges/"
echo ""
echo "Vérifications:"
echo "  1. Les onglets du formulaire create/update fonctionnent"
echo "  2. Le bouton 'Gérer les catégories existantes' fonctionne (plus d'erreur 500)"
echo "  3. La bannière s'affiche dans la page de détail"
echo "  4. Les onglets juges fonctionnent"
echo "  5. Les pages scoring ne génèrent plus d'erreur 500"
