#!/bin/bash
# Script de déploiement pour corriger l'erreur sur /grades/dashboard/

echo "=== Déploiement des corrections pour /grades/dashboard/ ==="
echo ""

# Définir les variables
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichiers à déployer
FILES_TO_DEPLOY=(
    "apps/competitions/utils/discipline_filtering.py"
    "apps/grades/utils_module.py"
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
echo "Vérifiez que la page https://martialcomp.com/fr/grades/dashboard/ fonctionne maintenant"