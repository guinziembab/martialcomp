#!/bin/bash

# Script pour transférer l'app core vers la production

echo "=== TRANSFERT DE L'APP CORE VERS LA PRODUCTION ==="
echo ""

# 1. Créer une archive de l'app core
echo "1. CRÉATION DE L'ARCHIVE DE L'APP CORE"
echo "======================================"

cd /mnt/c/martial_hub_django/martialcomp

# Créer l'archive
tar -czf core_app_transfer.tar.gz apps/core/

if [ -f "core_app_transfer.tar.gz" ]; then
    echo "✅ Archive créée: core_app_transfer.tar.gz"
    echo "   Taille: $(du -h core_app_transfer.tar.gz | cut -f1)"
else
    echo "❌ Erreur lors de la création de l'archive"
    exit 1
fi

echo ""

# 2. Afficher le contenu de l'archive
echo "2. CONTENU DE L'ARCHIVE"
echo "======================="

tar -tzf core_app_transfer.tar.gz

echo ""

# 3. Instructions de transfert
echo "3. TRANSFERT VERS LA PRODUCTION"
echo "==============================="

echo "Commandes à exécuter:"
echo ""
echo "# 1. Transférer l'archive"
echo "scp core_app_transfer.tar.gz martialcomp-production:/tmp/"
echo ""
echo "# 2. Sur le serveur de production"
echo "ssh martialcomp-production"
echo "cd /var/www/vhosts/martialcomp.com/httpdocs"
echo ""
echo "# 3. Sauvegarder l'existant (s'il existe)"
echo "if [ -d apps/core ]; then"
echo "    mv apps/core apps/core.backup.$(date +%Y%m%d_%H%M%S)"
echo "fi"
echo ""
echo "# 4. Extraire l'archive"
echo "tar -xzf /tmp/core_app_transfer.tar.gz"
echo ""
echo "# 5. Vérifier les permissions"
echo "chown -R www-data:www-data apps/core"
echo "chmod -R 755 apps/core"
echo ""
echo "# 6. Nettoyer"
echo "rm /tmp/core_app_transfer.tar.gz"

echo ""
echo "============================================"