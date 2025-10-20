#!/bin/bash
# Script de transfert des traductions vers la production
# Date: $(date +%Y-%m-%d)

set -e

PACKAGE_DIR="translations_production_20251007_181612"
PACKAGE_FILE="${PACKAGE_DIR}.tar.gz"
SERVER="root@vigilant-swartz"
REMOTE_TMP="/tmp"

echo "🌍 Transfert des traductions MartialComp vers la production"
echo "============================================================="
echo ""

# Vérifier que le package existe
if [ ! -f "$PACKAGE_FILE" ]; then
    echo "❌ Erreur: Package $PACKAGE_FILE non trouvé"
    exit 1
fi

echo "📦 Package: $PACKAGE_FILE ($(du -h $PACKAGE_FILE | cut -f1))"
echo ""

# Afficher les statistiques du package
echo "📊 Contenu du package:"
echo "   - 10 langues (fr, en, es, it, de, ja, zh, ar, sw, pt)"
echo "   - 13,454 messages traduits par langue"
echo "   - Total: 134,540+ messages"
echo ""

# Transférer le package
echo "📤 Transfert vers le serveur de production..."
scp "$PACKAGE_FILE" "$SERVER:$REMOTE_TMP/"

if [ $? -eq 0 ]; then
    echo "✅ Transfert réussi!"
else
    echo "❌ Erreur lors du transfert"
    exit 1
fi

echo ""
echo "📋 Prochaines étapes sur le serveur de production:"
echo ""
echo "   ssh $SERVER"
echo "   cd $REMOTE_TMP"
echo "   tar -xzf $PACKAGE_FILE"
echo "   cd $PACKAGE_DIR"
echo "   chmod +x INSTALL.sh"
echo "   ./INSTALL.sh"
echo ""
echo "🔍 Le script INSTALL.sh va:"
echo "   1. Sauvegarder les traductions actuelles"
echo "   2. Installer les nouvelles traductions"
echo "   3. Appliquer les permissions"
echo "   4. Redémarrer le service"
echo "   5. Afficher les statistiques"
echo ""
echo "✅ Package prêt à être déployé!"
