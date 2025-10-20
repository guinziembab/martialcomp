#!/bin/bash

echo "🚀 Déploiement des corrections Federation en production"
echo "======================================================"

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="federation_fixes_backup_${TIMESTAMP}"
FILES_TO_DEPLOY=(
    "apps/competitions/views/onboarding/federations.py"
    "apps/competitions/views/onboarding/__init__.py"
    "apps/competitions/views/dashboard/federations.py"
)

echo "📁 Création du dossier de sauvegarde: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

echo ""
echo "📦 Préparation des fichiers à déployer..."

for file in "${FILES_TO_DEPLOY[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        echo "✅ $file copié"
    else
        echo "❌ $file non trouvé!"
    fi
done

echo ""
echo "📋 Résumé des corrections appliquées:"
echo "1. ✅ Ajout de create_federation_user dans onboarding/federations.py"
echo "2. ✅ Correction des redirections (federations:federation_dashboard → competitions:dashboard:federations)"
echo "3. ✅ federation_id rendu optionnel dans federation_dashboard()"
echo "4. ✅ Auto-détection de la fédération de l'utilisateur"
echo "5. ✅ Ajout de _get_practitioners_count_for_federation() pour gérer Practitioner.organization"
echo "6. ✅ Gestion des relations Organization ↔ Club ↔ Federation"

echo ""
echo "📝 Instructions de déploiement:"
echo "1. Transférer le dossier $BACKUP_DIR vers le serveur de production"
echo "2. Sauvegarder les fichiers actuels sur le serveur"
echo "3. Copier les nouveaux fichiers:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "   cp $BACKUP_DIR/$(basename $file) /chemin/production/$file"
done
echo "4. Redémarrer le serveur: systemctl restart apache2 (ou équivalent)"
echo "5. Tester l'onboarding federation et le dashboard"

echo ""
echo "⚠️  IMPORTANT:"
echo "- Vérifier que les modèles Organization et Affiliation existent en production"
echo "- S'assurer que les migrations sont à jour"
echo "- Tester d'abord sur un environnement de staging si possible"

echo ""
echo "✅ Package de déploiement créé: $BACKUP_DIR/"
echo ""

# Créer aussi un script de déploiement automatique
cat > "$BACKUP_DIR/deploy.sh" << 'EOF'
#!/bin/bash
# Script de déploiement automatique

echo "🚀 Déploiement des corrections Federation..."

# Sauvegarder les fichiers actuels
for file in apps/competitions/views/onboarding/federations.py apps/competitions/views/onboarding/__init__.py apps/competitions/views/dashboard/federations.py; do
    if [ -f "$file" ]; then
        cp "$file" "${file}.backup_$(date +%Y%m%d_%H%M%S)"
        echo "Sauvegarde: $file"
    fi
done

# Copier les nouveaux fichiers
cp federations.py apps/competitions/views/onboarding/federations.py
cp __init__.py apps/competitions/views/onboarding/__init__.py
cp federations.py apps/competitions/views/dashboard/federations.py

echo "✅ Fichiers déployés"
echo "⚠️  N'oubliez pas de redémarrer le serveur!"
EOF

chmod +x "$BACKUP_DIR/deploy.sh"

echo "Script de déploiement automatique créé: $BACKUP_DIR/deploy.sh"