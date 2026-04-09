#!/bin/bash
# Script de déploiement pour corriger les erreurs du système de grades

echo "=== Déploiement des corrections du système de grades ==="
echo ""

# Définir les variables
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES_TO_DEPLOY=(
    "apps/competitions/views/club/practitioners.py"
    "apps/competitions/forms/grades.py"
    "apps/grades/utils_module.py"
    "apps/grades/views/bulk.py"
)

echo "Fichiers à déployer:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done
echo ""

# Copier les fichiers
echo "Copie des fichiers vers le serveur..."
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo -n "  Copie de $file... "
    scp "$file" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "OK"
    else
        echo "ERREUR"
    fi
done

echo ""
echo "Redémarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && sudo systemctl reload gunicorn"

echo ""
echo "Déploiement terminé!"
echo ""
echo "Vérifiez que les pages suivantes fonctionnent maintenant:"
echo "  - https://martialcomp.com/fr/grades/bulk-assignment/"
echo "  - https://martialcomp.com/fr/grades/grade/"