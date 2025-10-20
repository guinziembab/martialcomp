#!/bin/bash

echo "🔧 Déploiement de la correction de création de fédération"
echo "========================================================"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "apps/competitions/forms/onboarding.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Créer une sauvegarde
echo "💾 Création de la sauvegarde..."
BACKUP_DIR="backups_federation_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp apps/competitions/forms/onboarding.py "$BACKUP_DIR/"
cp apps/competitions/views/onboarding/federations.py "$BACKUP_DIR/"

echo "✅ Sauvegarde créée dans: $BACKUP_DIR"

# Appliquer les corrections
echo "🔧 Application des corrections..."

# Remplacer le formulaire
cp onboarding.py apps/competitions/forms/onboarding.py

# Remplacer la vue
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
echo "1. ✅ Ajout des champs manquants dans Meta.fields du formulaire"
echo "2. ✅ Simplification de la validation du champ country"
echo "3. ✅ Correction de la méthode save() du formulaire"
echo "4. ✅ Amélioration de la gestion d'erreur dans la vue"
echo "5. ✅ Ajout de logs détaillés pour le débogage"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://votre-domaine.com/fr/competitions/onboarding/federation/"
echo ""
echo "↩️ Pour restaurer:"
echo "cp $BACKUP_DIR/* [chemins originaux]"
