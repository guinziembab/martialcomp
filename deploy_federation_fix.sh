#!/bin/bash

# Script de déploiement des correctifs de création de fédération
# Date: 2025-01-16
# Version: 1.0

set -e  # Arrêter en cas d'erreur

echo "🚀 DÉPLOIEMENT DES CORRECTIFS FÉDÉRATION - $(date)"
echo "=================================================="

# Variables
BACKUP_DIR="/tmp/federation_backup_$(date +%Y%m%d_%H%M%S)"
TEMPLATE_DIR="/var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/onboarding"
SCRIPT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

echo "📁 Création du répertoire de sauvegarde: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo "💾 Sauvegarde des fichiers existants..."
cp "$TEMPLATE_DIR/federation_creation.html" "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  Fichier original non trouvé (normal pour première installation)"

echo "📋 Déploiement du nouveau template..."
cp "federation_creation_fixed_20251016_161850.html" "$TEMPLATE_DIR/federation_creation.html"
chmod 644 "$TEMPLATE_DIR/federation_creation.html"
chown www-data:www-data "$TEMPLATE_DIR/federation_creation.html"

echo "🧹 Nettoyage du cache Python..."
find "$SCRIPT_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$SCRIPT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "🔄 Redémarrage d'Apache..."
systemctl restart apache2

echo "✅ Vérification du déploiement..."
if [ -f "$TEMPLATE_DIR/federation_creation.html" ]; then
    echo "✅ Template déployé avec succès"
    
    # Vérifier que le script places.js n'est pas présent
    if ! grep -q "places.js" "$TEMPLATE_DIR/federation_creation.html"; then
        echo "✅ Script places.js supprimé avec succès"
    else
        echo "⚠️  ATTENTION: Script places.js encore présent!"
    fi
    
    # Vérifier la présence des meta tags de cache-busting
    if grep -q "Cache-Control.*no-cache" "$TEMPLATE_DIR/federation_creation.html"; then
        echo "✅ Meta tags de cache-busting présents"
    else
        echo "⚠️  ATTENTION: Meta tags de cache-busting manquants!"
    fi
else
    echo "❌ ERREUR: Template non déployé!"
    exit 1
fi

echo ""
echo "🎯 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "=================================="
echo "📋 Prochaines étapes:"
echo "1. Demander à l'utilisateur de vider complètement le cache navigateur (Ctrl+Shift+R)"
echo "2. Tester en navigation privée"
echo "3. Vérifier la console développeur pour les erreurs JavaScript"
echo "4. Si le problème persiste, exécuter le script de création manuelle"
echo ""
echo "📁 Sauvegarde disponible dans: $BACKUP_DIR"
echo "🕐 Déploiement terminé à: $(date)"