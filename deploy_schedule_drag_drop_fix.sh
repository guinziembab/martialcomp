#!/bin/bash
# Script de deploiement pour les corrections du planning drag & drop AJAX
# Corrections: Drag & drop avec modal rapide au lieu de redirection

echo "=== Deploiement Corrections Planning Drag & Drop AJAX ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers a deployer
FILES=(
    "apps/competitions/templates/competitions/management/schedule.html"
    "apps/competitions/views/management/schedule.py"
    "apps/competitions/views/management/__init__.py"
    "apps/competitions/urls/management.py"
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
echo "  OK Drag & drop ouvre un modal rapide au lieu de rediriger"
echo "  OK Modal avec confirmation d'heure de debut et duree"
echo "  OK API AJAX pour ajout rapide de categorie"
echo "  OK API pour recuperer prochaine heure disponible"
echo "  OK Fallback vers formulaire complet si Bootstrap absent"
echo ""
echo "Testez le planning :"
echo "  https://martialcomp.com/fr/competitions/management/schedule/4/overview/"
echo ""
echo "Pour ajouter des tatamis, utilisez le bouton 'Parametres' ou 'Gerer les tatamis'"
