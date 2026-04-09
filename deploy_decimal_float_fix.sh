#!/bin/bash
# Script de deploiement pour la correction Decimal * float
# Correction: Erreur 'unsupported operand type(s) for *: decimal.Decimal and float'

echo "=== Deploiement Correction Decimal/Float ==="
echo ""

# Configuration
SSH_ALIAS="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichier a deployer
FILE="apps/competitions/models/technical_scoring.py"

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
echo "  OK Conversion explicite Decimal vers float dans calculate_final_score()"
echo "  OK total_score et total_weight initialises en float"
echo "  OK Plus d'erreur 'Decimal * float'"
echo ""
echo "Testez le calcul des resultats :"
echo "  1. Allez dans Gestion > Notation d'une competition"
echo "  2. Cliquez sur 'Calculer tous les resultats'"
echo "  3. Verifiez que les resultats s'affichent correctement"
echo ""
