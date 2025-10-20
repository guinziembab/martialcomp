#!/bin/bash

echo "🚀 Préparation du package de production pour Federation Dashboard"
echo "==========================================================="

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="federation_production_package_${TIMESTAMP}"
PACKAGE_DIR="/mnt/c/martial_hub_django/martialcomp/${PACKAGE_NAME}"

# Créer la structure du package
echo "📦 Création du package: ${PACKAGE_NAME}"
mkdir -p "${PACKAGE_DIR}"/{views,urls,templates,models,scripts}

# Copier les fichiers corrigés
echo ""
echo "📋 Collecte des fichiers..."

# Views
cp apps/competitions/views/onboarding/federations.py "${PACKAGE_DIR}/views/onboarding_federations.py"
cp apps/competitions/views/onboarding/__init__.py "${PACKAGE_DIR}/views/onboarding_init.py"
cp apps/competitions/views/dashboard/federations.py "${PACKAGE_DIR}/views/dashboard_federations.py"
echo "✅ Views copiées"

# URLs
cp apps/competitions/urls/dashboard.py "${PACKAGE_DIR}/urls/dashboard.py"
echo "✅ URLs copiées"

# Templates
cp apps/competitions/templates/competitions/dashboard/federation.html "${PACKAGE_DIR}/templates/federation.html"
cp apps/competitions/templates/competitions/dashboard/federation_*.html "${PACKAGE_DIR}/templates/" 2>/dev/null || echo "⚠️  Pas de templates secondaires"
echo "✅ Templates copiés"

# Patch et models
cp apps/competitions/models/notification_patch.py "${PACKAGE_DIR}/models/notification_patch.py" 2>/dev/null || echo "⚠️  Patch notification non trouvé"
cp apps/competitions/models/__init__.py "${PACKAGE_DIR}/models/models_init.py"
echo "✅ Models copiés"

# Créer le script de déploiement
cat > "${PACKAGE_DIR}/deploy_production.sh" << 'EOF'
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
EOF

chmod +x "${PACKAGE_DIR}/deploy_production.sh"

# Créer un README
cat > "${PACKAGE_DIR}/README.md" << 'EOF'
# Package de Production - Federation Dashboard

## Contenu

### Views
- `onboarding_federations.py` : Correction create_federation_user
- `dashboard_federations.py` : Dashboard complet avec toutes corrections
- `onboarding_init.py` : Exports des fonctions

### URLs
- `dashboard.py` : Routes complètes pour federation

### Templates
- `federation.html` : Template principal corrigé
- `federation_*.html` : Templates secondaires

### Models
- `notification_patch.py` : Patch pour Notification.federation
- `models_init.py` : Init avec import du patch

## Déploiement

1. Transférer ce dossier sur le serveur de production
2. Se placer dans la racine du projet Django
3. Exécuter: `bash federation_production_package_*/deploy_production.sh`

## Corrections Appliquées

1. ✅ ImportError 'create_federation_user'
2. ✅ TypeError federation_id
3. ✅ FieldError 'club'
4. ✅ FieldError 'organizing_federation'
5. ✅ FieldError 'federation' (Notification)
6. ✅ TemplateDoesNotExist
7. ✅ NoReverseMatch namespace

## Tests Post-Déploiement

- Accéder à `/fr/competitions/dashboard/federations/`
- Vérifier l'affichage des statistiques
- Tester les liens de navigation
- Vérifier qu'il n'y a pas d'erreur 500

## Rollback

Si problème, les sauvegardes sont créées automatiquement dans `backups_federation_*`
EOF

# Créer l'archive
cd /mnt/c/martial_hub_django/martialcomp
tar -czf "${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"

echo ""
echo "✅ Package créé: ${PACKAGE_NAME}.tar.gz"
echo ""
echo "📋 Instructions de transfert:"
echo "1. Copier le fichier sur le serveur de production:"
echo "   scp ${PACKAGE_NAME}.tar.gz user@serveur:/chemin/destination/"
echo ""
echo "2. Sur le serveur de production:"
echo "   tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "   cd ${PACKAGE_NAME}"
echo "   bash deploy_production.sh"
echo ""
echo "📊 Résumé du package:"
find "${PACKAGE_DIR}" -type f | wc -l | xargs echo "- Nombre de fichiers:"
du -sh "${PACKAGE_NAME}.tar.gz" | cut -f1 | xargs echo "- Taille du package:"