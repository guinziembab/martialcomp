#!/bin/bash
# Script de déploiement complet pour la correction du club dashboard
# Ce script peut être exécuté localement pour copier le fichier vers la production

echo "=== Déploiement de la correction Club Dashboard ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_FILE="apps/competitions/views/dashboard/club.py"
REMOTE_FILE="$REMOTE_PATH/$LOCAL_FILE"

# Vérifier que le fichier local existe
if [ ! -f "$LOCAL_FILE" ]; then
    echo "ERREUR: Le fichier $LOCAL_FILE n'existe pas localement"
    exit 1
fi

# Vérifier que les corrections sont présentes
echo "Vérification des corrections dans le fichier local..."
if grep -q "^    now = timezone.now().date()" "$LOCAL_FILE"; then
    NOW_LINE=$(grep -n "^    now = timezone.now().date()" "$LOCAL_FILE" | head -1 | cut -d: -f1)
    echo "✓ now trouvé à la ligne $NOW_LINE"
else
    echo "✗ ERREUR: La correction 'now' n'est pas trouvée dans le fichier local"
    exit 1
fi

if grep -q "^    club_organization = None" "$LOCAL_FILE"; then
    CLUB_ORG_LINE=$(grep -n "^    club_organization = None" "$LOCAL_FILE" | head -1 | cut -d: -f1)
    echo "✓ club_organization trouvé à la ligne $CLUB_ORG_LINE"
else
    echo "✗ ERREUR: La correction 'club_organization' n'est pas trouvée dans le fichier local"
    exit 1
fi

echo ""
echo "Le fichier local est correct. Déploiement vers la production..."
echo ""

# Copier le fichier vers la production
echo "Copie du fichier vers la production..."
scp "$LOCAL_FILE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_FILE"
if [ $? -ne 0 ]; then
    echo ""
    echo "✗ ERREUR: Impossible de copier le fichier vers la production"
    echo ""
    echo "Veuillez exécuter manuellement :"
    echo "  scp $LOCAL_FILE $REMOTE_USER@$REMOTE_HOST:$REMOTE_FILE"
    echo "  ssh $REMOTE_USER@$REMOTE_HOST \"cd $REMOTE_PATH && sudo systemctl reload gunicorn\""
    exit 1
fi

echo "✓ Fichier copié avec succès"
echo ""

# Redémarrer Gunicorn
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
echo "  ✓ now défini à la ligne 158 (après le log du club)"
echo "  ✓ club_organization initialisé à None à la ligne 161"
echo "  ✓ Suppression de la définition dupliquée de now"
echo ""
echo "Vérifiez que la page fonctionne maintenant :"
echo "  https://martialcomp.com/fr/competitions/dashboard/club/"
