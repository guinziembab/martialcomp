#!/bin/bash
# Script à exécuter sur le serveur de production

PROD_DIR="/var/www/martialcomp"
BACKUP_DIR="$PROD_DIR/backups/$(date +%Y%m%d_%H%M%S)"

echo "Déploiement sur le serveur de production..."

# Créer le backup
echo "1. Création du backup..."
mkdir -p "$BACKUP_DIR"
cp -r $PROD_DIR/api $BACKUP_DIR/
cp -r $PROD_DIR/api_auth $BACKUP_DIR/
cp -r $PROD_DIR/apps $BACKUP_DIR/ 2>/dev/null || true

# Appliquer les modifications
echo "2. Application des modifications..."

# API files
cp -v api/urls.py $PROD_DIR/api/
cp -v api_auth/views.py $PROD_DIR/api_auth/
cp -v api_auth/models.py $PROD_DIR/api_auth/
cp -v api_auth/serializers.py $PROD_DIR/api_auth/
cp -v api_auth/urls.py $PROD_DIR/api_auth/

# Extract apps folder
echo "3. Extraction du dossier apps..."
tar -xzf apps.tar.gz -C $PROD_DIR/

# Apply the patch
echo "4. Application du patch Git..."
cd $PROD_DIR
git apply patches/*.patch || echo "Patch peut-être déjà appliqué"

# Collecter les fichiers statiques
echo "5. Collecte des fichiers statiques..."
cd $PROD_DIR
python manage.py collectstatic --noinput

# Migrations
echo "6. Application des migrations..."
python manage.py migrate

# Redémarrer les services
echo "7. Redémarrage des services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "Déploiement terminé!"
