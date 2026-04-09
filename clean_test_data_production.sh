#!/bin/bash
# Script pour nettoyer les données de test d'une compétition en production
#
# Usage:
#   bash clean_test_data_production.sh

echo "=== Nettoyage des données de test en production ==="
echo ""

# Configuration
SSH_ALIAS="martialcomp-production"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
SCRIPT_FILE="scripts/clean_test_competition_data.py"

# Vérifier que le script local existe
if [ ! -f "$SCRIPT_FILE" ]; then
    echo "ERREUR: Le script $SCRIPT_FILE n'existe pas localement"
    exit 1
fi
echo "OK Script local trouvé: $SCRIPT_FILE"

echo ""
echo "PARAMETRES ACTUELS (dans $SCRIPT_FILE):"
grep -E "^COMPETITION_ID|^DRY_RUN" "$SCRIPT_FILE"
echo ""

# Créer le dossier scripts en production si nécessaire
echo "Création du dossier scripts en production..."
ssh "$SSH_ALIAS" "mkdir -p $REMOTE_PATH/scripts"

# Copier le script vers la production
echo "Copie du script vers la production..."
scp "$SCRIPT_FILE" "$SSH_ALIAS:$REMOTE_PATH/$SCRIPT_FILE"
if [ $? -ne 0 ]; then
    echo "ERREUR: Impossible de copier le script"
    exit 1
fi
echo "OK Script copié"

# Exécuter le script via manage.py shell
echo ""
echo "Exécution du script de nettoyage..."
echo ""
ssh "$SSH_ALIAS" "cd $REMOTE_PATH && python3 manage.py shell -c \"
import sys
sys.path.insert(0, '.')
exec(open('scripts/clean_test_competition_data.py').read())
\""

echo ""
echo "=== Terminé ==="
