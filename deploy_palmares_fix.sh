#!/bin/bash
# Script de deploiement pour la correction du palmares
# Le palmares prend maintenant en compte les resultats de CompetitionRanking

echo "=== Deploiement Correction Palmares ==="
echo ""

# Configuration
SSH_ALIAS="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichier a deployer
FILE="apps/competitions/services/palmares_service.py"

echo "Fichier a deployer: $FILE"
echo ""

# Verifier que le fichier local existe
if [ ! -f "$FILE" ]; then
    echo "ERREUR: Le fichier $FILE n'existe pas localement"
    exit 1
fi
echo "OK $FILE existe localement"
echo ""

# Copier le fichier vers la production
echo "Copie du fichier vers la production..."
scp "$FILE" "$SSH_ALIAS:$REMOTE_PATH/$FILE"
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible de copier $FILE"
    exit 1
fi
echo "OK $FILE copie"
echo ""

# Redemarrer Gunicorn
echo "Redemarrage de Gunicorn..."
ssh "$SSH_ALIAS" "pkill -HUP gunicorn || sudo systemctl reload gunicorn 2>/dev/null || touch $REMOTE_PATH/config/wsgi.py"
echo "OK Gunicorn redemarre"
echo ""

echo "=== Deploiement termine ==="
echo ""
echo "Correction appliquee :"
echo "  OK PalmaresService cherche maintenant dans CompetitionRanking"
echo "  OK get_statistics() compte les medailles depuis technical_scoring"
echo "  OK get_recent_results() inclut les resultats techniques"
echo ""
echo "Testez le palmares :"
echo "  1. Allez sur la fiche d'un pratiquant ayant participe"
echo "  2. Cliquez sur l'onglet 'Palmares'"
echo "  3. Les medailles et participations doivent maintenant s'afficher"
echo ""
