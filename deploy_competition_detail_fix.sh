#!/bin/bash

# Script de déploiement de la correction pour competition_detail
# Corrige l'erreur 500 sur la page publique des compétitions

echo "=== DÉPLOIEMENT CORRECTION COMPETITION_DETAIL ==="
echo "Date: $(date)"

# Configuration
LOCAL_VIEW="/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/competitions.py"
REMOTE_VIEW_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/"
SSH_HOST="martialcomp-production"

echo "1. Vérification du fichier local..."
if [ ! -f "$LOCAL_VIEW" ]; then
    echo "❌ Erreur: Fichier local non trouvé"
    exit 1
fi

echo "2. Création d'une sauvegarde sur le serveur..."
ssh $SSH_HOST "cd $REMOTE_VIEW_PATH && cp competitions.py competitions.py.backup_detail_fix_$(date +%Y%m%d_%H%M%S)"

echo "3. Copie du fichier corrigé..."
scp "$LOCAL_VIEW" "$SSH_HOST:$REMOTE_VIEW_PATH/competitions.py"

echo "4. Redémarrage des services Django..."
ssh $SSH_HOST "sudo systemctl restart gunicorn 2>/dev/null || true"
ssh $SSH_HOST "sudo systemctl reload nginx"

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ !"
echo ""
echo "=== CORRECTIONS APPLIQUÉES ==="
echo "1. Ajout de l'import manquant :"
echo "   from apps.users.models import UserProfile"
echo ""
echo "2. Correction des références à l'organisation :"
echo "   - competition.organization → competition.organizing_organization"
echo "   - Ajout de hasattr() pour vérifier l'existence"
echo ""
echo "=== VÉRIFICATION ==="
echo "1. Ouvrir https://martialcomp.com/fr/competitions/competitions/4/"
echo "2. La page devrait maintenant s'afficher correctement"
echo "3. Selon votre rôle, vous serez soit :"
echo "   - Redirigé vers l'interface de gestion (si organisateur)"
echo "   - Montré la page d'inscription publique (si participant)"
echo ""
echo "Si problème, restaurer avec :"
echo "ssh $SSH_HOST 'cd $REMOTE_VIEW_PATH && cp competitions.py.backup_detail_fix_* competitions.py'"
echo "ssh $SSH_HOST 'sudo systemctl restart gunicorn'"