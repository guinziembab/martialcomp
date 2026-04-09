#!/bin/bash
# Script de diagnostic et correction de l'affichage des noms de pratiquants
# Le problème: les numéros de licence/emails s'affichent au lieu des noms

echo "=== Diagnostic et correction de l'affichage des noms de pratiquants ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à vérifier/synchroniser
FILES_TO_SYNC=(
    "apps/competitions/templates/competitions/dashboard/club.html"
    "apps/competitions/templates/competitions/club/practitioners_enhanced.html"
    "apps/competitions/models/practitioners.py"
)

echo "=== ÉTAPE 1: Diagnostic sur le serveur de production ==="
echo ""

# Vérifier la méthode __str__ du modèle Practitioner sur la production
echo "1. Vérification de la méthode __str__ sur la production..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && grep -A 5 'def __str__' apps/competitions/models/practitioners.py | head -10"

echo ""
echo "2. Vérification des templates sur la production..."

# Vérifier comment le nom est affiché dans club.html
echo ""
echo "--- club.html: Affichage du nom dans le tableau ---"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && grep -n 'first_name.*last_name\|practitioner.first_name' apps/competitions/templates/competitions/dashboard/club.html | head -10"

echo ""
echo "--- practitioners_enhanced.html: Affichage du nom ---"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && grep -n 'first_name.*last_name\|practitioner.first_name' apps/competitions/templates/competitions/club/practitioners_enhanced.html | head -10"

echo ""
echo "=== ÉTAPE 2: Synchronisation des fichiers ==="
echo ""

for file in "${FILES_TO_SYNC[@]}"; do
    if [ -f "$file" ]; then
        echo "Synchronisation de $file..."
        scp "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file"
        if [ $? -eq 0 ]; then
            echo "  ✓ $file synchronisé"
        else
            echo "  ✗ Erreur lors de la synchronisation de $file"
        fi
    else
        echo "  ⚠ Fichier local non trouvé: $file"
    fi
done

echo ""
echo "=== ÉTAPE 3: Nettoyage du cache et redémarrage ==="
echo ""

# Vider le cache Django
echo "Nettoyage du cache Django..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && source venv/bin/activate && python manage.py clear_cache 2>/dev/null || echo 'Pas de commande clear_cache'"

# Supprimer les fichiers .pyc
echo "Suppression des fichiers .pyc..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && find . -name '*.pyc' -delete && find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null"

# Redémarrer Gunicorn
echo "Redémarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "sudo systemctl reload gunicorn || sudo systemctl restart gunicorn"

echo ""
echo "=== ÉTAPE 4: Vérification finale ==="
echo ""

# Vérifier que les fichiers sont bien synchronisés
echo "Vérification des fichiers synchronisés..."
for file in "${FILES_TO_SYNC[@]}"; do
    echo ""
    echo "--- $file ---"
    if [[ "$file" == *"practitioners.py" ]]; then
        ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && grep -A 2 'def __str__' $file"
    else
        ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && grep -n 'practitioner.first_name.*practitioner.last_name' $file | head -3"
    fi
done

echo ""
echo "=== Terminé ==="
echo ""
echo "Vérifiez maintenant les pages:"
echo "  - https://martialcomp.com/fr/competitions/dashboard/club/"
echo "  - https://martialcomp.com/fr/competitions/club/practitioners/"
echo ""
echo "Si le problème persiste, videz le cache de votre navigateur (Ctrl+Shift+R)"
