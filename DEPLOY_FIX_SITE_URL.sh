#!/bin/bash
# Déploiement fix URL bouton "Voir le site"
# Le SubdomainGenerator utilisait BASE_URL (localhost) au lieu de SITE_URL (production)

set -e

echo "=== Déploiement fix URL site organization ==="

# Configuration
PROD_SERVER="martialcomp@martialcomp.com"
PROD_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Fichier à déployer
FILE="apps/competitions/utils/subdomain_generator.py"

echo "1. Copie du fichier corrigé..."
scp -o StrictHostKeyChecking=no "$FILE" "$PROD_SERVER:$PROD_PATH/$FILE"

echo "2. Redémarrage de Gunicorn..."
ssh -o StrictHostKeyChecking=no "$PROD_SERVER" "sudo systemctl restart gunicorn || sudo /usr/local/bin/restart_gunicorn.sh || (cd $PROD_PATH && source venv/bin/activate && pkill -f gunicorn; sleep 2; gunicorn config.wsgi:application -b 127.0.0.1:8888 -w 4 --daemon)"

echo "3. Vider le cache Redis..."
ssh -o StrictHostKeyChecking=no "$PROD_SERVER" "redis-cli FLUSHALL 2>/dev/null || echo 'Cache non vidé (Redis non accessible)'"

echo ""
echo "=== Déploiement terminé ==="
echo "Le bouton 'Voir le site' devrait maintenant afficher l'URL correcte:"
echo "https://martialcomp.com/org/khiphap"
echo ""
echo "Testez sur: https://martialcomp.com/fr/org/khiphap/admin/site/"
