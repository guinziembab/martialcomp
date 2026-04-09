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
    "apps/competitions/urls/club.py"
)

echo "Vérification des fichiers locaux..."
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "✗ ERREUR: Le fichier $file n'existe pas localement"
        exit 1
    fi
    echo "✓ $file trouvé"
done

echo ""
echo "Vérification des corrections dans le template..."

TEMPLATE_FILE="apps/competitions/templates/competitions/club/competition_management_pro.html"

# Vérifier que les corrections JavaScript sont présentes
if grep -q "const messages = {" "$TEMPLATE_FILE"; then
    echo "✓ Objet messages trouvé"
else
    echo "✗ ERREUR: L'objet messages n'est pas trouvé dans le template"
    exit 1
fi

# Vérifier que les modals sont présents
if grep -q "id=\"refereeModal\"" "$TEMPLATE_FILE"; then
    echo "✓ Modal refereeModal trouvé"
else
    echo "✗ ERREUR: Le modal refereeModal n'est pas trouvé"
    exit 1
fi

if grep -q "id=\"shareModal\"" "$TEMPLATE_FILE"; then
    echo "✓ Modal shareModal trouvé"
else
    echo "✗ ERREUR: Le modal shareModal n'est pas trouvé"
    exit 1
fi

# Vérifier que les URLs sont corrigées
if grep -q "publishCompetition:.*/publish/" "$TEMPLATE_FILE"; then
    echo "✓ URL publishCompetition corrigée"
else
    echo "✗ ERREUR: URL publishCompetition non corrigée"
    exit 1
fi

echo ""
echo "=== Déploiement vers la production ==="
echo ""

# Fonction pour copier un fichier
deploy_file() {
    local_file=$1
    remote_file="$REMOTE_PATH/$local_file"
    
    echo "Copie de $local_file..."
    scp "$local_file" "$REMOTE_USER@$REMOTE_HOST:$remote_file"
    if [ $? -ne 0 ]; then
        echo "✗ ERREUR: Impossible de copier $local_file"
        return 1
    fi
    echo "✓ $local_file copié avec succès"
    return 0
}

# Copier tous les fichiers
for file in "${FILES[@]}"; do
    deploy_file "$file"
    if [ $? -ne 0 ]; then
        echo ""
        echo "=== ÉCHEC DU DÉPLOIEMENT ==="
        echo ""
        echo "Veuillez exécuter manuellement :"
        echo "  scp $file $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file"
        exit 1
    fi
done

echo ""
echo "Redémarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && sudo systemctl reload gunicorn"
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ ATTENTION: Erreur lors du redémarrage de Gunicorn"
    echo "Veuillez redémarrer manuellement :"
    echo "  ssh $REMOTE_USER@$REMOTE_HOST \"cd $REMOTE_PATH && sudo systemctl reload gunicorn\""
    exit 1
fi

echo "✓ Gunicorn redémarré avec succès"
echo ""

# Vérification finale
echo "=== Déploiement terminé avec succès ==="
echo ""
echo "Corrections appliquées :"
echo "  ✓ Correction des erreurs JavaScript ({% trans %} dans JS)"
echo "  ✓ Ajout du modal refereeModal pour les arbitres"
echo "  ✓ Ajout du modal shareModal pour le partage"
echo "  ✓ Correction des URLs API (publish, types, etc.)"
echo "  ✓ Ajout de la fonction shareCompetition()"
echo "  ✓ Amélioration de la gestion des erreurs"
echo ""
echo "Vérifiez que la page fonctionne maintenant :"
echo "  https://martialcomp.com/fr/competitions/club/competitions/[ID]/manage/pro/"
echo ""
echo "IMPORTANT: Videz le cache du navigateur (Ctrl+F5) pour charger la nouvelle version."
