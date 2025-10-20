#!/bin/bash

# Script pour créer un package de production optimisé
# Ce script crée une archive contenant uniquement les fichiers essentiels

PACKAGE_NAME="martialcomp_production_$(date +%Y%m%d_%H%M%S).tar.gz"
TEMP_DIR="production_export_temp"

echo "📦 Création du package de production: $PACKAGE_NAME"

# Créer un dossier temporaire
mkdir -p $TEMP_DIR

echo "📋 Copie des fichiers essentiels..."

# Copier les fichiers de base
cp manage.py $TEMP_DIR/ 2>/dev/null
cp requirements.txt $TEMP_DIR/ 2>/dev/null
cp Pipfile* $TEMP_DIR/ 2>/dev/null

# Copier la configuration
cp -r config $TEMP_DIR/

# Copier les applications (en excluant __pycache__)
mkdir -p $TEMP_DIR/apps
rsync -av --exclude='__pycache__' --exclude='*.pyc' --exclude='*.log' apps/ $TEMP_DIR/apps/

# Copier les templates
cp -r templates $TEMP_DIR/

# Copier les fichiers statiques
cp -r static $TEMP_DIR/

# Copier les médias (optionnel - décommentez si nécessaire)
# cp -r media $TEMP_DIR/

# Copier les locales si présentes
if [ -d "locale" ]; then
    cp -r locale $TEMP_DIR/
fi

# Copier les fichiers d'environnement (attention aux secrets!)
if [ -f ".env.production" ]; then
    cp .env.production $TEMP_DIR/
fi

# Créer l'archive
echo "🗜️  Création de l'archive..."
tar -czf $PACKAGE_NAME -C $TEMP_DIR .

# Nettoyer le dossier temporaire
rm -rf $TEMP_DIR

# Afficher la taille finale
echo "✅ Package créé avec succès!"
echo "📊 Taille du package: $(ls -lh $PACKAGE_NAME | awk '{print $5}')"
echo "📍 Fichier: $PACKAGE_NAME"
echo ""
echo "🚀 Pour déployer:"
echo "1. Transférer le fichier sur le serveur de production"
echo "2. Extraire: tar -xzf $PACKAGE_NAME"
echo "3. Installer les dépendances: pip install -r requirements.txt"
echo "4. Collecter les fichiers statiques: python manage.py collectstatic --noinput"
echo "5. Appliquer les migrations: python manage.py migrate"
echo "6. Redémarrer le serveur applicatif"