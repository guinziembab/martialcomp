#!/bin/bash

# Script pour transférer et exécuter la correction de la table documents
echo "🚀 Déploiement du script de correction documents..."

SERVER="root@martialcomp.com"
REMOTE_PATH="/var/www/vhosts/martialcomp.com/httpdocs"

echo "📁 Transfert des fichiers de correction..."

# Transférer les scripts de correction
scp fix_documents_table.py $SERVER:$REMOTE_PATH/
scp fix_documents_simple.py $SERVER:$REMOTE_PATH/

echo "✅ Fichiers transférés"

echo "🔧 Exécution de la correction sur le serveur..."

# Exécuter la correction via SSH
ssh $SERVER << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

echo "🎯 Méthode 1: Script autonome"
python fix_documents_table.py

echo ""
echo "🎯 Méthode 2: Via shell Django (backup)"
python manage.py shell < fix_documents_simple.py

echo ""
echo "✅ Correction terminée!"
EOF

echo "🎉 Script de correction déployé et exécuté!"