#!/bin/bash

# Script de déploiement de la correction des statistiques d'inscription
# Corrige l'incohérence entre le total des inscrits et les inscrits du club

echo "=== DÉPLOIEMENT CORRECTION STATISTIQUES D'INSCRIPTION ==="
echo "Date: $(date)"

# Configuration
LOCAL_VIEW="/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/club/registrations.py"
LOCAL_TEMPLATE="/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/club/competition_registration_simple.html"
REMOTE_VIEW_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/"
REMOTE_TEMPLATE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/"
SSH_HOST="martialcomp-production"

echo "1. Vérification des fichiers locaux..."
if [ ! -f "$LOCAL_VIEW" ] || [ ! -f "$LOCAL_TEMPLATE" ]; then
    echo "❌ Erreur: Fichiers locaux non trouvés"
    exit 1
fi

echo "2. Création des sauvegardes sur le serveur..."
ssh $SSH_HOST "cd $REMOTE_VIEW_PATH && cp registrations.py registrations.py.backup_stats_$(date +%Y%m%d_%H%M%S)"
ssh $SSH_HOST "cd $REMOTE_TEMPLATE_PATH && cp competition_registration_simple.html competition_registration_simple.html.backup_stats_$(date +%Y%m%d_%H%M%S)"

echo "3. Copie des fichiers corrigés..."
scp "$LOCAL_VIEW" "$SSH_HOST:$REMOTE_VIEW_PATH/registrations.py"
scp "$LOCAL_TEMPLATE" "$SSH_HOST:$REMOTE_TEMPLATE_PATH/competition_registration_simple.html"

echo "4. Redémarrage des services Django..."
ssh $SSH_HOST "sudo systemctl restart gunicorn"
ssh $SSH_HOST "sudo systemctl reload nginx"

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "=== CHANGEMENTS APPORTÉS ==="
echo "1. Vue registrations.py :"
echo "   - Ajout du calcul du total global des inscrits (toutes organisations)"
echo "   - Ajout du calcul spécifique des inscrits du club actuel"
echo ""
echo "2. Template competition_registration_simple.html :"
echo "   - Affichage du total global dans la première stat-card"
echo "   - Nouvelle stat-card violette pour les inscrits du club"
echo "   - Mise à jour du compteur dans l'onglet 'Déjà inscrits'"
echo ""
echo "=== VÉRIFICATIONS À EFFECTUER ==="
echo "1. Ouvrir https://martialcomp.com/fr/competitions/club/competition-registration/4/"
echo "2. Les statistiques devraient maintenant afficher :"
echo "   - Total inscrits : Nombre total de tous les inscrits à la compétition"
echo "   - De votre club : Nombre d'inscrits uniquement de votre club"
echo "   - Pratiquants du club : Nombre total de pratiquants dans votre club"
echo "   - Restants à inscrire : Pratiquants non encore inscrits"
echo ""
echo "Si problème, restaurer avec :"
echo "ssh $SSH_HOST 'cd $REMOTE_VIEW_PATH && cp registrations.py.backup_stats_* registrations.py'"
echo "ssh $SSH_HOST 'cd $REMOTE_TEMPLATE_PATH && cp competition_registration_simple.html.backup_stats_* competition_registration_simple.html'"
echo "ssh $SSH_HOST 'sudo systemctl restart gunicorn'"