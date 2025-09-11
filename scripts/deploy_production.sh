#!/bin/bash
# Script de déploiement en production - Templates et Dashboard

echo "🚀 Déploiement des templates et dashboard en production"
echo "=================================================="

# Variables
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
TEMPLATES_DIR="competitions/templates"
STATIC_DIR="competitions/static"

# Créer la sauvegarde
echo "📦 Création de la sauvegarde..."
mkdir -p $BACKUP_DIR
cp -r $TEMPLATES_DIR $BACKUP_DIR/ 2>/dev/null || true
cp -r $STATIC_DIR $BACKUP_DIR/ 2>/dev/null || true

# Redémarrer le serveur Django si en production
if [ "$DJANGO_ENV" = "production" ]; then
    echo "🔄 Redémarrage du serveur Django..."
    systemctl restart gunicorn || service gunicorn restart || echo "⚠️ Impossible de redémarrer gunicorn"
fi

# Collecter les fichiers statiques
echo "📁 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Compiler les traductions
echo "🌍 Compilation des traductions..."
python manage.py compilemessages

echo "✅ Déploiement terminé!"
echo "📦 Sauvegarde disponible dans: $BACKUP_DIR"
