#!/bin/bash
# Script de déploiement de la section Finances dans la fiche pratiquant
# Exécuter depuis le répertoire martialcomp

REMOTE_HOST="root@212.227.78.104"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SSH_KEY="$HOME/.ssh/ionos_martialcomp"

echo "=== Déploiement de la Section Finances Pratiquant ==="

# 1. Créer le répertoire services finances si nécessaire
echo "1/5 - Création du répertoire services finances..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" "mkdir -p $REMOTE_PATH/apps/finances/services/"

# 2. Transférer le service PractitionerFinanceService
echo "2/5 - Transfert du service PractitionerFinanceService..."
scp -i "$SSH_KEY" apps/finances/services/practitioner_finance_service.py "$REMOTE_HOST:$REMOTE_PATH/apps/finances/services/"

# 3. Transférer les vues Python (avec les nouvelles fonctions)
echo "3/5 - Transfert des vues Python..."
scp -i "$SSH_KEY" apps/competitions/views/club/practitioners.py "$REMOTE_HOST:$REMOTE_PATH/apps/competitions/views/club/"

# 4. Transférer les URLs
echo "4/5 - Transfert des URLs..."
scp -i "$SSH_KEY" apps/competitions/urls/club.py "$REMOTE_HOST:$REMOTE_PATH/apps/competitions/urls/"

# 5. Transférer le template mis à jour
echo "5/5 - Transfert du template..."
scp -i "$SSH_KEY" apps/competitions/templates/competitions/club/practitioner_detail_modern.html "$REMOTE_HOST:$REMOTE_PATH/apps/competitions/templates/competitions/club/"

echo ""
echo "=== Fichiers transférés ==="
echo ""
echo "Maintenant, connectez-vous au serveur et exécutez :"
echo ""
echo "ssh -i $SSH_KEY $REMOTE_HOST"
echo ""
echo "Puis sur le serveur :"
echo "  cd $REMOTE_PATH"
echo "  source ../venv/bin/activate"
echo "  python manage.py collectstatic --noinput"
echo "  sudo systemctl restart gunicorn"
echo ""
echo "=== Déploiement terminé ==="
