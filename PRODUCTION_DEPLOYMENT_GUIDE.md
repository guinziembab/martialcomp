# 🚀 MartialComp - Guide de Déploiement Production

> **Version**: 1.0  
> **Date**: Septembre 2025  
> **Environnement**: Plesk + Cloudflare + Django  
> **Serveur**: Ionos VPS - Ubuntu/Debian

---

## 📋 Table des Matières

1. [Architecture Générale](#architecture-générale)
2. [Configuration Serveur](#configuration-serveur)
3. [Configuration Plesk](#configuration-plesk)
4. [Configuration Cloudflare](#configuration-cloudflare)
5. [Configuration Django](#configuration-django)
6. [Services Système](#services-système)
7. [Base de Données](#base-de-données)
8. [Fichiers Statiques](#fichiers-statiques)
9. [Sécurité](#sécurité)
10. [Monitoring](#monitoring)
11. [Procédures de Migration](#procédures-de-migration)
12. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Générale

```
Internet → Cloudflare CDN → Plesk Nginx → Apache → Gunicorn → Django
                                     ↓
                              PostgreSQL + Redis (si utilisé)
```

### Stack Technique
- **OS**: Ubuntu 22.04+ / Debian 12+
- **Panel**: Plesk Obsidian
- **Proxy**: Nginx (Plesk) → Apache → Gunicorn
- **Application**: Django 4.2+
- **Database**: PostgreSQL 16+
- **Cache**: Redis (optionnel)
- **CDN**: Cloudflare
- **SSL**: Let's Encrypt via Cloudflare

---

## 🖥️ Configuration Serveur

### Prérequis Système
```bash
# Paquets requis
apt update && apt upgrade -y
apt install -y python3 python3-venv python3-pip
apt install -y postgresql postgresql-contrib
apt install -y redis-server  # optionnel
apt install -y git curl wget
```

### Structure des Répertoires
```
/var/www/vhosts/martialcomp.com/
├── conf/                           # Configuration Plesk
│   ├── vhost_nginx.conf           # Config Nginx personnalisée
│   └── vhost_ssl_nginx.conf       # Config SSL personnalisée
├── httpdocs/                      # Code source Django
│   ├── apps/                      # Applications Django
│   ├── config/                    # Configuration Django
│   │   └── settings/              # Settings par environnement
│   │       ├── base.py           # Settings de base
│   │       ├── production.py     # Settings production
│   │       └── development.py    # Settings développement
│   ├── static/                    # Fichiers statiques collectés
│   ├── media/                     # Fichiers uploadés
│   ├── logs/                      # Logs Django
│   ├── manage.py                  # Script Django
│   └── requirements.txt           # Dépendances Python
├── venv/                          # Environnement virtuel Python
└── logs/                          # Logs Plesk
```

### Permissions
```bash
# Propriétaire et permissions
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/
chmod -R 775 /var/www/vhosts/martialcomp.com/httpdocs/static/
chmod -R 775 /var/www/vhosts/martialcomp.com/httpdocs/media/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/logs/
```

---

## 🎛️ Configuration Plesk

### Paramètres du Domaine

#### Hébergement Web
```
Type d'hébergement: Apache & nginx
Document root: /var/www/vhosts/martialcomp.com/httpdocs
Proxy mode: Désactivé (important!)
PHP: Désactivé (Django utilise Python)
```

#### SSL/TLS
```
Certificat: Let's Encrypt via Extension Cloudflare
Redirection HTTPS: Activée au niveau Cloudflare (pas Plesk)
HSTS: Configuré via Django settings
```

### Configuration Nginx (Plesk)

#### Fichier: `/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf`
```nginx
# Configuration multilingue pour Django i18n
location ~ ^/(fr|en|es|it|de|pt|ru|vi|no|ja|zh-hans|hi|ar|sw|am|zu|yo|ko)/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
}

# Route pour les URLs d'administration
location ~ ^/(admin|api|accounts)/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Fichiers statiques
location /static/ {
    alias /var/www/vhosts/martialcomp.com/httpdocs/static/;
    expires 30d;
    access_log off;
}

# Fichiers média
location /media/ {
    alias /var/www/vhosts/martialcomp.com/httpdocs/media/;
    expires 7d;
}
```

#### Fichier: `/var/www/vhosts/system/martialcomp.com/conf/vhost_ssl_nginx.conf`
```nginx
# Configuration SSL identique à vhost_nginx.conf
# (Copier le même contenu)
```

### Configuration Apache (via Plesk)

#### Directives Apache additionnelles
```apache
# Support des headers Cloudflare
LoadModule headers_module modules/mod_headers.so
LoadModule rewrite_module modules/mod_rewrite.so

# Configuration des headers de sécurité
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set Referrer-Policy strict-origin-when-cross-origin

# Configuration pour Cloudflare
SetEnvIf X-Forwarded-Proto "https" HTTPS=on
```

---

## ☁️ Configuration Cloudflare

### DNS Records
```
Type    Name    Content              TTL     Proxy
A       @       217.154.24.122       Auto    Proxied (Orange)
A       www     217.154.24.122       Auto    Proxied (Orange)
A       *       217.154.24.122       Auto    Proxied (Orange)
```

### SSL/TLS Settings
```
Mode: Full (strict)
Edge Certificates: Let's Encrypt
Always Use HTTPS: On
Automatic HTTPS Rewrites: On
Minimum TLS Version: 1.2
```

### Security Settings
```
Security Level: Medium
Bot Fight Mode: On
Browser Integrity Check: On
Challenge Passage: 30 minutes
```

### Page Rules
```
URL: martialcomp.com/*
Settings:
- Always Use HTTPS: On
- Browser Cache TTL: 8 days
- Edge Cache TTL: 7 days
```

### Speed Settings
```
Auto Minify: HTML, CSS, JavaScript
Brotli: On
Early Hints: On
```

---

## ⚙️ Configuration Django

### Structure des Settings

#### `config/settings/base.py` - Configuration de Base
```python
"""
Configuration de base pour MartialComp
"""
import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'corsheaders',
    'rest_framework',
    'rosetta',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.competitions',
    'apps.organizations',
    'apps.grades',
    'apps.shop',
    'apps.permissions_manager',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware configuration
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # CRITIQUE!
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.permissions_manager.middleware.PermissionCacheMiddleware',
]

ROOT_URLCONF = 'config.urls'

# Database (sera surchargé en production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('fr', _('Français')),
    ('en', _('English')),
    ('es', _('Español')),
    ('it', _('Italiano')),
    ('de', _('Deutsch')),
    ('pt', _('Português')),
    ('ru', _('Русский')),
    ('vi', _('Tiếng Việt')),
    ('no', _('Norsk')),
    ('ja', _('日本語')),
    ('zh-hans', _('中文简体')),
    ('hi', _('हिंदी')),
    ('ar', _('العربية')),
    ('sw', _('Kiswahili')),
    ('am', _('አማርኛ')),
    ('zu', _('isiZulu')),
    ('yo', _('Yorùbá')),
    ('ko', _('한국어')),
]

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

# Static files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Allauth configuration
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# Authentication URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/competitions/onboarding/role/'
LOGOUT_REDIRECT_URL = '/'
```

#### `config/settings/production.py` - Configuration Production
```python
"""
Configuration de production pour MartialComp
"""
import os
from pathlib import Path
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECRET KEY - OBLIGATOIRE en production
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'CHANGEZ-MOI-EN-PRODUCTION')

# Hosts autorisés
ALLOWED_HOSTS = [
    'martialcomp.com',
    'www.martialcomp.com',
    '*.martialcomp.com',
    '217.154.24.122',  # IP serveur
]

# Database PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'martialcomp_prod'),
        'USER': os.environ.get('DB_USER', 'martialcomp_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'prefer',
        },
    }
}

# Configuration Cloudflare
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

# Security settings
SECURE_SSL_REDIRECT = False  # Géré par Cloudflare
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session and CSRF security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# CSRF Trusted Origins pour Cloudflare
CSRF_TRUSTED_ORIGINS = [
    'https://martialcomp.com',
    'https://www.martialcomp.com',
    'https://*.martialcomp.com',
]

# Static files
STATIC_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/static/'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = '/var/www/vhosts/martialcomp.com/httpdocs/media/'
MEDIA_URL = '/media/'

# Cache avec Redis (optionnel)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = 'MartialComp <noreply@martialcomp.com>'

# Logging
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
            'class': 'logging.FileHandler',
            'filename': '/var/www/vhosts/martialcomp.com/httpdocs/logs/django.log',
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/www/vhosts/martialcomp.com/httpdocs/logs/django_error.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

print("✅ Configuration de production chargée")
```

### Variables d'Environnement

#### Fichier: `/var/www/vhosts/martialcomp.com/httpdocs/.env`
```bash
# Base de données
DB_NAME=martialcomp_prod
DB_USER=martialcomp_user
DB_PASSWORD=votre_mot_de_passe_securise
DB_HOST=localhost
DB_PORT=5432

# Django
DJANGO_SECRET_KEY=votre_cle_secrete_django_tres_longue_et_aleatoire
DJANGO_SETTINGS_MODULE=config.settings.production

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_email

# Cache Redis (optionnel)
REDIS_URL=redis://127.0.0.1:6379/1

# Debug (production)
DEBUG=False
```

---

## 🔧 Services Système

### Service Gunicorn

#### Fichier: `/etc/systemd/system/martialcomp.service`
```ini
[Unit]
Description=Gunicorn instance to serve MartialComp Django
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
Environment="PATH=/var/www/vhosts/martialcomp.com/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/var/www/vhosts/martialcomp.com/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --bind 127.0.0.1:8000 \
    --timeout 300 \
    --keep-alive 2 \
    --log-level info \
    --log-file /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn.log \
    --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Commandes de Gestion
```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable martialcomp.service
sudo systemctl start martialcomp.service

# Vérifier le statut
sudo systemctl status martialcomp.service

# Redémarrer
sudo systemctl restart martialcomp.service

# Voir les logs
sudo journalctl -u martialcomp.service -f
```

---

## 🗄️ Base de Données

### Configuration PostgreSQL

#### Installation
```bash
# Installation PostgreSQL
sudo apt install postgresql postgresql-contrib

# Création utilisateur et base
sudo -u postgres psql
CREATE DATABASE martialcomp_prod;
CREATE USER martialcomp_user WITH PASSWORD 'mot_de_passe_securise';
GRANT ALL PRIVILEGES ON DATABASE martialcomp_prod TO martialcomp_user;
ALTER USER martialcomp_user CREATEDB;
\q
```

#### Configuration de Sécurité
```bash
# Fichier: /etc/postgresql/16/main/postgresql.conf
listen_addresses = 'localhost'
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB

# Fichier: /etc/postgresql/16/main/pg_hba.conf
# Connexions locales uniquement
local   all             martialcomp_user                md5
host    all             martialcomp_user    127.0.0.1/32    md5
```

#### Maintenance
```bash
# Sauvegarde
pg_dump -U martialcomp_user -h localhost martialcomp_prod > backup_$(date +%Y%m%d_%H%M%S).sql

# Restauration
psql -U martialcomp_user -h localhost martialcomp_prod < backup_file.sql
```

---

## 📁 Fichiers Statiques

### Configuration
```bash
# Répertoires
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/static
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs/media

# Permissions
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs/static/
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs/media/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/static/
chmod -R 755 /var/www/vhosts/martialcomp.com/httpdocs/media/
```

### Collecte des Statiques
```bash
# Script de déploiement
#!/bin/bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source ../venv/bin/activate
python manage.py collectstatic --noinput --clear
python manage.py compress  # Si django-compressor est utilisé
deactivate
```

---

## 🔒 Sécurité

### Checklist Sécurité Production

#### Django Settings
- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` unique et sécurisée
- [ ] `ALLOWED_HOSTS` configuré correctement
- [ ] HTTPS forcé (via Cloudflare)
- [ ] Headers de sécurité configurés
- [ ] CSRF protection activée
- [ ] Session cookies sécurisés

#### Serveur
- [ ] Utilisateur `www-data` pour les fichiers web
- [ ] Permissions fichiers correctes (755/644)
- [ ] `.env` protégé (600)
- [ ] Logs non accessibles publiquement
- [ ] Firewall configuré
- [ ] SSH avec clés uniquement

#### Base de Données
- [ ] Utilisateur dédié avec permissions minimales
- [ ] Connexions locales uniquement
- [ ] Mot de passe fort
- [ ] Sauvegardes régulières

### Pare-feu UFW
```bash
# Configuration basique
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Apache Full'
ufw allow 'Nginx Full'
ufw enable
```

---

## 📊 Monitoring

### Scripts de Monitoring

#### Fichier: `/root/scripts/health_check.sh`
```bash
#!/bin/bash
# Health check pour MartialComp

echo "=== MartialComp Health Check ==="
echo "Date: $(date)"

# Service Gunicorn
echo "--- Gunicorn Status ---"
systemctl is-active martialcomp.service

# Test HTTP
echo "--- HTTP Test ---"
curl -I -s https://martialcomp.com | head -n 1

# Database
echo "--- Database Test ---"
sudo -u postgres psql -d martialcomp_prod -c "SELECT COUNT(*) FROM django_migrations;" 2>/dev/null || echo "DB Error"

# Disk Usage
echo "--- Disk Usage ---"
df -h /var/www/vhosts/martialcomp.com/

echo "=== End Health Check ==="
```

#### Crontab pour Monitoring
```bash
# Crontab pour root
0 */6 * * * /root/scripts/health_check.sh >> /var/log/martialcomp_health.log 2>&1
0 2 * * * /root/scripts/backup_db.sh
```

### Logs à Surveiller
```bash
# Logs système
tail -f /var/log/syslog
tail -f /var/log/auth.log

# Logs Apache/Nginx
tail -f /var/www/vhosts/system/martialcomp.com/logs/access_log
tail -f /var/www/vhosts/system/martialcomp.com/logs/error_log

# Logs Django
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn.log

# Logs PostgreSQL
tail -f /var/log/postgresql/postgresql-16-main.log
```

---

## 🔄 Procédures de Migration

### Migration vers Nouveau Serveur

#### 1. Préparation Nouveau Serveur
```bash
# Installation des dépendances
apt update && apt upgrade -y
# Installer Plesk, PostgreSQL, Python, etc.

# Création utilisateurs et base de données
# Configuration Plesk et Cloudflare
```

#### 2. Sauvegarde Ancien Serveur
```bash
#!/bin/bash
# Script de sauvegarde complète

BACKUP_DIR="/root/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Code source
tar -czf $BACKUP_DIR/httpdocs.tar.gz -C /var/www/vhosts/martialcomp.com/ httpdocs/

# Base de données
pg_dump -U martialcomp_user martialcomp_prod > $BACKUP_DIR/database.sql

# Configuration Plesk
cp /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf $BACKUP_DIR/
cp /etc/systemd/system/martialcomp.service $BACKUP_DIR/

# Logs importants
tar -czf $BACKUP_DIR/logs.tar.gz /var/www/vhosts/martialcomp.com/httpdocs/logs/

echo "Sauvegarde créée dans: $BACKUP_DIR"
```

#### 3. Restauration Nouveau Serveur
```bash
#!/bin/bash
# Script de restauration

BACKUP_DIR="/path/to/backup"

# Restaurer le code
cd /var/www/vhosts/martialcomp.com/
tar -xzf $BACKUP_DIR/httpdocs.tar.gz

# Restaurer la base
psql -U martialcomp_user -h localhost martialcomp_prod < $BACKUP_DIR/database.sql

# Restaurer les configurations
cp $BACKUP_DIR/vhost_nginx.conf /var/www/vhosts/system/martialcomp.com/conf/
cp $BACKUP_DIR/martialcomp.service /etc/systemd/system/

# Permissions
chown -R www-data:www-data /var/www/vhosts/martialcomp.com/httpdocs/

# Services
systemctl daemon-reload
systemctl enable martialcomp.service
systemctl start martialcomp.service
```

#### 4. Tests de Validation
```bash
# Tests après migration
# 1. Vérifier services
systemctl status martialcomp.service
systemctl status postgresql
systemctl status nginx

# 2. Test HTTP
curl -I https://martialcomp.com

# 3. Test base de données
python manage.py check --deploy

# 4. Test fonctionnalités
# - Connexion utilisateur
# - Création compte
# - Upload fichiers
```

### Mise à Jour Application

#### Procédure Standard
```bash
#!/bin/bash
# Script de mise à jour

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Sauvegarde
pg_dump -U martialcomp_user martialcomp_prod > /root/backups/pre_update_$(date +%Y%m%d_%H%M%S).sql

# 2. Mode maintenance (optionnel)
# Créer page maintenance.html temporaire

# 3. Git pull ou upload nouveau code
git pull origin main  # ou upload manuel

# 4. Environnement virtuel
source ../venv/bin/activate

# 5. Dependencies
pip install -r requirements.txt

# 6. Migrations
python manage.py migrate

# 7. Static files
python manage.py collectstatic --noinput

# 8. Restart services
systemctl restart martialcomp.service

# 9. Tests
curl -I https://martialcomp.com

deactivate
```

---

## 🔍 Troubleshooting

### Problèmes Courants et Solutions Éprouvées

#### 1. Erreur 500 - Django ne démarre pas
```bash
# Vérifier les logs
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn.log
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/django.log

# Tester Django directement
cd /var/www/vhosts/martialcomp.com/httpdocs
source ../venv/bin/activate
python manage.py check
python manage.py shell
```

**Solutions courantes:**
- Middleware allauth manquant → Ajouter à `MIDDLEWARE` dans `base.py`
- SECRET_KEY manquante → Configurer dans `.env.production`
- Base de données inaccessible → Vérifier credentials
- Permissions fichiers → `chown -R www-data:www-data`
- Variables d'environnement non chargées → Vérifier `.env.production`
- Django non installé dans venv → `pip install -r requirements.txt`

#### 1.1. Erreur 400 - Bad Request

**Cause principale**: `ALLOWED_HOSTS` manquant ou mal configuré

**Solution**:
```bash
# Vérifier .env.production
grep ALLOWED_HOSTS /var/www/vhosts/martialcomp.com/httpdocs/.env.production

# Si vide, ajouter:
echo "ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com,*.martialcomp.com,217.154.24.122,127.0.0.1,localhost" >> .env.production

# Redémarrer
systemctl restart martialcomp.service
```

#### 2. Erreur 404 - URLs non trouvées
```bash
# Vérifier configuration Nginx
cat /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf

# Tester proxy
curl -I http://127.0.0.1:8000/

# Vérifier URLs Django
python manage.py show_urls  # si django-extensions installé
```

#### 3. Problèmes SSL/Cloudflare
```bash
# Vérifier certificat
openssl s_client -connect martialcomp.com:443 -servername martialcomp.com

# Tester sans Cloudflare
curl -I --resolve martialcomp.com:443:217.154.24.122 https://martialcomp.com
```

#### 4. Performance/Mémoire
```bash
# Monitoring ressources
htop
iostat -x 1
free -h

# Logs Gunicorn
tail -f /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn.log | grep -E "worker|memory"

# Optimisation Gunicorn
# Ajuster workers, timeout, max-requests dans martialcomp.service
```

### Commandes de Debug Utiles

```bash
# Services système
systemctl status martialcomp.service
systemctl status postgresql
systemctl status nginx
systemctl status apache2

# Réseau
ss -tlnp | grep -E ":80|:443|:8000|:5432"
netstat -tlnp | grep -E "python|postgres|nginx|apache"

# Processus
ps aux | grep -E "gunicorn|postgres|nginx|apache"

# Fichiers/Permissions
ls -la /var/www/vhosts/martialcomp.com/httpdocs/
ls -la /var/www/vhosts/martialcomp.com/httpdocs/config/settings/

# Django
cd /var/www/vhosts/martialcomp.com/httpdocs
source ../venv/bin/activate
python manage.py check --deploy
python manage.py diffsettings
python manage.py showmigrations
```

---

## 📝 Checklist de Déploiement

### Avant Déploiement
- [ ] Serveur configuré (OS, Plesk, PostgreSQL)
- [ ] Domaine pointé vers serveur
- [ ] Cloudflare configuré
- [ ] Certificats SSL actifs

### Déploiement Application
- [ ] Code source uploadé
- [ ] Environnement virtuel créé
- [ ] Dependencies installées (`pip install -r requirements.txt`)
- [ ] Base de données créée et configurée
- [ ] Variables d'environnement configurées (`.env.production` avec ALLOWED_HOSTS)
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Superuser créé (`python manage.py createsuperuser`)
- [ ] Fichiers statiques collectés (`python manage.py collectstatic`)
- [ ] Service Gunicorn configuré et démarré
- [ ] Configuration Nginx/Apache appliquée

### Tests Post-Déploiement
- [ ] Site accessible via HTTPS
- [ ] Toutes les langues fonctionnent (`/fr/`, `/en/`, etc.)
- [ ] Connexion utilisateur OK
- [ ] Interface admin accessible (`/admin/`)
- [ ] Upload de fichiers fonctionne
- [ ] Emails envoyés correctement
- [ ] Performance acceptable (< 3s)

### Monitoring
- [ ] Health check script configuré
- [ ] Logs monitorés
- [ ] Sauvegardes automatiques
- [ ] Alertes configurées

---

## 🆘 Contacts d'Urgence

### Fournisseurs
- **Hébergeur**: Ionos.fr - Support technique
- **Domaine**: OVH/Ionos - Gestion DNS
- **CDN**: Cloudflare - Support Enterprise

### Scripts d'Urgence
```bash
# Redémarrage complet
/root/scripts/restart_all.sh

# Mode maintenance
/root/scripts/maintenance_mode.sh

# Rollback rapide
/root/scripts/rollback.sh
```

---

## 📋 Changelog

| Version | Date | Changements |
|---------|------|-------------|
| 1.0 | Sept 2025 | Configuration initiale complète |

---

**Document maintenu par**: Équipe DevOps MartialComp  
**Dernière révision**: Septembre 2025  
**Prochaine révision**: Décembre 2025

---

> ⚠️ **Important**: Toujours tester les modifications sur un environnement de staging avant la production.
> 
> 🔐 **Sécurité**: Ne jamais commiter les fichiers `.env` ou les mots de passe dans le contrôle de version.