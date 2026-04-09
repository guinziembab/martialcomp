#!/bin/bash

# Script de déploiement de la correction pour manage-simple
# Corrige l'erreur 500 en ajoutant les données manquantes au contexte

echo "=== DÉPLOIEMENT CORRECTION MANAGE-SIMPLE ==="
echo "Date: $(date)"

# Configuration
LOCAL_VIEW="/mnt/c/martial_hub_django/martialcomp/apps/competitions/views/club/event_organizer.py"
LOCAL_TEMPLATE="/mnt/c/martial_hub_django/martialcomp/apps/competitions/templates/competitions/club/competition_management_simple.html"
REMOTE_VIEW_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/views/club/"
REMOTE_TEMPLATE_PATH="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/club/"
SSH_HOST="martialcomp-production"

echo "1. Vérification des fichiers locaux..."
if [ ! -f "$LOCAL_VIEW" ] || [ ! -f "$LOCAL_TEMPLATE" ]; then
    echo "❌ Erreur: Fichiers locaux non trouvés"
    exit 1
fi

echo "2. Création des sauvegardes sur le serveur..."
ssh $SSH_HOST "cd $REMOTE_VIEW_PATH && cp event_organizer.py event_organizer.py.backup_manage_simple_$(date +%Y%m%d_%H%M%S)"
ssh $SSH_HOST "cd $REMOTE_TEMPLATE_PATH && cp competition_management_simple.html competition_management_simple.html.backup_manage_simple_$(date +%Y%m%d_%H%M%S)"

echo "3. Copie des fichiers corrigés..."
scp "$LOCAL_VIEW" "$SSH_HOST:$REMOTE_VIEW_PATH/event_organizer.py"
scp "$LOCAL_TEMPLATE" "$SSH_HOST:$REMOTE_TEMPLATE_PATH/competition_management_simple.html"

echo "4. Redémarrage des services Django..."
ssh $SSH_HOST "sudo systemctl restart gunicorn 2>/dev/null || true"
ssh $SSH_HOST "sudo systemctl reload nginx"

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ !"
echo ""
echo "=== CORRECTIONS APPLIQUÉES ==="
echo "1. Vue event_organizer.py - competition_management_simple :"
echo "   - Ajout de la récupération des catégories de la compétition"
echo "   - Ajout des inscriptions pour chaque catégorie"
echo "   - Ajout de categories_with_registrations au contexte"
echo "   - Ajout du total des inscriptions"
echo ""
echo "2. Template competition_management_simple.html :"
echo "   - Correction de cat_data.registration_count → cat_data.count"
echo ""
echo "=== VÉRIFICATION ==="
echo "1. Ouvrir https://martialcomp.com/fr/competitions/club/competitions/4/manage-simple/"
echo "2. La page devrait maintenant s'afficher correctement"
echo "3. Vérifier :"
echo "   - Les types de compétition s'affichent"
echo "   - Les catégories s'affichent avec le nombre d'inscrits"
echo "   - Cliquer sur une catégorie affiche les inscrits"
echo ""
echo "Si problème, restaurer avec :"
echo "ssh $SSH_HOST 'cd $REMOTE_VIEW_PATH && cp event_organizer.py.backup_manage_simple_* event_organizer.py'"
echo "ssh $SSH_HOST 'cd $REMOTE_TEMPLATE_PATH && cp competition_management_simple.html.backup_manage_simple_* competition_management_simple.html'"
echo "ssh $SSH_HOST 'sudo systemctl restart gunicorn'"