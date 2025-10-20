#!/bin/bash

echo "🚀 Création du package de correction FINAL pour la création de fédération"
echo "========================================================================"

# Créer le répertoire du package
PACKAGE_DIR="federation_final_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$PACKAGE_DIR"

echo "📁 Création du répertoire: $PACKAGE_DIR"

# Copier les fichiers corrigés
echo "📋 Copie des fichiers corrigés..."

# Formulaire corrigé
cp apps/competitions/forms/onboarding.py "$PACKAGE_DIR/"

# Vue corrigée
cp apps/competitions/views/onboarding/federations.py "$PACKAGE_DIR/"

# Vue dashboard corrigée
cp apps/competitions/views/dashboard/federations.py "$PACKAGE_DIR/"

# Créer le script de déploiement
cat > "$PACKAGE_DIR/deploy_final_fix.sh" << 'EOF'
#!/bin/bash

echo "🔧 Déploiement de la correction FINALE de création de fédération"
echo "==============================================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "apps/competitions/forms/onboarding.py" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Créer une sauvegarde
echo "💾 Création de la sauvegarde..."
BACKUP_DIR="backups_federation_final_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

cp apps/competitions/forms/onboarding.py "$BACKUP_DIR/"
cp apps/competitions/views/onboarding/federations.py "$BACKUP_DIR/"
cp apps/competitions/views/dashboard/federations.py "$BACKUP_DIR/"

echo "✅ Sauvegarde créée dans: $BACKUP_DIR"

# Appliquer les corrections
echo "🔧 Application des corrections..."

# Remplacer le formulaire
cp onboarding.py apps/competitions/forms/onboarding.py

# Remplacer la vue onboarding
cp federations.py apps/competitions/views/onboarding/federations.py

# Remplacer la vue dashboard
cp federations.py apps/competitions/views/dashboard/federations.py

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
echo "1. ✅ Protection contre la double exécution"
echo "2. ✅ Nettoyage des messages en double"
echo "3. ✅ Redirection vers federation_detail avec ID spécifique"
echo "4. ✅ Création automatique du profil utilisateur"
echo "5. ✅ Amélioration de la gestion d'erreur"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://votre-domaine.com/fr/competitions/onboarding/federation/"
echo ""
echo "↩️ Pour restaurer:"
echo "cp $BACKUP_DIR/* [chemins originaux]"
EOF

chmod +x "$PACKAGE_DIR/deploy_final_fix.sh"

# Créer le script de transfert
cat > "deploy_final_federation_fix.sh" << EOF
#!/bin/bash

echo "🚀 Déploiement automatique de la correction FINALE de création de fédération"
echo "=========================================================================="

PACKAGE_DIR="$PACKAGE_DIR"
SERVER="martialcomp-production"

echo "📤 Transfert du package vers le serveur..."
scp -r "$PACKAGE_DIR" "$SERVER:/tmp/"

echo "🔧 Application de la correction sur le serveur..."
ssh "$SERVER" "cd /home/martialcomp/martialcomp && bash /tmp/$PACKAGE_DIR/deploy_final_fix.sh"

echo "✅ Déploiement terminé !"
echo ""
echo "🧪 Testez maintenant la création de fédération:"
echo "https://directive/fr/competitions/onboarding/federation/"
EOF

chmod +x "deploy_final_federation_fix.sh"

# Créer l'archive
echo "📦 Création de l'archive..."
tar -czf "${PACKAGE_DIR}.tar.gz" "$PACKAGE_DIR"

echo "✅ Package créé: ${PACKAGE_DIR}.tar.gz"
echo "✅ Script de déploiement créé: deploy_final_federation_fix.sh"
echo ""
echo "🚀 Pour déployer:"
echo "./deploy_final_federation_fix.sh"
echo ""
echo "📁 Contenu du package:"
ls -la "$PACKAGE_DIR"