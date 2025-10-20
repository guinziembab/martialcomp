#!/bin/bash
# Script de création du package de mise à jour pour la production
# Inclut l'onglet Résultats et les corrections d'URLs

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="update_resultats_${TIMESTAMP}"
PACKAGE_DIR="/tmp/${PACKAGE_NAME}"

echo "🚀 Création du package de mise à jour..."
echo "📦 Package : ${PACKAGE_NAME}"

# Créer la structure
mkdir -p ${PACKAGE_DIR}/{apps/competitions/{views,templates/competitions/club},docs}

# 1. Copier les fichiers modifiés
echo "📄 Copie des fichiers modifiés..."

# Template principal avec l'onglet Résultats
cp apps/competitions/templates/competitions/club/competition_management_detail.html ${PACKAGE_DIR}/apps/competitions/templates/competitions/club/

# Vue pour fournir les données nécessaires
cp apps/competitions/views/club/event_organizer.py ${PACKAGE_DIR}/apps/competitions/views/club/

# Vue pro (si elle existe)
if [ -f "apps/competitions/views/competition_management_pro.py" ]; then
    cp apps/competitions/views/competition_management_pro.py ${PACKAGE_DIR}/apps/competitions/views/
fi

# Documentation
cp RAPPORT_INTEGRATION_RESULTATS.md ${PACKAGE_DIR}/docs/
cp RAPPORT_CORRECTION_URLS_RESULTATS.md ${PACKAGE_DIR}/docs/
cp GUIDE_MISE_A_JOUR_PRODUCTION.md ${PACKAGE_DIR}/docs/

# 2. Créer le script de déploiement
cat > ${PACKAGE_DIR}/deploy_on_server.sh << 'DEPLOY_SCRIPT'
#!/bin/bash
# Script de déploiement sur le serveur de production

echo "🚀 Déploiement de l'onglet Résultats..."

# Configuration
WEBAPP_DIR="/home/martialcomp/public_html"
BACKUP_DIR="/home/martialcomp/backups/$(date +%Y%m%d_%H%M%S)"

# Créer le répertoire de sauvegarde
echo "💾 Création de la sauvegarde..."
mkdir -p $BACKUP_DIR

# Sauvegarder les fichiers existants
if [ -f "$WEBAPP_DIR/apps/competitions/templates/competitions/club/competition_management_detail.html" ]; then
    cp "$WEBAPP_DIR/apps/competitions/templates/competitions/club/competition_management_detail.html" \
       "$BACKUP_DIR/competition_management_detail.html.bak"
    echo "✓ Template sauvegardé"
fi

if [ -f "$WEBAPP_DIR/apps/competitions/views/club/event_organizer.py" ]; then
    cp "$WEBAPP_DIR/apps/competitions/views/club/event_organizer.py" \
       "$BACKUP_DIR/event_organizer.py.bak"
    echo "✓ Vue sauvegardée"
fi

# Copier les nouveaux fichiers
echo "📤 Installation des nouveaux fichiers..."
cp -r apps/* $WEBAPP_DIR/apps/
echo "✓ Fichiers copiés"

# Activer l'environnement virtuel
cd $WEBAPP_DIR
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    source ../venv/bin/activate
else
    echo "⚠️  Environnement virtuel non trouvé, continuons..."
fi

# Collecter les fichiers statiques
echo "🎨 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput --clear || true

# Redémarrer l'application
echo "🔄 Redémarrage de l'application..."
touch $WEBAPP_DIR/passenger_wsgi.py

echo "✅ Déploiement terminé!"
echo ""
echo "📝 Vérifications à faire :"
echo "1. Accéder à une compétition : /competitions/club/competitions/{id}/manage/"
echo "2. Vérifier que l'onglet 'Résultats' apparaît"
echo "3. Tester les liens vers le système de notation"
echo ""
echo "🔙 En cas de problème, restaurer depuis : $BACKUP_DIR"
DEPLOY_SCRIPT

chmod +x ${PACKAGE_DIR}/deploy_on_server.sh

# 3. Créer un fichier README
cat > ${PACKAGE_DIR}/README.md << 'README'
# Mise à jour : Onglet Résultats

## Contenu de la mise à jour

1. **Nouvel onglet Résultats** dans la gestion des compétitions avec :
   - Accès au dashboard des juges
   - Interface de configuration de la notation
   - Résultats par catégorie avec actions rapides
   - Graphique de l'état de notation
   - Tableau de suivi temps réel

2. **Corrections d'URLs** pour éviter les erreurs NoReverseMatch

3. **Intégration Chart.js** pour les graphiques (via CDN)

## Installation

1. Transférer le package sur le serveur :
   ```bash
   scp update_resultats_*.tar.gz user@serveur:/home/martialcomp/
   ```

2. Se connecter au serveur et extraire :
   ```bash
   ssh user@serveur
   cd /home/martialcomp
   tar -xzf update_resultats_*.tar.gz
   ```

3. Exécuter le script de déploiement :
   ```bash
   cd update_resultats_*
   ./deploy_on_server.sh
   ```

## Rollback

Si nécessaire, les fichiers originaux sont sauvegardés dans :
`/home/martialcomp/backups/[timestamp]/`
README

# 4. Créer l'archive
echo "📦 Création de l'archive..."
cd /tmp
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_NAME}

# Afficher les informations
echo ""
echo "✅ Package créé avec succès!"
echo "📦 Fichier : /tmp/${PACKAGE_NAME}.tar.gz"
echo "📏 Taille : $(du -h /tmp/${PACKAGE_NAME}.tar.gz | cut -f1)"
echo ""
echo "📋 Contenu du package :"
tar -tzf ${PACKAGE_NAME}.tar.gz | grep -E "\.(py|html|md)$" | head -20
echo ""
echo "🚀 Prochaine étape : transférer le package vers le serveur de production"
echo "   scp /tmp/${PACKAGE_NAME}.tar.gz user@production:/home/martialcomp/"