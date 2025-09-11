#!/bin/bash
# Script de déploiement corrigé pour le bon répertoire

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
BACKUP_DIR="$PROD_DIR/backups/$(date +%Y%m%d_%H%M%S)"
CURRENT_DIR="/tmp/transfer_package"

echo "======================================"
echo "DÉPLOIEMENT CORRIGÉ - MartialComp"
echo "======================================"
echo "Répertoire de production : $PROD_DIR"
echo ""

# 1. Créer le répertoire de backup
echo "1. Création du backup..."
mkdir -p "$BACKUP_DIR"

# Sauvegarder les fichiers existants
if [ -d "$PROD_DIR/api" ]; then
    cp -r "$PROD_DIR/api" "$BACKUP_DIR/"
    echo "   - api/ sauvegardé"
fi

if [ -d "$PROD_DIR/api_auth" ]; then
    cp -r "$PROD_DIR/api_auth" "$BACKUP_DIR/"
    echo "   - api_auth/ sauvegardé"
fi

if [ -d "$PROD_DIR/apps" ]; then
    cp -r "$PROD_DIR/apps" "$BACKUP_DIR/"
    echo "   - apps/ sauvegardé"
fi

# 2. Créer les répertoires si nécessaires
echo -e "\n2. Préparation des répertoires..."
mkdir -p "$PROD_DIR/api"
mkdir -p "$PROD_DIR/api_auth"

# 3. Copier les nouveaux fichiers
echo -e "\n3. Copie des nouveaux fichiers..."

# Copier api/urls.py
if [ -f "$CURRENT_DIR/urls.py" ]; then
    # Le premier urls.py est pour api/
    cp -v "$CURRENT_DIR/urls.py" "$PROD_DIR/api/urls.py"
fi

# Copier les fichiers api_auth
cp -v "$CURRENT_DIR/views.py" "$PROD_DIR/api_auth/views.py"
cp -v "$CURRENT_DIR/models.py" "$PROD_DIR/api_auth/models.py"
cp -v "$CURRENT_DIR/serializers.py" "$PROD_DIR/api_auth/serializers.py"

# Note: Il y a deux urls.py dans transfer_package, il faut identifier lequel va où
# Pour l'instant on suppose que le deuxième est pour api_auth
if [ -f "$CURRENT_DIR/urls.py" ]; then
    echo "   Note: Vérifiez manuellement quel urls.py va dans api_auth/"
fi

# 4. Extraire et installer apps
echo -e "\n4. Installation du dossier apps..."
cd "$PROD_DIR"
tar -xzf "$CURRENT_DIR/apps.tar.gz"
echo "   - apps/ extrait avec succès"

# 5. Appliquer le patch s'il existe
echo -e "\n5. Application du patch Git..."
if [ -f "/tmp/patches/0001-Backend-expose-enriched-organization-in-api-v1-auth-.patch" ]; then
    cd "$PROD_DIR"
    git apply "/tmp/patches/0001-Backend-expose-enriched-organization-in-api-v1-auth-.patch" || echo "   Patch peut-être déjà appliqué"
else
    echo "   Aucun patch trouvé dans /tmp/patches/"
fi

# 6. Collecter les fichiers statiques
echo -e "\n6. Collecte des fichiers statiques..."
cd "$PROD_DIR"
python manage.py collectstatic --noinput || python3 manage.py collectstatic --noinput

# 7. Appliquer les migrations
echo -e "\n7. Application des migrations..."
python manage.py migrate || python3 manage.py migrate

# 8. Vérifier et redémarrer les services
echo -e "\n8. Redémarrage des services..."

# Vérifier quel serveur d'application est utilisé
if systemctl is-active --quiet gunicorn; then
    echo "   - Redémarrage de Gunicorn..."
    systemctl restart gunicorn
elif systemctl is-active --quiet uwsgi; then
    echo "   - Redémarrage de uWSGI..."
    systemctl restart uwsgi
else
    echo "   - Recherche du processus Python/Django..."
    # Essayer de trouver le processus
    ps aux | grep -E "python.*manage.py|gunicorn|uwsgi" | grep -v grep
fi

# Redémarrer Nginx
if systemctl is-active --quiet nginx; then
    echo "   - Redémarrage de Nginx..."
    systemctl restart nginx
fi

# Apache si utilisé par Plesk
if systemctl is-active --quiet apache2; then
    echo "   - Redémarrage d'Apache..."
    systemctl restart apache2
fi

echo -e "\n======================================"
echo "DÉPLOIEMENT TERMINÉ!"
echo "======================================"
echo ""
echo "Actions de vérification :"
echo "1. Vérifiez le site : https://martialcomp.com"
echo "2. Testez la nouvelle API : curl https://martialcomp.com/api/v1/auth/profile/"
echo "3. Vérifiez les logs :"
echo "   - tail -f /var/log/nginx/error.log"
echo "   - journalctl -u gunicorn -f"
echo ""
echo "Backup créé dans : $BACKUP_DIR"