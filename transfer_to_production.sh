#!/bin/bash
# Script de transfert des modifications vers production
# Date: $(date +%Y-%m-%d)

# Configuration
PRODUCTION_HOST="root@martialcomp.com"
PRODUCTION_DIR="/var/www/martialcomp"
LOCAL_DIR="/mnt/c/martial_hub_django/martialcomp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_before_transfer_$TIMESTAMP"

echo "======================================"
echo "TRANSFERT VERS PRODUCTION - MartialComp"
echo "======================================"
echo "Host: $PRODUCTION_HOST"
echo "Date: $(date)"
echo ""

# 1. Créer le patch du commit principal
echo "1. Création du patch pour le commit 80e4485..."
mkdir -p patches
git format-patch -1 80e4485 -o patches/

# 2. Préparer les fichiers modifiés
echo "2. Préparation des fichiers modifiés..."
mkdir -p transfer_package

# Copier les fichiers modifiés de l'API
cp -v api/urls.py transfer_package/
cp -v api_auth/views.py transfer_package/
cp -v api_auth/models.py transfer_package/
cp -v api_auth/serializers.py transfer_package/
cp -v api_auth/urls.py transfer_package/

# 3. Créer une archive du dossier apps
echo "3. Création de l'archive du dossier apps..."
tar -czf transfer_package/apps.tar.gz apps/

# 4. Créer le script de déploiement distant
cat > transfer_package/deploy_on_server.sh << 'EOF'
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
EOF

chmod +x transfer_package/deploy_on_server.sh

# 5. Créer le rapport de transfert
cat > transfer_package/transfer_report.txt << EOF
RAPPORT DE TRANSFERT - $(date)
================================

Fichiers transférés:
- api/urls.py
- api_auth/views.py
- api_auth/models.py
- api_auth/serializers.py
- api_auth/urls.py
- apps/ (archive complète)
- Patch du commit 80e4485

Modifications principales:
1. Nouvelle API mobile enrichie (/api/v1/auth/profile/)
2. Login social (Google/Facebook)
3. Nouveaux endpoints health et dashboard mobile
4. Structure complète du dossier apps

Instructions post-déploiement:
1. Vérifier les logs: tail -f /var/log/nginx/error.log
2. Tester l'API: curl https://martialcomp.com/api/health/
3. Vérifier les migrations: python manage.py showmigrations
EOF

echo ""
echo "Package de transfert préparé dans: transfer_package/"
echo ""
echo "Prêt pour le transfert SSH. Veuillez fournir le mot de passe quand demandé."