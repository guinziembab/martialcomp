#!/bin/bash

# Script pour préparer l'archive de déploiement MartialComp
# À exécuter dans le répertoire du projet

echo "🏗️ Préparation de l'archive de déploiement..."

# Créer le répertoire de déploiement
mkdir -p deployment_package

# Créer l'archive avec les fichiers essentiels
tar -czf deployment_package/martialcomp.tar.gz \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='env' \
    --exclude='venv' \
    --exclude='db.sqlite3' \
    --exclude='media' \
    --exclude='static' \
    --exclude='*.log' \
    --exclude='Cache' \
    --exclude='backups' \
    --exclude='*.docx' \
    --exclude='*.pdf' \
    --exclude='*.png' \
    --exclude='*.jpg' \
    --exclude='clubs/logos' \
    --exclude='federations/logos' \
    --exclude='competitions/logos' \
    --exclude='*.md' \
    --exclude='*.bat' \
    --exclude='*.ps1' \
    config/ \
    competitions/ \
    api/ \
    api_auth/ \
    documents/ \
    finances/ \
    grades/ \
    multitenant/ \
    organizations/ \
    permissions_manager/ \
    security/ \
    shop/ \
    scripts/ \
    deployment/ \
    manage.py \
    requirements.txt \
    locale/

echo "✅ Archive créée: deployment_package/martialcomp.tar.gz"
echo "📦 Taille: $(du -h deployment_package/martialcomp.tar.gz | cut -f1)"

# Créer le script de déploiement distant
cat > deployment_package/deploy_remote.sh << 'EOF'
#!/bin/bash

# Script de déploiement à exécuter sur le serveur DigitalOcean
set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🥋 DÉPLOIEMENT MARTIALCOMP - DIGITALOCEAN"
echo "========================================"

# Variables (à personnaliser)
DOMAIN="${DOMAIN:-martialcomp.com}"
ADMIN_EMAIL="${ADMIN_EMAIL:-bertrand.guinziemba@gmail.com}"
DB_PASSWORD="${DB_PASSWORD:-MartialComp2024!}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 50)}"

log_info "Configuration: $DOMAIN"

# ÉTAPE 1: Mise à jour système
log_info "Mise à jour du système..."
apt update && apt upgrade -y

# ÉTAPE 2: Installation des dépendances
log_info "Installation des dépendances..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    postgresql \
    postgresql-contrib \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    ufw \
    fail2ban \
    htop \
    supervisor \
    redis-server \
    libpq-dev \
    libjpeg-dev \
    libpng-dev

# ÉTAPE 3: Configuration sécurité
log_info "Configuration sécurité..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'
ufw --force enable

# ÉTAPE 4: Utilisateur deploy
log_info "Création utilisateur deploy..."
if ! id "deploy" &>/dev/null; then
    adduser --disabled-password --gecos "" deploy
    usermod -aG sudo deploy
fi

mkdir -p /home/deploy/.ssh
cp ~/.ssh/authorized_keys /home/deploy/.ssh/ 2>/dev/null || true
chown -R deploy:deploy /home/deploy/.ssh
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys 2>/dev/null || true

sudo -u deploy mkdir -p /home/deploy/{logs,backups,static,media}

# ÉTAPE 5: PostgreSQL
log_info "Configuration PostgreSQL..."
sudo -u postgres psql << EOSQL
CREATE DATABASE martialcomp_prod;
CREATE USER martialcomp_user WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE martialcomp_user SET client_encoding TO 'utf8';
ALTER ROLE martialcomp_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE martialcomp_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE martialcomp_prod TO martialcomp_user;
\\q
EOSQL

systemctl restart postgresql

# ÉTAPE 6: Décompression du projet
log_info "Installation du projet..."
cd /home/deploy
tar -xzf martialcomp.tar.gz
chown -R deploy:deploy martialcomp

# ÉTAPE 7: Environnement Python
log_info "Configuration Python..."
sudo -u deploy python3 -m venv /home/deploy/venv
sudo -u deploy /bin/bash << 'EOPY'
source /home/deploy/venv/bin/activate
pip install --upgrade pip
cd /home/deploy/martialcomp
pip install -r requirements.txt
pip install psycopg2-binary gunicorn
EOPY

# ÉTAPE 8: Configuration Django
log_info "Configuration Django..."
sudo -u deploy tee /home/deploy/martialcomp/config/production.env > /dev/null << EOENV
SECRET_KEY=$SECRET_KEY
DEBUG=False
DJANGO_SETTINGS_MODULE=config.settings_production

DB_NAME=martialcomp_prod
DB_USER=martialcomp_user
DB_PASSWORD=$DB_PASSWORD
DB_HOST=localhost
DB_PORT=5432

DOMAIN_NAME=$DOMAIN
SITE_URL=https://$DOMAIN
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@$DOMAIN
EMAIL_HOST_PASSWORD=change_me
DEFAULT_FROM_EMAIL=MartialComp <noreply@$DOMAIN>
ADMIN_EMAIL=$ADMIN_EMAIL

REDIS_URL=redis://127.0.0.1:6379/1
EOENV

# ÉTAPE 9: Django - migrations et collectstatic
log_info "Déploiement Django..."
sudo -u deploy /bin/bash << 'EOPY'
cd /home/deploy/martialcomp
source /home/deploy/venv/bin/activate
export $(grep -v '^#' config/production.env | xargs)

python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', '$ADMIN_EMAIL', 'MartialComp2024!') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell
EOPY

# ÉTAPE 10: Nginx
log_info "Configuration Nginx..."
tee /etc/nginx/sites-available/martialcomp > /dev/null << EONGINX
upstream martialcomp_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location /static/ {
        alias /home/deploy/static/;
        expires 1y;
    }
    
    location /media/ {
        alias /home/deploy/media/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://martialcomp_app;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    client_max_body_size 50M;
}
EONGINX

rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/martialcomp /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# ÉTAPE 11: Supervisor pour Gunicorn
log_info "Configuration Supervisor..."
tee /etc/supervisor/conf.d/martialcomp.conf > /dev/null << EOSUP
[program:martialcomp]
command=/bin/bash -c "cd /home/deploy/martialcomp && export \$(grep -v '^#' config/production.env | xargs) && exec /home/deploy/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 config.wsgi:application"
directory=/home/deploy/martialcomp
user=deploy
group=deploy
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/deploy/logs/gunicorn.log
EOSUP

supervisorctl reread
supervisorctl update
supervisorctl start martialcomp

# ÉTAPE 12: Redis
systemctl start redis-server
systemctl enable redis-server

log_success "Déploiement terminé !"
echo "🌐 Site: http://$DOMAIN"
echo "👤 Admin: http://$DOMAIN/admin/ (admin/MartialComp2024!)"
echo "📊 Status: supervisorctl status"

EOF

chmod +x deployment_package/deploy_remote.sh

echo "✅ Script de déploiement distant créé"
echo ""
echo "📋 Prochaines étapes:"
echo "1. Transférer l'archive: scp deployment_package/* root@VOTRE_IP:~/"
echo "2. Se connecter au serveur: ssh root@VOTRE_IP"
echo "3. Exécuter: chmod +x deploy_remote.sh && ./deploy_remote.sh"