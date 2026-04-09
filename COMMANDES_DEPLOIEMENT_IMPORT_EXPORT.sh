#!/bin/bash
# Commandes rapides pour déployer l'import/export en production
# Usage: ./COMMANDES_DEPLOIEMENT_IMPORT_EXPORT.sh

echo "=== Commandes de déploiement Import/Export ==="
echo ""

# Configuration
REMOTE_USER="pierrep99"
REMOTE_HOST="martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "1. Déploiement automatique (recommandé):"
echo "   ./DEPLOY_IMPORT_EXPORT_PRODUCTION.sh"
echo ""

echo "2. Déploiement manuel - Copie des fichiers:"
echo "   scp apps/competitions/views/club/import_export.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/views/club/"
echo "   scp apps/competitions/templates/competitions/club/import_export.html ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/apps/competitions/templates/competitions/club/"
echo "   scp config/settings/production.py ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/config/settings/"
echo ""

echo "3. Redémarrer le serveur (sur le serveur de production):"
echo "   sudo systemctl restart gunicorn"
echo "   # OU"
echo "   touch ${REMOTE_PATH}/config/wsgi.py"
echo ""

echo "4. Vérifier les logs:"
echo "   ssh ${REMOTE_USER}@${REMOTE_HOST} 'tail -f /var/log/django/martialcomp.log'"
echo ""

echo "5. Tester l'import:"
echo "   https://martialcomp.com/fr/competitions/club/import-export/#import-section"
echo ""
