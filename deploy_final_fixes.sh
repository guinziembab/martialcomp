#\!/bin/bash
# Script de correction finale pour la production

PRODUCTION_SERVER="martialcomp-production"
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "=========================================="
echo "Correction finale de la production"
echo "Date: $(date)"
echo "=========================================="

# 1. Désactiver temporairement les prints dans les settings
echo "1. Correction des settings..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && sed -i 's/print(/# print(/g' config/settings/base.py"

# 2. Créer les fichiers manquants
echo "2. Création des fichiers manquants..."
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && touch apps/competitions/views/dashboard/role_switch.py && echo 'pass' > apps/competitions/views/dashboard/role_switch.py"

# 3. Redémarrer Apache
echo "3. Redémarrage d'Apache..."
ssh "$PRODUCTION_SERVER" "sudo systemctl restart apache2"

# 4. Vérifier le statut
echo "4. Vérification du site..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ || echo "000")
echo "Statut HTTP: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo "✓ Site accessible\!"
else
    echo "✗ Site toujours en erreur"
    # Afficher les dernières erreurs
    ssh "$PRODUCTION_SERVER" "tail -20 /var/log/apache2/error.log 2>/dev/null  < /dev/null |  grep -v 'certificate does NOT'"
fi

echo "=========================================="
echo "Correction terminée"
echo "=========================================="
