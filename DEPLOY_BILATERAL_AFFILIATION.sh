#!/bin/bash
# Script de deploiement - Systeme d'affiliation bilaterale
# Date: 2025-12-28

set -e

echo "=== DEPLOIEMENT SYSTEME AFFILIATION BILATERALE ==="

# Connexion au serveur
SERVER="martialcomp@ssh.cluster030.hosting.ovh.net"
REMOTE_PATH="/home/martialcomp/www"

# Fichiers a transferer
echo "1. Transfert du modele Organization..."
scp -O "c:/martial_hub_django/martialcomp/apps/organizations/models.py" "$SERVER:$REMOTE_PATH/apps/organizations/models.py"

echo "2. Transfert de la migration..."
scp -O "c:/martial_hub_django/martialcomp/apps/organizations/migrations/0006_add_bilateral_affiliation_approval.py" "$SERVER:$REMOTE_PATH/apps/organizations/migrations/"

echo "3. Transfert de la vue federation..."
scp -O "c:/martial_hub_django/martialcomp/apps/competitions/views/dashboard/federations.py" "$SERVER:$REMOTE_PATH/apps/competitions/views/dashboard/federations.py"

echo "4. Transfert du template..."
scp -O "c:/martial_hub_django/martialcomp/apps/competitions/templates/competitions/dashboard/federation_clubs.html" "$SERVER:$REMOTE_PATH/apps/competitions/templates/competitions/dashboard/federation_clubs.html"

echo "5. Application des migrations sur le serveur..."
ssh "$SERVER" "cd $REMOTE_PATH && source ../venv/bin/activate && python manage.py migrate organizations --settings=config.settings.production"

echo "6. Collecte des fichiers statiques..."
ssh "$SERVER" "cd $REMOTE_PATH && source ../venv/bin/activate && python manage.py collectstatic --noinput --settings=config.settings.production"

echo "7. Redemarrage de Gunicorn..."
ssh "$SERVER" "pkill -f gunicorn || true; sleep 2; cd $REMOTE_PATH && source ../venv/bin/activate && nohup gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2 --timeout 120 > gunicorn.log 2>&1 &"

echo ""
echo "=== DEPLOIEMENT TERMINE ==="
echo "Le systeme d'affiliation bilaterale est maintenant deploye."
echo ""
echo "Fonctionnalites:"
echo "- Federation peut inviter un club (en attente d'approbation du club)"
echo "- Club peut demander une affiliation (en attente d'approbation de la federation)"
echo "- Les deux parties doivent approuver pour que l'affiliation soit active"
echo "- Interface mise a jour avec 3 sections: demandes, invitations, affilies"
