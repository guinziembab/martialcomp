# 🚀 Guide de Réinstallation Production MartialComp
## Déploiement propre depuis le backup local

### 📋 Vue d'ensemble

Ce guide vous accompagne pour réinstaller complètement MartialComp en production sur votre serveur IONOS Debian avec Plesk, en utilisant votre backup local comme base.

## 🎯 Situation Actuelle

- ✅ **Backup production** : Créé et analysé
- ✅ **Backup local** : Disponible dans `C:\martial_hub_django\martialcomp_backup_local`
- ✅ **Serveur IONOS** : `root@martialcomp.com` accessible
- ✅ **Architecture** : Nginx + Gunicorn + PostgreSQL + Plesk

## 📦 Phase 1 : Préparation du Backup Local

### **1.1 Vérification du backup local**

```powershell
# Depuis Windows - Analyser le backup
cd C:\martial_hub_django
ls martialcomp_backup_local

# Vérifier les éléments critiques
ls martialcomp_backup_local | Where-Object {$_.Name -in @("config", "manage.py", "competitions", "requirements.txt")}
```

### **1.2 Nettoyage et organisation**

```powershell
# Créer un package de déploiement propre
mkdir C:\martial_hub_django\deployment_package
cd C:\martial_hub_django\deployment_package

# Copier uniquement les éléments essentiels
Copy-Item ..\martialcomp_backup_local\config .\config -Recurse -Force
Copy-Item ..\martialcomp_backup_local\manage.py .\manage.py -Force
Copy-Item ..\martialcomp_backup_local\requirements.txt .\requirements.txt -Force

# Applications Django essentielles
$apps = @("competitions", "organizations", "multitenant", "grades", "finances", "shop", "documents", "family_management", "permissions_manager", "payment", "accounts", "api", "api_auth", "federations")
foreach ($app in $apps) {
    if (Test-Path "..\martialcomp_backup_local\$app") {
        Copy-Item "..\martialcomp_backup_local\$app" ".\$app" -Recurse -Force
        Write-Host "✅ $app copié" -ForegroundColor Green
    } else {
        Write-Host "⚠️ $app manquant" -ForegroundColor Yellow
    }
}

# Templates et statiques
Copy-Item ..\martialcomp_backup_local\templates .\templates -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\martialcomp_backup_local\static .\static -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\martialcomp_backup_local\staticfiles .\staticfiles -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item ..\martialcomp_backup_local\locale .\locale -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "📦 Package de déploiement créé" -ForegroundColor Green
```

### **1.3 Créer le fichier requirements.txt**

```powershell
# Créer un requirements.txt complet
@'
Django==5.1.4
psycopg2-binary==2.9.7
gunicorn==21.2.0
django-environ==0.11.2
django-allauth==0.57.0
django-modeltranslation==0.18.11
django-widget-tweaks==1.5.0
django-crispy-forms==2.0
crispy-bootstrap4==2022.1
django-redis==5.4.0
redis==5.0.1
django-cors-headers==4.3.1
djangorestframework==3.14.0
Pillow==10.0.1
django-rosetta==0.9.9
celery==5.3.4
django-celery-beat==2.5.0
requests==2.31.0
qrcode==7.4.2
stripe==7.8.0
reportlab==4.0.4
whitenoise==6.6.0
python-dateutil==2.8.2
pytz==2023.3
'@ | Out-File -FilePath ".\requirements.txt" -Encoding UTF8

Write-Host "✅ Requirements.txt créé" -ForegroundColor Green
```

## 🗄️ Phase 2 : Préparation du Serveur

### **2.1 Connexion et nettoyage**

```bash
# Connexion au serveur
ssh root@martialcomp.com

# Arrêter les services actuels
systemctl stop nginx
pkill -f gunicorn || true
systemctl stop postgresql || true
systemctl stop redis || true

# Sauvegarder l'installation actuelle
mkdir -p /root/backup_ancien_$(date +%Y%m%d)
cp -r /var/www/vhosts/martialcomp.com/httpdocs /root/backup_ancien_$(date +%Y%m%d)/

# Nettoyer le répertoire web
rm -rf /var/www/vhosts/martialcomp.com/httpdocs/*
mkdir -p /var/www/vhosts/martialcomp.com/httpdocs

echo "✅ Serveur préparé pour la réinstallation"
```

### **2.2 Installation des dépendances système**

```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation des packages essentiels
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y postgresql postgresql-contrib
apt install -y redis-server
apt install -y nginx
apt install -y git curl wget htop vim
apt install -y build-essential libpq-dev gettext

# Vérifier les installations
python3 --version
postgres --version
redis-server --version
nginx -v

echo "✅ Dépendances système installées"
```

## 📤 Phase 3 : Transfert et Installation

### **3.1 Transfert du code depuis Windows**

```powershell
# Depuis Windows - Compresser le package
cd C:\martial_hub_django
Compress-Archive -Path "deployment_package\*" -DestinationPath "martialcomp_deployment.zip" -Force

# Transférer vers le serveur
scp martialcomp_deployment.zip root@martialcomp.com:/tmp/

Write-Host "✅ Code transféré vers le serveur" -ForegroundColor Green
```

### **3.2 Installation sur le serveur**

```bash
# Sur le serveur - Extraire le code
cd /var/www/vhosts/martialcomp.com/httpdocs
unzip /tmp/martialcomp_deployment.zip
chown -R www-data:www-data .

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Code installé et dépendances installées"
```

## 🗃️ Phase 4 : Configuration de la Base de Données

### **4.1 Configuration PostgreSQL**

```bash
# Configurer PostgreSQL
sudo -u postgres psql << EOF
-- Supprimer l'ancienne base si elle existe
DROP DATABASE IF EXISTS martialcomp;
DROP USER IF EXISTS martialcomp;

-- Créer le nouvel utilisateur et la base
CREATE USER martialcomp WITH PASSWORD 'mot_de_passe_securise';
CREATE DATABASE martialcomp OWNER martialcomp;
GRANT ALL PRIVILEGES ON DATABASE martialcomp TO martialcomp;

-- Configuration des permissions
ALTER USER martialcomp CREATEDB;
\q
EOF

# Tester la connexion
psql -h localhost -U martialcomp -d martialcomp -c "SELECT version();"

echo "✅ Base de données configurée"
```

### **4.2 Configuration Django**

```bash
# Configuration des variables d'environnement
cd /var/www/vhosts/martialcomp.com/httpdocs

cat > .env << EOF
SECRET_KEY=$(openssl rand -base64 64)
DEBUG=False
ALLOWED_HOSTS=martialcomp.com,www.martialcomp.com,*.martialcomp.com
CSRF_TRUSTED_ORIGINS=https://martialcomp.com,https://www.martialcomp.com

# Base de données
DATABASE_URL=postgresql://martialcomp:mot_de_passe_securise@localhost:5432/martialcomp

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (à configurer selon vos besoins)
EMAIL_HOST=smtp.ionos.fr
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@martialcomp.com
EMAIL_HOST_PASSWORD=votre_mot_de_passe_email

# Stripe (optionnel)
STRIPE_PUBLISHABLE_KEY=pk_live_votre_cle
STRIPE_SECRET_KEY=sk_live_votre_cle
EOF

# Appliquer les migrations
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py compilemessages

# Créer un superutilisateur
python manage.py createsuperuser

echo "✅ Django configuré"
```

## ⚙️ Phase 5 : Configuration des Services

### **5.1 Configuration Gunicorn**

```bash
# Créer la configuration Gunicorn
cat > /var/www/vhosts/martialcomp.com/httpdocs/gunicorn.conf.py << 'EOF'
import multiprocessing

bind = "127.0.0.1:8001"
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
user = "www-data"
group = "www-data"
tmp_upload_dir = "/tmp"
accesslog = "/var/log/gunicorn/access.log"
errorlog = "/var/log/gunicorn/error.log"
loglevel = "info"
preload_app = True
EOF

# Créer les répertoires de logs
mkdir -p /var/log/gunicorn
chown -R www-data:www-data /var/log/gunicorn

echo "✅ Gunicorn configuré"
```

### **5.2 Configuration du service systemd**

```bash
# Créer le service systemd
cat > /etc/systemd/system/martialcomp.service << 'EOF'
[Unit]
Description=MartialComp Gunicorn Application Server
Documentation=https://docs.gunicorn.org/
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
Environment=PYTHONPATH=/var/www/vhosts/martialcomp.com/httpdocs
Environment=PYTHONUNBUFFERED=1
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/venv/bin/gunicorn \
    --config /var/www/vhosts/martialcomp.com/httpdocs/gunicorn.conf.py \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s TERM $MAINPID
TimeoutStopSec=5
KillMode=mixed
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Activer et démarrer le service
systemctl daemon-reload
systemctl enable martialcomp
systemctl start martialcomp

# Vérifier le statut
systemctl status martialcomp

echo "✅ Service systemd configuré"
```

## 🌐 Phase 6 : Configuration Nginx

### **6.1 Configuration Nginx pour Plesk**

```bash
# Configuration Nginx dans Plesk
cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf << 'EOF'
server {
    listen 80;
    server_name martialcomp.com www.martialcomp.com *.martialcomp.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name martialcomp.com www.martialcomp.com *.martialcomp.com;
    
    # Configuration SSL (géré par Plesk)
    ssl_certificate /opt/psa/var/certificates/cert-XXXXXX.pem;
    ssl_certificate_key /opt/psa/var/certificates/cert-XXXXXX.key;
    
    # Configuration SSL optimisée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Logs
    access_log /var/www/vhosts/system/martialcomp.com/logs/access_ssl_log;
    error_log /var/www/vhosts/system/martialcomp.com/logs/error_log;
    
    # Taille maximum des uploads
    client_max_body_size 20M;
    
    # Proxy vers Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        proxy_buffer_size 4k;
        proxy_buffers 4 32k;
        proxy_busy_buffers_size 64k;
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
    
    # Health check
    location /health/ {
        proxy_pass http://127.0.0.1:8001/health/;
        access_log off;
    }
}
EOF

# Tester et recharger Nginx
nginx -t && systemctl reload nginx

echo "✅ Nginx configuré"
```

## 🧪 Phase 7 : Tests et Validation

### **7.1 Tests de base**

```bash
# Test de l'application
curl -f http://localhost:8001/
curl -f https://martialcomp.com/

# Test de l'admin
curl -f https://martialcomp.com/admin/

# Test de l'API
curl -f https://martialcomp.com/api/

# Vérifier les services
systemctl status martialcomp postgresql redis nginx

echo "✅ Tests de base réussis"
```

### **7.2 Tests des fonctionnalités**

```bash
# Test de la base de données
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
python manage.py check --deploy

# Test des migrations
python manage.py showmigrations

# Test des traductions
python manage.py compilemessages

echo "✅ Tests des fonctionnalités réussis"
```

## 📊 Phase 8 : Monitoring et Maintenance

### **8.1 Configuration du monitoring**

```bash
# Script de monitoring simple
cat > /root/monitor-martialcomp.sh << 'EOF'
#!/bin/bash
echo "=== Monitoring MartialComp ==="
echo "Date: $(date)"
echo ""

# Services
echo "Services:"
systemctl is-active martialcomp && echo "✅ MartialComp" || echo "❌ MartialComp"
systemctl is-active postgresql && echo "✅ PostgreSQL" || echo "❌ PostgreSQL"
systemctl is-active nginx && echo "✅ Nginx" || echo "❌ Nginx"
systemctl is-active redis && echo "✅ Redis" || echo "❌ Redis"

# Application
echo ""
echo "Application:"
curl -f http://localhost:8001/health/ && echo "✅ Health Check" || echo "❌ Health Check"

# Ressources
echo ""
echo "Ressources:"
free -h | head -2
df -h / | tail -1
EOF

chmod +x /root/monitor-martialcomp.sh

# Tâche cron pour monitoring
(crontab -l 2>/dev/null; echo "*/5 * * * * /root/monitor-martialcomp.sh >> /var/log/monitoring.log") | crontab -

echo "✅ Monitoring configuré"
```

### **8.2 Configuration des sauvegardes**

```bash
# Script de sauvegarde
cat > /root/backup-martialcomp.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Sauvegarde base de données
pg_dump -U martialcomp -d martialcomp > $BACKUP_DIR/db_backup_$DATE.sql

# Sauvegarde code
tar -czf $BACKUP_DIR/code_backup_$DATE.tar.gz /var/www/vhosts/martialcomp.com/httpdocs

# Nettoyer les anciens backups (garder 7 jours)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup terminé: $DATE"
EOF

chmod +x /root/backup-martialcomp.sh

# Sauvegarde quotidienne
(crontab -l 2>/dev/null; echo "0 2 * * * /root/backup-martialcomp.sh") | crontab -

echo "✅ Sauvegardes configurées"
```

## ✅ Phase 9 : Checklist Finale

### **9.1 Vérifications finales**

```bash
# Checklist automatique
cat > /root/checklist-final.sh << 'EOF'
#!/bin/bash
echo "=== CHECKLIST FINALE MARTIALCOMP ==="
echo ""

# Services
echo "1. Services:"
systemctl is-active martialcomp && echo "   ✅ MartialComp" || echo "   ❌ MartialComp"
systemctl is-active postgresql && echo "   ✅ PostgreSQL" || echo "   ❌ PostgreSQL"
systemctl is-active nginx && echo "   ✅ Nginx" || echo "   ❌ Nginx"
systemctl is-active redis && echo "   ✅ Redis" || echo "   ❌ Redis"

# Tests
echo ""
echo "2. Tests d'accès:"
curl -f http://localhost:8001/ >/dev/null 2>&1 && echo "   ✅ Application locale" || echo "   ❌ Application locale"
curl -f https://martialcomp.com/ >/dev/null 2>&1 && echo "   ✅ Site HTTPS" || echo "   ❌ Site HTTPS"
curl -f https://martialcomp.com/admin/ >/dev/null 2>&1 && echo "   ✅ Admin" || echo "   ❌ Admin"

# Configuration
echo ""
echo "3. Configuration:"
[ -f /var/www/vhosts/martialcomp.com/httpdocs/.env ] && echo "   ✅ Variables d'environnement" || echo "   ❌ Variables d'environnement"
[ -f /etc/systemd/system/martialcomp.service ] && echo "   ✅ Service systemd" || echo "   ❌ Service systemd"
[ -f /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf ] && echo "   ✅ Configuration Nginx" || echo "   ❌ Configuration Nginx"

# Monitoring
echo ""
echo "4. Monitoring:"
crontab -l | grep -q monitor && echo "   ✅ Monitoring automatique" || echo "   ❌ Monitoring automatique"
crontab -l | grep -q backup && echo "   ✅ Sauvegardes automatiques" || echo "   ❌ Sauvegardes automatiques"

echo ""
echo "=== FIN CHECKLIST ==="
EOF

chmod +x /root/checklist-final.sh
/root/checklist-final.sh
```

## 🎉 Déploiement Terminé !

### **Informations importantes :**

- **URL Application** : https://martialcomp.com
- **Admin Django** : https://martialcomp.com/admin/
- **API** : https://martialcomp.com/api/
- **Health Check** : https://martialcomp.com/health/

### **Commandes utiles :**

```bash
# Redémarrer l'application
systemctl restart martialcomp

# Voir les logs
journalctl -u martialcomp -f

# Monitoring
/root/monitor-martialcomp.sh

# Sauvegarde manuelle
/root/backup-martialcomp.sh

# Checklist
/root/checklist-final.sh
```

### **Maintenance régulière :**

- **Sauvegardes** : Automatiques tous les jours à 2h
- **Monitoring** : Automatique toutes les 5 minutes
- **Logs** : Disponibles dans `/var/log/gunicorn/` et `journalctl`
- **Updates** : À effectuer manuellement selon les besoins

**🎯 Votre installation MartialComp est maintenant opérationnelle !**