#!/bin/bash
# Script d'installation des traductions en production
# Date: $(date +%Y-%m-%d)

set -e

echo "🌍 Installation des traductions MartialComp en production"
echo "=========================================================="

# Variables
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="$PROD_DIR/locale_backup_$(date +%Y%m%d_%H%M%S)"

# Vérifier qu'on est sur le serveur de production
if [ ! -d "$PROD_DIR" ]; then
    echo "❌ Erreur: Répertoire de production non trouvé"
    echo "   Ce script doit être exécuté sur le serveur de production"
    exit 1
fi

# Backup des traductions actuelles
echo "📦 Sauvegarde des traductions actuelles..."
mkdir -p "$BACKUP_DIR"
cp -r "$PROD_DIR/locale" "$BACKUP_DIR/" 2>/dev/null || echo "   Pas de traductions existantes"

# Copier les nouvelles traductions
echo "📥 Installation des nouvelles traductions..."
for lang in fr en es it de ja zh ar sw pt; do
    echo "   - $lang"
    mkdir -p "$PROD_DIR/locale/$lang/LC_MESSAGES"
    cp -f locale/$lang/LC_MESSAGES/django.po "$PROD_DIR/locale/$lang/LC_MESSAGES/"
    cp -f locale/$lang/LC_MESSAGES/django.mo "$PROD_DIR/locale/$lang/LC_MESSAGES/"
done

# Permissions
echo "🔒 Application des permissions..."
cd "$PROD_DIR"
chown -R martialco:psacln locale/
find locale/ -type f -exec chmod 644 {} \;
find locale/ -type d -exec chmod 755 {} \;

# Redémarrer le service
echo "🔄 Redémarrage du service..."
systemctl restart martialcomp.service

# Vérification
echo ""
echo "✅ Installation terminée avec succès!"
echo ""
echo "📊 Statistiques des traductions:"
for lang in fr en es it de ja zh ar sw pt; do
    count=$(msgfmt --statistics "$PROD_DIR/locale/$lang/LC_MESSAGES/django.po" 2>&1 | grep -oP '\d+(?= translated)')
    echo "   $lang: $count messages traduits"
done

echo ""
echo "💾 Backup sauvegardé dans: $BACKUP_DIR"
echo "🌐 Les traductions sont maintenant actives sur https://martialcomp.com"
