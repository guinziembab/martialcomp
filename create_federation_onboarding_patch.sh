#!/bin/bash

echo "🔧 Création du patch de production pour l'onboarding Federation"
echo "=============================================================="

# Créer un dossier temporaire
PATCH_DIR="federation_onboarding_patch_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$PATCH_DIR"

# Copier le template corrigé
cp apps/competitions/templates/competitions/onboarding/final_setup.html "$PATCH_DIR/final_setup.html"

# Créer le script de déploiement
cat > "$PATCH_DIR/apply_patch.sh" << 'EOF'
#!/bin/bash

echo "🚀 Application du patch onboarding Federation"
echo "==========================================="

# Vérifier qu'on est dans le bon dossier
if [ ! -d "apps/competitions/templates" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Sauvegarder l'ancien fichier
BACKUP_FILE="apps/competitions/templates/competitions/onboarding/final_setup.html.backup_$(date +%Y%m%d_%H%M%S)"
cp apps/competitions/templates/competitions/onboarding/final_setup.html "$BACKUP_FILE"
echo "✅ Sauvegarde créée: $BACKUP_FILE"

# Copier le nouveau fichier
cp final_setup.html apps/competitions/templates/competitions/onboarding/final_setup.html
echo "✅ Template corrigé déployé"

echo ""
echo "✅ Patch appliqué avec succès!"
echo ""
echo "Le problème suivant a été corrigé:"
echo "- URLs 'competitions:federations:' remplacées par 'competitions:dashboard:'"
echo ""
echo "↩️  Pour restaurer:"
echo "   cp $BACKUP_FILE apps/competitions/templates/competitions/onboarding/final_setup.html"
EOF

chmod +x "$PATCH_DIR/apply_patch.sh"

# Créer l'archive
tar -czf "$PATCH_DIR.tar.gz" "$PATCH_DIR"

echo ""
echo "✅ Patch créé: $PATCH_DIR.tar.gz"
echo ""
echo "📋 Instructions:"
echo "1. Transférer sur le serveur:"
echo "   scp $PATCH_DIR.tar.gz martialcomp-production:/tmp/"
echo ""
echo "2. Sur le serveur:"
echo "   cd /tmp"
echo "   tar -xzf $PATCH_DIR.tar.gz"
echo "   cd /chemin/vers/martialcomp"
echo "   bash /tmp/$PATCH_DIR/apply_patch.sh"
echo ""
echo "3. Pas besoin de redémarrer (c'est juste un template)"

# Nettoyer
rm -rf "$PATCH_DIR"