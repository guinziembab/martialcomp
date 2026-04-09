#!/bin/bash
# Script de déploiement pour corriger l'erreur 500 sur /competitions/dashboard/club/
# Corrections appliquées :
# 1. Déplacer la définition de now de la ligne 296 à la ligne 158 (juste après le log du club)
# 2. Initialiser club_organization = None à la ligne 161
# 3. Supprimer la définition dupliquée de now aux lignes 295-296

echo "=== Déploiement de la correction pour club_dashboard ==="
echo ""

# Définir les variables
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichier à déployer
FILE="apps/competitions/views/dashboard/club.py"

echo "Fichier à déployer: $FILE"
echo ""

# Vérifier que le fichier local existe
if [ ! -f "$FILE" ]; then
    echo "ERREUR: Le fichier $FILE n'existe pas localement"
    exit 1
fi

# Copier le fichier
echo -n "Copie de $FILE vers la production... "
scp "$FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/$FILE"
if [ $? -eq 0 ]; then
    echo "OK"
else
    echo "ERREUR lors de la copie"
    exit 1
fi

echo ""
echo "Redémarrage de Gunicorn..."
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_PATH && sudo systemctl reload gunicorn"
if [ $? -eq 0 ]; then
    echo "Gunicorn redémarré avec succès"
else
    echo "ATTENTION: Erreur lors du redémarrage de Gunicorn"
    echo "Vous devrez peut-être redémarrer manuellement"
fi

echo ""
echo "=== Déploiement terminé! ==="
echo ""
echo "Vérifiez que la page https://martialcomp.com/fr/competitions/dashboard/club/ fonctionne maintenant"
echo ""
echo "Corrections appliquées :"
echo "  ✓ now défini à la ligne 158 (après le log du club)"
echo "  ✓ club_organization initialisé à None à la ligne 161"
echo "  ✓ Suppression de la définition dupliquée de now"
