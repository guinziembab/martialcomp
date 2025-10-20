#!/bin/bash

echo "🔧 Déploiement de la correction du RÔLE pour la création de fédération"
echo "====================================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "apps/competitions/views/onboarding/federations.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Créer une sauvegarde
echo "💾 Création de la sauvegarde..."
BACKUP_DIR="backups_federation_role_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp apps/competitions/views/onboarding/federations.py "$BACKUP_DIR/"

echo "✅ Sauvegarde créée dans: $BACKUP_DIR"

# Appliquer les corrections
echo "🔧 Application des corrections..."

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
echo "1. ✅ Correction de la vérification du rôle (plus flexible)"
echo "2. ✅ Création automatique du profil UserProfile (pas Practitioner)"
echo "3. ✅ Mise à jour du rôle vers federation_admin après création"
echo "4. ✅ Protection contre les redirections en boucle"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://votre-domaine.com/fr/competitions/onboarding/federation/"
echo ""
echo "↩️ Pour restaurer:"
echo "cp $BACKUP_DIR/* [chemins originaux]"
