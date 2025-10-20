#!/bin/bash
# Script de déploiement du fix practitioner sur production

echo "🚀 DÉPLOIEMENT DU FIX PRACTITIONER"
echo "==================================="

# Variables
PROD_HOST="root@vigilant-swartz"
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOCAL_PACKAGE="production_fix_final.tar.gz"

# 1. Transférer le package
echo "1. Transfert du package..."
scp $LOCAL_PACKAGE $PROD_HOST:$PROD_DIR/

# 2. Exécuter les commandes sur production
echo "2. Application du fix sur production..."
ssh $PROD_HOST << 'ENDSSH'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "📦 Backup actuel..."
tar czf backup_$(date +%Y%m%d_%H%M%S).tar.gz apps/competitions/admin* apps/competitions/models/practitioner*

echo "🗑️  Suppression de TOUS les fichiers practitioner..."
find apps/competitions -name "*practitioner*" -type f | while read f; do
  echo "  Suppression: $f"
  rm -f "$f"
done

echo "📂 Extraction du nouveau package..."
tar xzf production_fix_final.tar.gz

echo "🧹 Nettoyage du cache..."
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "🔄 Redémarrage Apache..."
systemctl restart apache2

echo "✅ Fix appliqué !"
echo ""
echo "📊 Vérification finale:"
echo "Fichiers practitioner restants:"
find apps/competitions -name "*practitioner*" -type f 2>/dev/null | head -5 || echo "  ✅ Aucun fichier practitioner trouvé dans apps/competitions"

ENDSSH

echo ""
echo "✅ DÉPLOIEMENT TERMINÉ"
echo "🌐 Testez: https://martialcomp.com/fr/admin/competitions/practitioner/"
