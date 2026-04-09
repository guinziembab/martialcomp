#!/bin/bash
# Script pour vérifier que Gunicorn fonctionne correctement en production

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "🔍 Vérification de Gunicorn en production..."
echo ""

# Option 1: Exécuter localement si on est sur le serveur de production
if [ -d "$PRODUCTION_PATH" ]; then
    echo "Exécution locale sur le serveur de production..."
    cd "$PRODUCTION_PATH"
    python3 scripts/verify_gunicorn_production.py
    exit $?
fi

# Option 2: Exécuter via SSH si on est sur une machine distante
if command -v ssh &> /dev/null; then
    echo "Exécution distante via SSH..."
    
    # Transférer le script si nécessaire
    scp scripts/verify_gunicorn_production.py "$PRODUCTION_SERVER:$PRODUCTION_PATH/scripts/"
    
    # Exécuter le script sur le serveur distant
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && python3 scripts/verify_gunicorn_production.py"
    exit $?
fi

echo "❌ Impossible de déterminer comment exécuter la vérification"
echo "   Assurez-vous d'être sur le serveur de production ou que SSH est configuré"
exit 1
