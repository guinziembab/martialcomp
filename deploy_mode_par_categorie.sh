#!/bin/bash
# Script de déploiement: Mode Combat par Catégorie
# Permet de basculer chaque catégorie individuellement entre mode Équipe et Individuel

echo "=== Déploiement: Mode Combat par Catégorie ==="
echo "Date: $(date)"

# Configuration
REMOTE="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/martialcomp"
LOCAL_PATH="c:/martial_hub_django/martialcomp"

echo ""
echo "1. Transfert de la migration..."
scp "$LOCAL_PATH/apps/competitions/migrations/0025_add_combat_mode_to_category.py" \
    "$REMOTE:$REMOTE_PATH/apps/competitions/migrations/"

echo ""
echo "2. Transfert du modèle categories.py..."
scp "$LOCAL_PATH/apps/competitions/models/categories.py" \
    "$REMOTE:$REMOTE_PATH/apps/competitions/models/"

echo ""
echo "3. Transfert de la vue combat.py..."
scp "$LOCAL_PATH/apps/competitions/views/combat.py" \
    "$REMOTE:$REMOTE_PATH/apps/competitions/views/"

echo ""
echo "4. Transfert du template competition_mode_switch.html..."
scp "$LOCAL_PATH/apps/competitions/templates/competitions/combat/competition_mode_switch.html" \
    "$REMOTE:$REMOTE_PATH/apps/competitions/templates/competitions/combat/"

echo ""
echo "5. Connexion SSH pour appliquer la migration et redémarrer..."
echo "Exécutez les commandes suivantes sur le serveur:"
echo ""
echo "cd $REMOTE_PATH"
echo "source ../venv/bin/activate"
echo "python manage.py migrate competitions 0025_add_combat_mode_to_category"
echo ""
echo "# Puis redémarrer gunicorn:"
echo "pkill -f gunicorn"
echo "nohup gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120 > gunicorn.log 2>&1 &"
echo "disown"
echo ""
echo "=== Fin du script ==="
