#!/bin/bash

echo "🔄 TRANSFERT ONBOARDING DÉVELOPPEMENT → PRODUCTION"
echo "=================================================="

# Configuration
DEV_DIR="/mnt/c/martial_hub_django/martialcomp"
PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

# Créer un backup de la production
echo "📦 Création du backup de production..."
BACKUP_DIR="/var/backups/onboarding_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup des fichiers critiques
cp -r "$PROD_DIR/apps/competitions/views/onboarding" "$BACKUP_DIR/"
cp -r "$PROD_DIR/apps/competitions/forms/onboarding.py" "$BACKUP_DIR/"
cp -r "$PROD_DIR/apps/competitions/urls/onboarding.py" "$BACKUP_DIR/"
cp -r "$PROD_DIR/apps/competitions/templates/competitions/onboarding" "$BACKUP_DIR/"

echo "✅ Backup créé dans: $BACKUP_DIR"

# Transférer les vues d'onboarding
echo "📁 Transfert des vues d'onboarding..."
cp -r "$DEV_DIR/apps/competitions/views/onboarding"/* "$PROD_DIR/apps/competitions/views/onboarding/"

# Transférer le formulaire d'onboarding
echo "📝 Transfert du formulaire d'onboarding..."
cp "$DEV_DIR/apps/competitions/forms/onboarding.py" "$PROD_DIR/apps/competitions/forms/onboarding.py"

# Transférer les URLs d'onboarding
echo "🔗 Transfert des URLs d'onboarding..."
cp "$DEV_DIR/apps/competitions/urls/onboarding.py" "$PROD_DIR/apps/competitions/urls/onboarding.py"

# Transférer les templates d'onboarding
echo "🎨 Transfert des templates d'onboarding..."
cp -r "$DEV_DIR/apps/competitions/templates/competitions/onboarding"/* "$PROD_DIR/apps/competitions/templates/competitions/onboarding/"

# Transférer les fichiers CSS d'onboarding
echo "💄 Transfert des styles d'onboarding..."
if [ -f "$DEV_DIR/apps/competitions/static/css/onboarding.css" ]; then
    cp "$DEV_DIR/apps/competitions/static/css/onboarding.css" "$PROD_DIR/apps/competitions/static/css/"
fi

# Redémarrer Passenger
echo "🔄 Redémarrage de Passenger..."
touch "$PROD_DIR/passenger_wsgi.py"

echo "✅ Transfert terminé!"
echo "📁 Backup disponible dans: $BACKUP_DIR"
echo "🧪 Testez maintenant: https://app.martialcomp.com/fr/competitions/onboarding/federation/"

