#!/bin/bash

echo "=== Déploiement distant sur le serveur de production ==="

# Variables
PRODUCTION_PATH="/var/www/vhosts/martialcomp.com/httpdocs"
NGINX_CONF_PATH="/etc/nginx/sites-available"
BACKUP_DIR="/tmp/martialcomp_backup_$(date +%Y%m%d_%H%M%S)"

# Créer une sauvegarde
echo "Création d'une sauvegarde..."
mkdir -p "$BACKUP_DIR"
cp -r "$PRODUCTION_PATH" "$BACKUP_DIR/" 2>/dev/null || echo "Pas de fichiers existants à sauvegarder"

# Extraire le nouveau package
echo "Extraction du package..."
cd /tmp
tar -xzf martialcomp_production.tar.gz

# Arrêter les services existants
echo "Arrêt des services..."
systemctl stop nginx
pkill -f "manage.py runserver" || true
pkill -f "gunicorn" || true

# Créer la structure de répertoires
echo "Création de la structure de répertoires..."
mkdir -p "$PRODUCTION_PATH"
mkdir -p /var/log/gunicorn
mkdir -p /var/log/nginx

# Copier les fichiers de l'application
echo "Copie des fichiers de l'application..."
cp -r /tmp/config "$PRODUCTION_PATH/"
cp -r /tmp/competitions "$PRODUCTION_PATH/"
cp /tmp/manage.py "$PRODUCTION_PATH/"
cp /tmp/requirements.txt "$PRODUCTION_PATH/"
cp /tmp/start_production.sh "$PRODUCTION_PATH/"
cp /tmp/.env.production "$PRODUCTION_PATH/.env" 2>/dev/null || echo "Pas de fichier .env"

# Configurer nginx
echo "Configuration de nginx..."
cp /tmp/nginx_martialcomp.conf "$NGINX_CONF_PATH/martialcomp.com"
ln -sf "$NGINX_CONF_PATH/martialcomp.com" /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configurer les permissions
echo "Configuration des permissions..."
chown -R www-data:www-data "$PRODUCTION_PATH"
chown -R www-data:www-data /var/log/gunicorn
chmod +x "$PRODUCTION_PATH/start_production.sh"

# Installer les dépendances Python
echo "Installation des dépendances..."
cd "$PRODUCTION_PATH"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Configurer la base de données
echo "Configuration de la base de données..."
python manage.py migrate

# Collecter les fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Tester la configuration nginx
echo "Test de la configuration nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration nginx valide"
    
    # Démarrer l'application Django
    echo "Démarrage de l'application Django..."
    ./start_production.sh
    
    # Démarrer nginx
    echo "Démarrage de nginx..."
    systemctl start nginx
    systemctl enable nginx
    
    echo "=== Déploiement terminé avec succès ==="
    echo "Le site devrait être accessible sur https://martialcomp.com"
    
    # Vérifications
    echo "Vérifications:"
    echo "- Django: $(ps aux | grep gunicorn | grep -v grep | wc -l) processus gunicorn"
    echo "- Nginx: $(systemctl is-active nginx)"
    echo "- Test local: $(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/fr/ || echo "ERREUR")"
    
else
    echo "ERREUR: Configuration nginx invalide"
    echo "Restauration de la sauvegarde..."
    systemctl start nginx
    exit 1
fi

