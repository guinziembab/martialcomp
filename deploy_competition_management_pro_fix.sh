#!/bin/bash
# Script de déploiement pour les corrections de competition_management_pro
# Corrections : JavaScript, modals, URLs API, fonctions de partage

echo "=== Déploiement des corrections Competition Management Pro ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES=(
    "apps/competitions/templates/competitions/club/competition_management_pro.html"
    "apps/competitions/views/competition_management_pro.py"
)

# Vérifier que les fichiers locaux existent
echo "Vérification des fichiers locaux..."
for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        echo "✗ ERREUR: Le fichier $FILE n'existe pas localement"
        exit 1
    fi
    echo "✓ $FILE trouvé"
done

echo ""
echo "Vérification des corrections dans les fichiers..."

# Vérifier les corrections dans le template
TEMPLATE_FILE="apps/competitions/templates/competitions/club/competition_management_pro.html"
if grep -q "refereeModal" "$TEMPLATE_FILE"; then
    echo "✓ Modal refereeModal trouvé"
else
    echo "✗ ERREUR: Modal refereeModal non trouvé"
    exit 1
fi

if grep -q "function shareCompetition" "$TEMPLATE_FILE"; then
    echo "✓ Fonction shareCompetition trouvée"
else
    echo "✗ ERREUR: Fonction shareCompetition non trouvée"
    exit 1
fi

if grep -q "shareModal" "$TEMPLATE_FILE"; then
    echo "✓ Modal shareModal trouvé"
else
    echo "✗ ERREUR: Modal shareModal non trouvé"
    exit 1
fi

# Vérifier les corrections dans la vue
VIEW_FILE="apps/competitions/views/competition_management_pro.py"
if grep -q "registrations_list" "$VIEW_FILE"; then
    echo "✓ registrations_list trouvé dans la vue"
else
    echo "✗ ERREUR: registrations_list non trouvé"
    exit 1
fi

echo ""
echo "Les fichiers locaux sont corrects. Déploiement vers la production..."
echo ""

# Créer un backup sur le serveur distant
echo "Création des backups sur le serveur..."
for FILE in "${FILES[@]}"; do
    REMOTE_FILE="$REMOTE_PATH/$FILE"
    BACKUP_FILE="${REMOTE_FILE}.backup_$(date +%Y%m%d_%H%M%S)"
    
    ssh "$REMOTE_USER@$REMOTE_HOST" "if [ -f '$REMOTE_FILE' ]; then cp '$REMOTE_FILE' '$BACKUP_FILE' && echo '✓ Backup créé: $BACKUP_FILE'; else echo '⚠ Fichier non existant: $REMOTE_FILE'; fi"
done

echo ""
echo "Copie des fichiers vers la production..."

# Copier les fichiers
for FILE in "${FILES[@]}"; do
    REMOTE_FILE="$REMOTE_PATH/$FILE"
    echo "Copie de $FILE..."
    scp "$FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_FILE"
    if [ $? -eq 0 ]; then
        echo "✓ $FILE copié avec succès"
    else
        echo "✗ ERREUR: Impossible de copier $FILE"
        exit 1
    fi
done

echo ""
echo "Redémarrage du serveur Gunicorn..."

# Redémarrer Gunicorn
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && pkill -HUP gunicorn || (ps aux | grep gunicorn | grep -v grep | awk '{print \$2}' | head -1 | xargs -r kill -HUP) && echo '✓ Signal HUP envoyé à Gunicorn' || echo '⚠ Impossible de redémarrer Gunicorn automatiquement'"

echo ""
echo "=== Déploiement terminé ==="
echo ""
echo "Vérifications à effectuer :"
echo "1. Tester le bouton 'Ajouter un arbitre' dans l'onglet Arbitres"
echo "2. Tester les boutons 'Actions rapides' (Publier, Partager)"
echo "3. Vérifier que les inscriptions s'affichent dans l'onglet Inscriptions"
echo "4. Vérifier que les boutons Editer/Supprimer fonctionnent"
echo ""
echo "En cas de problème, restaurer les backups :"
for FILE in "${FILES[@]}"; do
    echo "  scp $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE.backup_* $FILE"
done
