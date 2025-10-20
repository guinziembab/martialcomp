#!/bin/bash

echo "🚀 Déploiement COMPLET des corrections Federation"
echo "================================================="
echo ""
echo "Ce script déploie toutes les corrections pour résoudre les erreurs du dashboard Federation."
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "deploy_complete.sh" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis le dossier federation_fixes_backup_*"
    exit 1
fi

echo "📦 Fichiers à déployer:"
echo "1. federations.py → views/onboarding/federations.py"
echo "2. __init__.py → views/onboarding/__init__.py"
echo "3. federations_dashboard_final.py → views/dashboard/federations.py"
echo "4. notification_patch.py → models/notification_patch.py"
echo "5. models_init.py → models/__init__.py"
echo ""

read -p "Voulez-vous continuer? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Déploiement annulé"
    exit 1
fi

# Créer des sauvegardes
echo ""
echo "📁 Création des sauvegardes..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Fonction pour sauvegarder et copier
backup_and_copy() {
    local source=$1
    local dest=$2
    local desc=$3
    
    if [ -f "$dest" ]; then
        cp "$dest" "${dest}.backup_${TIMESTAMP}"
        echo "   ✅ Sauvegarde: ${dest}.backup_${TIMESTAMP}"
    fi
    
    cp "$source" "$dest"
    echo "   ✅ Déployé: $desc"
}

# Déployer les fichiers
echo ""
echo "📝 Déploiement des fichiers..."

# Assurez-vous d'adapter ces chemins selon votre structure
backup_and_copy "federations.py" "apps/competitions/views/onboarding/federations.py" "Onboarding federations"
backup_and_copy "__init__.py" "apps/competitions/views/onboarding/__init__.py" "Onboarding init"
backup_and_copy "federations_dashboard_final.py" "apps/competitions/views/dashboard/federations.py" "Dashboard federations"
backup_and_copy "notification_patch.py" "apps/competitions/models/notification_patch.py" "Patch Notification"
backup_and_copy "models_init.py" "apps/competitions/models/__init__.py" "Models init avec patch"

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "📋 Corrections appliquées:"
echo "1. ImportError 'create_federation_user' → RÉSOLU"
echo "2. TypeError federation_dashboard → RÉSOLU"
echo "3. FieldError 'club' → RÉSOLU"
echo "4. FieldError 'organizing_federation' → RÉSOLU"
echo "5. FieldError 'federation' dans Notification → RÉSOLU (avec patch)"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Redémarrer le serveur web"
echo "2. Vider le cache si nécessaire"
echo "3. Tester le dashboard federation"
echo ""
echo "💡 Notes:"
echo "- Task Management est temporairement désactivé"
echo "- Le patch Notification est une solution temporaire"
echo "- Pour une solution permanente, modifier le code qui filtre par federation"