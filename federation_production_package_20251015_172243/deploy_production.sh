#!/bin/bash

echo "🚀 Déploiement des corrections Federation Dashboard"
echo "================================================="

# Vérifier qu'on est sur le serveur de production
if [ ! -d "apps/competitions" ]; then
    echo "❌ Erreur: Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Créer des sauvegardes
BACKUP_DIR="backups_federation_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📁 Création des sauvegardes dans $BACKUP_DIR..."

# Sauvegarder les fichiers existants
FILES_TO_BACKUP=(
    "apps/competitions/views/onboarding/federations.py"
    "apps/competitions/views/onboarding/__init__.py"
    "apps/competitions/views/dashboard/federations.py"
    "apps/competitions/urls/dashboard.py"
    "apps/competitions/templates/competitions/dashboard/federation.html"
    "apps/competitions/models/__init__.py"
)

for file in "${FILES_TO_BACKUP[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        echo "  ✅ Sauvegardé: $(basename $file)"
    fi
done

echo ""
echo "📝 Déploiement des fichiers..."

# Déployer les views
cp views/onboarding_federations.py apps/competitions/views/onboarding/federations.py
cp views/onboarding_init.py apps/competitions/views/onboarding/__init__.py
cp views/dashboard_federations.py apps/competitions/views/dashboard/federations.py
echo "✅ Views déployées"

# Déployer les URLs
cp urls/dashboard.py apps/competitions/urls/dashboard.py
echo "✅ URLs déployées"

# Déployer les templates
cp templates/federation.html apps/competitions/templates/competitions/dashboard/federation.html
cp templates/federation_*.html apps/competitions/templates/competitions/dashboard/ 2>/dev/null
echo "✅ Templates déployés"

# Déployer le patch si présent
if [ -f "models/notification_patch.py" ]; then
    cp models/notification_patch.py apps/competitions/models/notification_patch.py
    echo "✅ Patch notification déployé"
fi

# Déployer models init
cp models/models_init.py apps/competitions/models/__init__.py
echo "✅ Models init déployé"

echo ""
echo "🔧 Post-déploiement..."

# Collecter les fichiers statiques si nécessaire
if [ -f "manage.py" ]; then
    python manage.py collectstatic --noinput 2>/dev/null || true
fi

echo ""
echo "✅ Déploiement terminé!"
echo ""
echo "⚠️  ACTIONS REQUISES:"
echo "1. Redémarrer le serveur web (Apache/Gunicorn)"
echo "2. Vider le cache si nécessaire"
echo "3. Tester le dashboard federation"
echo ""
echo "📁 Les sauvegardes sont dans: $BACKUP_DIR/"
echo ""
echo "↩️  Pour restaurer:"
echo "   cp $BACKUP_DIR/* [chemins originaux]"
