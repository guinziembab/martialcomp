#!/bin/bash

echo "🔧 Déploiement de la correction FINALE du routage fédération"
echo "==========================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "apps/competitions/views/dashboard/base.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Créer une sauvegarde
echo "💾 Création de la sauvegarde..."
BACKUP_DIR="backups_federation_routing_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp apps/competitions/views/dashboard/base.py "$BACKUP_DIR/"
cp apps/competitions/adapters.py "$BACKUP_DIR/"
cp apps/competitions/views/onboarding/federations.py "$BACKUP_DIR/"

echo "✅ Sauvegarde créée dans: $BACKUP_DIR"

# Appliquer les corrections
echo "🔧 Application des corrections..."

# Remplacer les fichiers
cp base.py apps/competitions/views/dashboard/base.py
cp adapters.py apps/competitions/adapters.py
cp federations.py apps/competitions/views/onboarding/federations.py

echo "✅ Corrections appliquées"

# Redémarrer le serveur web
echo "🔄 Redémarrage du serveur web..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart apache2
    echo "✅ Apache2 redémarré"
elif command -v service &> /dev/null; then
    sudo service apache2 restart
    echo "✅ Apache2 redémarré"
else
    echo "⚠️ Impossible de redémarrer Apache2 automatiquement"
    echo "Veuillez redémarrer manuellement le serveur web"
fi

echo ""
echo "✅ Déploiement terminé !"
echo ""
echo "📋 Résumé des corrections appliquées:"
echo "1. ✅ Correction du routage federation_admin vers competitions:dashboard:federations"
echo "2. ✅ Correction de l'adapter pour utiliser la bonne URL"
echo "3. ✅ Amélioration de la protection contre la double exécution"
echo "4. ✅ Redirection vers federation_detail avec ID spécifique"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://votre-domaine.com/fr/competitions/onboarding/federation/"
echo ""
echo "↩️ Pour restaurer:"
echo "cp $BACKUP_DIR/* [chemins originaux]"
