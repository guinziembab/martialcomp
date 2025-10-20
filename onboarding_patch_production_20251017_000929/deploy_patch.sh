#!/bin/bash
# Script de déploiement du patch onboarding en production

echo "================================================"
echo "🚀 DÉPLOIEMENT PATCH ONBOARDING - PRODUCTION"
echo "================================================"
echo ""

# Variables
BACKUP_DIR="/home/martialc/backups/onboarding_$(date +%Y%m%d_%H%M%S)"
PROJECT_DIR="/home/martialc/martialcomp"

# Créer le répertoire de backup
echo "📁 Création du backup..."
mkdir -p $BACKUP_DIR

# Backup des fichiers existants
if [ -f "$PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py" ]; then
    cp $PROJECT_DIR/apps/competitions/views/onboarding/emergency_views.py $BACKUP_DIR/
fi
if [ -f "$PROJECT_DIR/apps/competitions/urls/onboarding.py" ]; then
    cp $PROJECT_DIR/apps/competitions/urls/onboarding.py $BACKUP_DIR/
fi

# Copier les nouveaux fichiers
echo ""
echo "📋 Installation des fichiers..."
cp -r apps/* $PROJECT_DIR/apps/
echo "✅ Fichiers copiés"

# Initialiser les disciplines
echo ""
echo "🔧 Initialisation des disciplines..."
cd $PROJECT_DIR
python manage.py init_disciplines

# Collecter les fichiers statiques
echo ""
echo "📦 Collection des fichiers statiques..."
python manage.py collectstatic --noinput

# Redémarrer les services
echo ""
echo "🔄 Redémarrage des services..."
# Option 1: Passenger
touch tmp/restart.txt
echo "✅ Passenger redémarré"

# Option 2: systemctl (décommenter si nécessaire)
# sudo systemctl restart gunicorn
# sudo systemctl restart nginx

echo ""
echo "================================================"
echo "✅ PATCH DÉPLOYÉ AVEC SUCCÈS!"
echo "================================================"
echo ""
echo "📝 Vérifications recommandées:"
echo "1. Tester l'onboarding: https://app.martialcomp.com/competitions/onboarding/"
echo "2. Vérifier les logs: tail -f /var/log/martialcomp/django.log"
echo "3. En cas de problème, restaurer depuis: $BACKUP_DIR"
