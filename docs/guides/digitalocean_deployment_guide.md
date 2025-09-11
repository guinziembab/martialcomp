# Guide de Déploiement MartialComp sur DigitalOcean

## 🚀 **ÉTAPE 1 : PRÉPARATION & COMPTE DIGITALOCEAN**

### 1.1 Création du Compte
1. **Allez sur** : https://www.digitalocean.com
2. **Créez un compte** avec votre email professionnel
3. **Vérifiez votre carte bancaire** (prélèvement de 1$ temporaire)
4. **Utilisez le code promo** `DO100` pour 100$ de crédit gratuit
5. **Activez 2FA** dans Security Settings

### 1.2 Configuration Initiale
```bash
# Générer une clé SSH sur votre machine locale
ssh-keygen -t rsa -b 4096 -C "votre-email@example.com"
# Fichier généré : ~/.ssh/id_rsa.pub
```

**Dans DigitalOcean Dashboard :**
- Settings → Security → SSH Keys
- Add SSH Key → Coller le contenu de `id_rsa.pub`
- Nommer : "MartialComp-Deploy-Key"

---

## 🖥️ **ÉTAPE 2 : CRÉATION DE L'INFRASTRUCTURE**

### 2.1 Création du Droplet Principal
**Dans DigitalOcean Dashboard :**
1. **Create → Droplets**
2. **Configuration recommandée :**
```
✅ Image: Ubuntu 22.04 LTS x64
✅ Plan: Basic Plan
✅ CPU Options: Regular Intel - 4GB/2vCPU ($24/month)
✅ Datacenter: Amsterdam 3 (AMS3) - Europe RGPD
✅ VPC Network: Default
✅ Authentication: SSH Keys - Sélectionner votre clé
✅ Hostname: martialcomp-prod
✅ Tags: production, web-server
```

### 2.2 Configuration Base de Données PostgreSQL
1. **Create → Databases**
2. **Configuration :**
```
✅ Engine: PostgreSQL 15
✅ Plan: Basic - 1GB RAM/1vCPU ($15/month)
✅ Datacenter: Amsterdam 3 (même que le Droplet)
✅ Database name: martialcomp_db
✅ User: martialcomp_user
✅ VPC Network: Default (même réseau que Droplet)
```

### 2.3 Configuration Redis Cache
1. **Create → Databases**
2. **Configuration :**
```
✅ Engine: Redis 7
✅ Plan: Basic - 1GB RAM ($15/month)
✅ Datacenter: Amsterdam 3
✅ VPC Network: Default
```

### 2.4 Configuration Spaces (Stockage)
1. **Create → Spaces**
2. **Configuration :**
```
✅ Datacenter: Amsterdam 3
✅ Space name: martialcomp-media
✅ File Listing: Restricted (sécurité)
✅ CDN: Enable (accélération)
```

---

## 🔧 **ÉTAPE 3 : CONFIGURATION DU SERVEUR**

### 3.1 Connexion au Serveur
```bash
# Récupérer l'IP de votre Droplet dans le dashboard
ssh root@VOTRE_IP_DROPLET

# Première connexion - Mise à jour système
apt update && apt upgrade -y
```

### 3.2 Installation des Outils Essentiels
```bash
# Installation Docker et Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installation Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Installation des outils système
apt install -y nginx git htop curl wget unzip fail2ban ufw

# Configuration Firewall
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
```

### 3.3 Configuration Nginx
```bash
# Créer la configuration Nginx
nano /etc/nginx/sites-available/martialcomp
```

**Contenu du fichier nginx :**
```nginx
server {
    listen 80;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # Redirection HTTPS (après configuration SSL)
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name votre-domaine.com www.votre-domaine.com;
    
    # Configuration SSL (à configurer avec Certbot)
    # ssl_certificate /etc/letsencrypt/live/votre-domaine.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/votre-domaine.com/privkey.pem;
    
    # Sécurité
    client_max_body_size 50M;
    
    # Proxy vers Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Fichiers statiques
    location /static/ {
        alias /opt/martialcomp/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers media via Spaces
    location /media/ {
        proxy_pass https://martialcomp-media.ams3.digitaloceanspaces.com/;
    }
}
```

```bash
# Activer la configuration
ln -s /etc/nginx/sites-available/martialcomp /etc/nginx/sites-enabled/
nginx -t  # Tester la configuration
systemctl reload nginx
```

---

## 🐳 **ÉTAPE 4 : DÉPLOIEMENT AVEC DOCKER**

### 4.1 Structure du Projet
```bash
# Créer l'arborescence
mkdir -p /opt/martialcomp/{app,data,logs}
cd /opt/martialcomp
```

### 4.2 Docker Compose Configuration
```bash
nano docker-compose.yml
```

**Contenu docker-compose.yml :**
```yaml
version: '3.8'

services:
  web:
    build: 
      context: ./app
      dockerfile: Dockerfile
    container_name: martialcomp_web
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app
      - ./data/staticfiles:/app/staticfiles
      - ./logs:/app/logs
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com
      - DATABASE_URL=postgresql://user:password@host:port/dbname
      - REDIS_URL=redis://redis-host:port
      - SECRET_KEY=votre-secret-key-securise
      - SPACES_ACCESS_KEY=votre-spaces-key
      - SPACES_SECRET_KEY=votre-spaces-secret
      - SPACES_BUCKET_NAME=martialcomp-media
      - SPACES_REGION=ams3
    depends_on:
      - redis-local
    networks:
      - martialcomp_network

  redis-local:
    image: redis:7-alpine
    container_name: martialcomp_redis_local
    restart: unless-stopped
    ports:
      - "6380:6379"  # Port local différent du Redis managé
    volumes:
      - ./data/redis:/data
    networks:
      - martialcomp_network

  # Worker Celery pour tâches asynchrones
  celery:
    build: 
      context: ./app
      dockerfile: Dockerfile
    container_name: martialcomp_celery
    restart: unless-stopped
    command: celery -A martialcomp worker -l info
    volumes:
      - ./app:/app
      - ./logs:/app/logs
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://user:password@host:port/dbname
      - REDIS_URL=redis://redis-local:6379
    depends_on:
      - redis-local
    networks:
      - martialcomp_network

networks:
  martialcomp_network:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
```

### 4.3 Dockerfile pour Django
```bash
nano app/Dockerfile
```

**Contenu Dockerfile :**
```dockerfile
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
        gettext \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Installation des dépendances Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . /app/

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Port d'écoute
EXPOSE 8000

# Script de démarrage
COPY scripts/start.sh /app/
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
```

### 4.4 Script de Démarrage
```bash
nano app/scripts/start.sh
```

**Contenu start.sh :**
```bash
#!/bin/bash

echo "🚀 Démarrage de MartialComp..."

# Attendre que la base de données soit prête
echo "⏳ Vérification de la base de données..."
python manage.py check --database default

# Migrations
echo "📊 Application des migrations..."
python manage.py migrate --no-input

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --no-input

# Création du superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@martialcomp.com', 'TempPassword123!')
    print('✅ Superutilisateur créé')
else:
    print('✅ Superutilisateur existe déjà')
"

# Démarrage du serveur
echo "🌐 Démarrage du serveur Django..."
exec gunicorn martialcomp.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level info
```

---

## ⚙️ **ÉTAPE 5 : CONFIGURATION DES VARIABLES D'ENVIRONNEMENT**

### 5.1 Récupération des Informations DigitalOcean

**Base de données PostgreSQL :**
```bash
# Dans le dashboard DigitalOcean → Databases → votre-postgresql
# Copiez les informations de connexion :
DATABASE_URL=postgresql://username:password@host:port/database?sslmode=require
```

**Redis :**
```bash
# Dans le dashboard DigitalOcean → Databases → votre-redis
REDIS_URL=rediss://username:password@host:port?ssl_cert_reqs=required
```

**Spaces (S3-compatible) :**
```bash
# Dans le dashboard DigitalOcean → API → Spaces Keys
# Générer une nouvelle clé :
SPACES_ACCESS_KEY=your-access-key
SPACES_SECRET_KEY=your-secret-key
```

### 5.2 Fichier de Configuration Sécurisé
```bash
# Créer le fichier d'environnement
nano /opt/martialcomp/.env.prod
```

**Contenu .env.prod :**
```bash
# Django Configuration
DEBUG=False
SECRET_KEY=votre-secret-key-tres-securise-minimum-50-caracteres
ALLOWED_HOSTS=votre-domaine.com,www.votre-domaine.com,127.0.0.1

# Database
DATABASE_URL=postgresql://user:password@db-host:25060/martialcomp_db?sslmode=require

# Redis
REDIS_URL=rediss://user:password@redis-host:25061?ssl_cert_reqs=required

# DigitalOcean Spaces
SPACES_ACCESS_KEY=your-access-key
SPACES_SECRET_KEY=your-secret-key
SPACES_BUCKET_NAME=martialcomp-media
SPACES_REGION=ams3
SPACES_ENDPOINT_URL=https://ams3.digitaloceanspaces.com

# Email Configuration (optionnel)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password

# Multi-tenant
DEFAULT_SCHEMA=public
TENANT_MODEL=competitions.models.Organization
TENANT_DOMAIN_MODEL=competitions.models.Domain
```

---

## 🚀 **ÉTAPE 6 : DÉPLOIEMENT ET LANCEMENT**

### 6.1 Transfert du Code
```bash
# Sur votre machine locale - Cloner votre repo
git clone https://github.com/votre-username/martialcomp.git /tmp/martialcomp

# Transférer vers le serveur
rsync -avz --exclude='.git' --exclude='__pycache__' \
  /tmp/martialcomp/ root@VOTRE_IP:/opt/martialcomp/app/

# Ou directement sur le serveur
cd /opt/martialcomp/app
git clone https://github.com/votre-username/martialcomp.git .
```

### 6.2 Configuration des Permissions
```bash
# Permissions des dossiers
chmod +x /opt/martialcomp/app/scripts/start.sh
chown -R www-data:www-data /opt/martialcomp/data
chmod -R 755 /opt/martialcomp/data
```

### 6.3 Lancement des Services
```bash
cd /opt/martialcomp

# Construction et lancement
docker-compose up -d --build

# Vérification des logs
docker-compose logs -f web

# Test de la base de données
docker-compose exec web python manage.py check --database default

# Application des migrations
docker-compose exec web python manage.py migrate
```

---

## 🔒 **ÉTAPE 7 : CONFIGURATION SSL ET SÉCURITÉ**

### 7.1 Installation Certbot (Let's Encrypt)
```bash
# Installation Certbot
apt install certbot python3-certbot-nginx -y

# Génération du certificat SSL
certbot --nginx -d votre-domaine.com -d www.votre-domaine.com

# Test de renouvellement automatique
certbot renew --dry-run
```

### 7.2 Configuration de la Sécurité
```bash
# Configuration fail2ban
nano /etc/fail2ban/jail.local
```

**Contenu jail.local :**
```ini
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-noscript]
enabled = true
```

```bash
# Redémarrage fail2ban
systemctl restart fail2ban
```

---

## 📊 **ÉTAPE 8 : MONITORING ET MAINTENANCE**

### 8.1 Configuration des Logs
```bash
# Rotation des logs
nano /etc/logrotate.d/martialcomp
```

**Contenu logrotate :**
```
/opt/martialcomp/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    notifempty
    create 644 www-data www-data
    postrotate
        docker-compose -f /opt/martialcomp/docker-compose.yml restart web
    endscript
}
```

### 8.2 Script de Backup Automatique
```bash
nano /opt/scripts/backup-martialcomp.sh
```

**Contenu backup script :**
```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/martialcomp"
DATE=$(date +%Y%m%d_%H%M%S)

# Création du dossier de backup
mkdir -p $BACKUP_DIR

# Backup de la base de données
docker-compose -f /opt/martialcomp/docker-compose.yml exec -T web \
    python manage.py dumpdata --natural-foreign --natural-primary \
    > $BACKUP_DIR/db_backup_$DATE.json

# Backup des fichiers de configuration
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    /opt/martialcomp/docker-compose.yml \
    /opt/martialcomp/.env.prod \
    /etc/nginx/sites-available/martialcomp

# Nettoyage des anciens backups (garde 7 jours)
find $BACKUP_DIR -name "*.json" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "✅ Backup completed: $DATE"
```

```bash
# Rendre le script exécutable
chmod +x /opt/scripts/backup-martialcomp.sh

# Ajouter au cron (backup quotidien à 2h)
crontab -e
# Ajouter: 0 2 * * * /opt/scripts/backup-martialcomp.sh
```

---

## ✅ **ÉTAPE 9 : VÉRIFICATIONS FINALES**

### 9.1 Tests de Fonctionnement
```bash
# Test de l'application
curl -I https://votre-domaine.com

# Vérification Docker
docker-compose ps

# Logs d'erreur
docker-compose logs web | grep ERROR

# Test base de données
docker-compose exec web python manage.py shell -c "
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT version();')
print('✅ PostgreSQL:', cursor.fetchone()[0])
"
```

### 9.2 Performance et Optimisation
```bash
# Test de charge basique
apt install apache2-utils -y
ab -n 100 -c 10 https://votre-domaine.com/

# Monitoring des ressources
htop
docker stats
```

---

## 🎯 **RÉCAPITULATIF DES COÛTS FINAUX**

```
💰 COÛT MENSUEL TOTAL ESTIMÉ
├── Droplet 4GB/2vCPU: 24€
├── PostgreSQL 1GB: 15€
├── Redis 1GB: 15€
├── Spaces 500GB: 10€
├── Backup storage: 2€
└── TOTAL: 66€/mois
```

**🎁 Avec le code promo DO100, vous avez ~1.5 mois gratuits !**