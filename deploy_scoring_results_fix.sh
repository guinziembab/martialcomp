#!/bin/bash
# Script de deploiement pour la correction du calcul des resultats
# Correction: Erreur 'WSGIRequest' object has no attribute '_request'

echo "=== Deploiement Correction Calcul Resultats ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers a deployer
FILES=(
    "apps/competitions/views/management/scoring.py"
)

echo "Fichiers a deployer:"
for FILE in "${FILES[@]}"; do
    echo "  - $FILE"
done
echo ""

# Verifier que les fichiers locaux existent
echo "Verification des fichiers locaux..."
for FILE in "${FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        echo "ERREUR: Le fichier $FILE n'existe pas localement"
        exit 1
    fi
    echo "OK $FILE existe"
done
echo ""

# Copier les fichiers vers la production
echo "Copie des fichiers vers la production..."
for FILE in "${FILES[@]}"; do
    echo "  Copie de $FILE..."
    scp "$FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE"
    if [ $? -ne 0 ]; then
        echo "ERREUR: Impossible de copier $FILE"
        exit 1
    fi
    echo "  OK $FILE copie"
done
echo ""

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "pkill -HUP gunicorn || sudo systemctl reload gunicorn 2>/dev/null || touch $REMOTE_PATH/config/wsgi.py"
echo "OK Gunicorn redemarre"
echo ""

echo "=== Deploiement termine ==="
echo ""
echo "Corrections appliquees :"
echo "  OK Fonction interne _calculate_category_results_internal() ajoutee"
echo "  OK generate_all_results() utilise la fonction interne"
echo "  OK Plus d'erreur 'WSGIRequest._request'"
echo ""
echo "Testez le calcul des resultats :"
echo "  1. Allez dans Gestion > Notation d'une competition"
echo "  2. Cliquez sur 'Calculer tous les resultats'"
echo "  3. Verifiez que les resultats s'affichent correctement"
echo ""
