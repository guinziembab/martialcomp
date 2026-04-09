#!/bin/bash
# Script de déploiement du système de filtrage des pratiquants
# Exécuter depuis le répertoire martialcomp

REMOTE_HOST="root@212.227.78.104"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SSH_KEY="$HOME/.ssh/ionos_martialcomp"

echo "=== Déploiement du système de filtrage des pratiquants ==="

# 1. Transférer le fichier JavaScript
echo "1/4 - Transfert du fichier JavaScript..."
scp -i "$SSH_KEY" static/js/dashboard/practitioner_filters.js "$REMOTE_HOST:$REMOTE_PATH/static/js/dashboard/"

# 2. Transférer les vues Python
echo "2/4 - Transfert des vues Python..."
scp -i "$SSH_KEY" apps/competitions/views/club/practitioners.py "$REMOTE_HOST:$REMOTE_PATH/apps/competitions/views/club/"

# 3. Transférer les URLs
echo "3/4 - Transfert des URLs..."
scp -i "$SSH_KEY" apps/competitions/urls/club.py "$REMOTE_HOST:$REMOTE_PATH/apps/competitions/urls/"

# 4. Transférer le template dashboard
echo "4/4 - Transfert du template..."
scp -i "$SSH_KEY" apps/competitions/templates/competitions/dashboard/club.html "$REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/dashboard/"

echo ""
echo "=== Fichiers transférés ==="
echo ""
echo "Maintenant, connectez-vous au serveur et exécutez :"
echo ""
echo "ssh -i $SSH_KEY $REMOTE_HOST"
echo ""
echo "Puis sur le serveur :"
echo "  cd $REMOTE_PATH"
echo "  source venv/bin/activate"
echo "  python manage.py collectstatic --noinput"
echo "  sudo systemctl restart gunicorn"
echo ""
echo "=== Déploiement terminé ==="
