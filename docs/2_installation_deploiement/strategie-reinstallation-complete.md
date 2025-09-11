# 🎯 Stratégie de Réinstallation Complète MartialComp
## Approche Dev-First avec Suppression Totale de Production

### 📋 Vue d'ensemble de la Stratégie

**Principe fondamental** : L'environnement de développement local devient le **référentiel unique** pour la nouvelle production.

### 🔄 Flux de Migration

```
Environnement Local (référentiel) 
    ↓
Sauvegarde des données production
    ↓
Suppression complète de la production
    ↓
Déploiement propre depuis le dev
    ↓
Restauration des données
```

---

## 📊 PHASE 0 : Analyse et Préparation

### **Audit de l'environnement local analysé**

✅ **Configuration actuelle identifiée** :
- Django 4.2.23 avec architecture multi-tenant
- 18 applications Django fonctionnelles
- Support de 18 langues
- PostgreSQL + Redis
- Configuration Gunicorn + Nginx prête
- Structure de déploiement existante

✅ **Données à préserver de la production** :
- Base de données PostgreSQL complète
- Fichiers media (logos, documents)
- Configurations de certificats SSL
- Logs de production

---

## 🗑️ PHASE 1 : Suppression Complète de Production

### **1.1 Sauvegarde complète avant destruction**

```bash
# Connexion au serveur
ssh root@martialcomp.com

# Arrêt de tous les services
systemctl stop nginx
pkill -f gunicorn || true
pkill -f celery || true
systemctl stop postgresql
systemctl stop redis

# Sauvegarde COMPLÈTE
mkdir -p /root/backup_final_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/root/backup_final_$(date +%Y%m%d_%H%M%S)"

# Base de données
pg_dump -U martialcomp_user -d martialcomp_db > $BACKUP_DIR/database_complete.sql

# Fichiers de l'application
tar -czf $BACKUP_DIR/app_complete.tar.gz /var/www/vhosts/martialcomp.com/httpdocs/

# Configuration système
cp -r /etc/nginx $BACKUP_DIR/nginx_config
cp -r /etc/systemd/system/martialcomp* $BACKUP_DIR/systemd_config
cp /etc/letsencrypt/live/martialcomp.com/* $BACKUP_DIR/ssl_certs/ 2>/dev/null || true

# Logs
cp -r /var/log/nginx $BACKUP_DIR/nginx_logs
cp -r /var/log/gunicorn $BACKUP_DIR/gunicorn_logs 2>/dev/null || true

echo "✅ Sauvegarde complète terminée dans $BACKUP_DIR"
```

### **1.2 Destruction complète de l'environnement**

```bash
# ATTENTION : Cette commande supprime TOUT !
echo "🔥 DESTRUCTION COMPLÈTE DE L'ENVIRONNEMENT EN COURS..."

# Arrêt et suppression des services
systemctl stop martialcomp 2>/dev/null || true
systemctl disable martialcomp 2>/dev/null || true
rm -f /etc/systemd/system/martialcomp*

# Suppression de l'application web
rm -rf /var/www/vhosts/martialcomp.com/httpdocs/*
rm -rf /var/www/vhosts/martialcomp.com/httpdocs/.*

# Suppression de la base de données
sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS martialcomp_db;
DROP USER IF EXISTS martialcomp_user;
EOF

# Suppression des configurations Nginx
rm -f /etc/nginx/sites-available/martialcomp*
rm -f /etc/nginx/sites-enabled/martialcomp*
rm -f /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf

# Nettoyage des logs
rm -rf /var/log/gunicorn
find /var/log/nginx -name "*martialcomp*" -delete

# Nettoyage des caches et sessions
redis-cli FLUSHALL 2>/dev/null || true

# Suppression des certificats SSL (ils seront regénérés)
certbot delete --cert-name martialcomp.com --non-interactive 2>/dev/null || true

# Suppression des utilisateurs système
userdel -r martialcomp 2>/dev/null || true

echo "💀 DESTRUCTION COMPLÈTE TERMINÉE"
echo "🏗️ Environnement prêt pour une installation propre"
```

---

## 🏗️ PHASE 2 : Préparation du Nouveau Déploiement

### **2.1 Préparation de l'environnement local (référentiel)**

```powershell
# Sur Windows - Préparation du package de déploiement
Write-Host "=== PRÉPARATION DU PACKAGE DEPUIS L'ENVIRONNEMENT DEV ===" -ForegroundColor Cyan

# Nettoyer l'environnement local
cd C:\martial_hub_django\martialcomp
python manage.py collectstatic --noinput --clear
python manage.py compilemessages

# Créer le package de déploiement propre
mkdir C:\martial_hub_django\production_deployment
cd C:\martial_hub_django\production_deployment

# Copier TOUT depuis le dev (sauf éléments exclus)
$excludes = @(".git", "__pycache__", "*.pyc", ".env", "db.sqlite3", "media", "venv", "node_modules")
robocopy C:\martial_hub_django\martialcomp . /E /XD .git __pycache__ venv node_modules /XF *.pyc .env db.sqlite3

Write-Host "✅ Package de production créé depuis l'environnement dev" -ForegroundColor Green
```

### **2.2 Configuration production depuis l'environnement dev**

```powershell
# Créer la configuration de production optimisée
$productionSettings = @"
# config/settings/production.py - Générée depuis l'environnement dev
import os
from pathlib import Path
from .base import *

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')

# Hosts configuration pour multi-tenant
ALLOWED_HOSTS = [
    '.martialcomp.com',      # Tous les sous-domaines
    'martialcomp.com',       # Domaine principal  
    'www.martialcomp.com',   # www
    '212.227.78.104',        # IP serveur IONOS
    '127.0.0.1',
    'localhost',
]

# CSRF pour architecture multi-tenant
CSRF_TRUSTED_ORIGINS = [
    'https://martialcomp.com',
    'https://www.martialcomp.com', 
    'https://*.martialcomp.com',
]

# Database - Depuis l'analyse de l'ancien production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'martialcomp'),
        'USER': os.environ.get('DB_USER', 'martialcomp'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# Cache avec Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'martialcomp_prod',
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_AGE = 1209600  # 2 semaines
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# Security headers
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Email depuis l'analyse production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.ionos.fr')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@martialcomp.com')

# Static files avec WhiteNoise
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Celery pour tâches asynchrones
CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Logging optimisé
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 50 * 1024 * 1024,  # 50 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO', 
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'competitions': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
    },
}

# Configuration spécifique multi-tenant
BASE_URL = os.environ.get('BASE_URL', 'https://martialcomp.com')

# Django-allauth depuis l'analyse
LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/onboarding/role/' 
LOGOUT_REDIRECT_URL = '/fr/'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
"@

$productionSettings | Out-File -FilePath "config\settings\production.py" -Encoding UTF8
Write-Host "✅ Configuration production créée depuis l'analyse" -ForegroundColor Green
```

---

## 🚀 PHASE 3 : Déploiement Propre

### **3.1 Préparation du serveur**

```bash
# Réinstallation des dépendances système
apt update && apt upgrade -y

# Installation des packages essentiels
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y postgresql postgresql-contrib
apt install -y redis-server
apt install -y nginx
apt install -y build-essential libpq-dev gettext
apt install -y supervisor

# Création de l'utilisateur système
useradd --create-home --shell /bin/bash --system martialcomp

# Préparation des dossiers
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/logs
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/media
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/staticfiles

# Permissions
chown -R martialcomp:www-data /var/www/vhosts/martialcomp.com/
chmod -R 755 /var/www/vhosts/martialcomp.com/

echo "✅ Serveur préparé pour le nouveau déploiement"
```

### **3.2 Transfert et installation**

```bash
# Transfert depuis Windows
# scp C:\martial_hub_django\production_deployment.zip root@martialcomp.com:/tmp/

# Sur le serveur - Extraction et installation
cd /var/www/vhosts/martialcomp.com/httpdocs
unzip /tmp/production_deployment.zip

# Création de l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installation des dépendances depuis l'environnement dev
pip install --upgrade pip
pip install -r requirements.txt

# Configuration des variables d'environnement
cat > .env << EOF
SECRET_KEY=$(openssl rand -base64 64)
DEBUG=False

# Database
DB_NAME=martialcomp
DB_USER=martialcomp
DB_PASSWORD=AQWZSX123ok,
DB_HOST=localhost
DB_PORT=5432

# Cache
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.ionos.fr
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_email
DEFAULT_FROM_EMAIL=noreply@martialcomp.com

# Base URL
BASE_URL=https://martialcomp.com
EOF

# Permissions finales
chown -R martialcomp:www-data .
chmod +x manage.py

echo "✅ Application installée depuis l'environnement dev"
```

---

## 🗄️ PHASE 4 : Restauration de la Base de Données

### **4.1 Création de la nouvelle base**

```bash
# Configuration PostgreSQL
sudo -u postgres psql << EOF
CREATE USER martialcomp WITH PASSWORD 'AQWZSX123ok,';
CREATE DATABASE martialcomp OWNER martialcomp;
GRANT ALL PRIVILEGES ON DATABASE martialcomp TO martialcomp;
ALTER USER martialcomp CREATEDB;
EOF

# Application des migrations depuis le dev
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py migrate

echo "✅ Base de données créée avec la structure du dev"
```

### **4.2 Restauration des données de production**

```bash
# Restauration sélective des données importantes
# (Optionnel : restaurer uniquement les données utilisateur, pas la structure)

# Identifier les tables avec données utilisateur importantes
psql -h localhost -U martialcomp -d martialcomp -c "\dt"

# Exemple de restauration sélective (à adapter selon vos besoins)
# pg_restore --data-only --table=auth_user $BACKUP_DIR/database_complete.sql
# pg_restore --data-only --table=organizations_organization $BACKUP_DIR/database_complete.sql

echo "⚠️ Restauration des données à personnaliser selon vos besoins"
```

---

## ⚙️ PHASE 5 : Configuration des Services

### **5.1 Configuration Gunicorn depuis l'environnement dev**

```bash
# Configuration Gunicorn optimisée
cat > gunicorn.conf.py << 'EOF'
import multiprocessing

bind = "127.0.0.1:8001"
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "martialcomp"
group = "www-data"
tmp_upload_dir = "/tmp"
accesslog = "/var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log"
errorlog = "/var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log"
loglevel = "info"
preload_app = True
EOF
```

### **5.2 Service systemd**

```bash
cat > /etc/systemd/system/martialcomp.service << 'EOF'
[Unit]
Description=MartialComp Gunicorn Application Server
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=martialcomp
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
Environment=PYTHONPATH=/var/www/vhosts/martialcomp.com/httpdocs
EnvironmentFile=/var/www/vhosts/martialcomp.com/httpdocs/.env
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/venv/bin/gunicorn \
    --config /var/www/vhosts/martialcomp.com/httpdocs/gunicorn.conf.py \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable martialcomp
systemctl start martialcomp
```

---

## 🌐 PHASE 6 : Configuration Nginx/Plesk

### **6.1 Configuration Nginx pour architecture multi-tenant**

```bash
cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf << 'EOF'
server {
    listen 80;
    server_name martialcomp.com www.martialcomp.com *.martialcomp.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name martialcomp.com www.martialcomp.com *.martialcomp.com;
    
    # SSL géré par Plesk/Let's Encrypt
    ssl_certificate /opt/psa/var/certificates/cert-XXXXXX.pem;
    ssl_certificate_key /opt/psa/var/certificates/cert-XXXXXX.key;
    
    # Logs
    access_log /var/www/vhosts/system/martialcomp.com/logs/access_ssl_log;
    error_log /var/www/vhosts/system/martialcomp.com/logs/error_log;
    
    # Configuration optimisée depuis l'analyse
    client_max_body_size 50M;
    
    # Proxy vers Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Fichiers statiques
    location /static/ {
        alias /var/www/vhosts/martialcomp.com/httpdocs/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers média 
    location /media/ {
        alias /var/www/vhosts/martialcomp.com/httpdocs/media/;
        expires 1M;
        add_header Cache-Control "public";
    }
}
EOF

nginx -t && systemctl reload nginx
```

---

## ✅ PHASE 7 : Validation et Tests

### **7.1 Tests de fonctionnement**

```bash
# Tests de base
curl -f http://localhost:8001/
curl -f https://martialcomp.com/

# Tests des services
systemctl status martialcomp postgresql redis nginx

# Tests de l'application
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py check --deploy
python manage.py collectstatic --noinput
python manage.py showmigrations

# Création du superuser
python manage.py createsuperuser

echo "✅ Tests de validation terminés"
```

---

## 📊 PHASE 8 : Monitoring et Finalisation

### **8.1 Configuration du monitoring**

```bash
# Script de monitoring
cat > /root/monitor-martialcomp.sh << 'EOF'
#!/bin/bash
echo "=== MONITORING MARTIALCOMP ==="
echo "Date: $(date)"
echo ""

# Services
systemctl is-active martialcomp && echo "✅ MartialComp" || echo "❌ MartialComp"
systemctl is-active postgresql && echo "✅ PostgreSQL" || echo "❌ PostgreSQL"
systemctl is-active nginx && echo "✅ Nginx" || echo "❌ Nginx"
systemctl is-active redis && echo "✅ Redis" || echo "❌ Redis"

# Application
curl -f http://localhost:8001/ && echo "✅ Application" || echo "❌ Application"

# Ressources
echo ""
echo "Mémoire:"
free -h | head -2
echo "Disque:"
df -h / | tail -1
EOF

chmod +x /root/monitor-martialcomp.sh

# Cron pour monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/monitor-martialcomp.sh >> /var/log/monitoring.log") | crontab -
```

---

## 🎯 RÉSUMÉ DE LA STRATÉGIE

### ✅ Avantages de cette approche

1. **Environnement dev = référentiel unique** : Cohérence totale
2. **Installation propre** : Pas de pollution de l'ancien système  
3. **Configuration maîtrisée** : Basée sur l'analyse de l'existant
4. **Architecture moderne** : Django 4.2.23 + multi-tenant optimisé
5. **Sécurité renforcée** : Variables d'environnement + SSL
6. **Monitoring intégré** : Surveillance automatique

### 🔄 Points de validation

- [ ] Sauvegarde complète effectuée
- [ ] Environnement de production supprimé
- [ ] Package dev transféré et installé
- [ ] Base de données recréée avec structure dev
- [ ] Services configurés et démarrés
- [ ] Tests de validation passés
- [ ] Monitoring opérationnel

### 🚀 Prochaines étapes

Cette stratégie vous permet de repartir sur une base saine en utilisant votre environnement de développement comme référence, tout en préservant les données importantes de production.

**Voulez-vous que nous commencions par la Phase 1 (sauvegarde et suppression) ?**