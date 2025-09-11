# Configuration Plesk pour MartialComp
## Adaptation Docker et Synchronisation des Environnements

### 🎯 Vue d'ensemble

Cette configuration adapte MartialComp pour fonctionner avec Plesk tout en maintenant les avantages de Docker et de la synchronisation des environnements.

### 🔧 Configuration Plesk

#### 1. Configuration Nginx dans Plesk

Créer un fichier de configuration Nginx personnalisé :

```nginx
# /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf

server {
    listen 80;
    server_name martialcomp.com www.martialcomp.com;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name martialcomp.com www.martialcomp.com;
    
    # Configuration SSL (gérée par Plesk)
    ssl_certificate /opt/psa/var/certificates/cert-XXXXXX.pem;
    ssl_certificate_key /opt/psa/var/certificates/cert-XXXXXX.key;
    
    # Sécurité
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Logs
    access_log /var/www/vhosts/system/martialcomp.com/logs/access_ssl_log;
    error_log /var/www/vhosts/system/martialcomp.com/logs/error_log;
    
    # Configuration pour Docker
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffers
        proxy_buffer_size 4k;
        proxy_buffers 4 32k;
        proxy_busy_buffers_size 64k;
        
        # Headers
        proxy_set_header Connection "";
        proxy_http_version 1.1;
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
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Sécurité
    location ~ /\. {
        deny all;
    }
    
    # Monitoring
    location /health/ {
        proxy_pass http://127.0.0.1:8002/health/;
        access_log off;
    }
}
```

#### 2. Configuration des Domaines et Sous-domaines

```nginx
# Configuration pour les sous-domaines d'organisations
# /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf

# Wildcard pour les sous-domaines
server {
    listen 443 ssl http2;
    server_name *.martialcomp.com;
    
    # Configuration SSL
    ssl_certificate /opt/psa/var/certificates/cert-XXXXXX.pem;
    ssl_certificate_key /opt/psa/var/certificates/cert-XXXXXX.key;
    
    # Logs spécifiques aux sous-domaines
    access_log /var/www/vhosts/system/martialcomp.com/logs/subdomains_access_log;
    error_log /var/www/vhosts/system/martialcomp.com/logs/subdomains_error_log;
    
    # Proxy vers l'application Django
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Header spécial pour identifier les sous-domaines
        proxy_set_header X-Subdomain $host;
    }
    
    # Fichiers statiques et média identiques
    location /static/ {
        alias /var/www/vhosts/martialcomp.com/httpdocs/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/vhosts/martialcomp.com/httpdocs/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

### 🐳 Adaptation Docker pour Plesk

#### 1. Script de Déploiement Plesk

```bash
#!/bin/bash
# deploy-plesk.sh
# Script de déploiement spécifique pour Plesk

set -e

DOMAIN="martialcomp.com"
HTTPDOCS="/var/www/vhosts/$DOMAIN/httpdocs"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 Déploiement MartialComp sur Plesk"
echo "===================================="

# Vérification des prérequis
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo "❌ Fichier docker-compose.prod.yml non trouvé"
    exit 1
fi

# Créer les répertoires nécessaires
mkdir -p "$HTTPDOCS/staticfiles"
mkdir -p "$HTTPDOCS/media"
mkdir -p "$HTTPDOCS/logs"

# Changer les permissions
chown -R www-data:www-data "$HTTPDOCS"
chmod -R 755 "$HTTPDOCS"

# Démarrer les services Docker
echo "🐳 Démarrage des services Docker..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

# Attendre que les services soient prêts
echo "⏳ Attente des services..."
sleep 30

# Vérifier la santé de l'application
echo "🔍 Vérification de la santé de l'application..."
timeout 60 bash -c 'until curl -f http://localhost:8002/health/; do sleep 2; done'

# Synchroniser les fichiers statiques
echo "📁 Synchronisation des fichiers statiques..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput

# Copier les fichiers statiques vers le répertoire web
docker cp $(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q web):/app/staticfiles/. "$HTTPDOCS/staticfiles/"

# Redémarrer Nginx
echo "🔄 Redémarrage de Nginx..."
systemctl reload nginx

echo "✅ Déploiement terminé!"
echo "   - Application : http://localhost:8002"
echo "   - Nginx : https://$DOMAIN"
echo "   - Logs : $HTTPDOCS/logs/"
```

#### 2. Configuration Systemd pour Docker

```ini
# /etc/systemd/system/martialcomp.service
[Unit]
Description=MartialComp Docker Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

### 🔄 Scripts de Synchronisation Plesk

#### 1. Script de Synchronisation des Environnements

```bash
#!/bin/bash
# sync-plesk-environments.sh
# Synchronisation des environnements pour Plesk

set -e

ENVIRONMENT="${1:-production}"
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups"
HTTPDOCS="/var/www/vhosts/martialcomp.com/httpdocs"

# Créer le répertoire de backup
mkdir -p "$BACKUP_DIR"

case "$ENVIRONMENT" in
    "production")
        echo "🚀 Déploiement en production..."
        DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
        PORT="8002"
        ;;
    "staging")
        echo "🧪 Déploiement en staging..."
        DOCKER_COMPOSE_FILE="docker-compose.staging.yml"
        PORT="8001"
        ;;
    *)
        echo "❌ Environnement non reconnu: $ENVIRONMENT"
        echo "Utilisation: $0 [production|staging]"
        exit 1
        ;;
esac

# Backup de la base de données
echo "📦 Création du backup de la base de données..."
BACKUP_FILE="$BACKUP_DIR/backup_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql"
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dump -U martialcomp -d martialcomp_db > "$BACKUP_FILE"

# Mise à jour du code
echo "📥 Mise à jour du code..."
git fetch origin
git checkout main
git pull origin main

# Reconstruction des services
echo "🔄 Reconstruction des services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build

# Vérification
echo "🔍 Vérification du déploiement..."
sleep 30
curl -f "http://localhost:$PORT/health/" || exit 1

# Synchronisation des fichiers statiques
echo "📁 Synchronisation des fichiers statiques..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput
docker cp $(docker-compose -f "$DOCKER_COMPOSE_FILE" ps -q web):/app/staticfiles/. "$HTTPDOCS/staticfiles/"

# Redémarrage de Nginx
echo "🔄 Redémarrage de Nginx..."
systemctl reload nginx

echo "✅ Synchronisation terminée!"
echo "   - Environnement: $ENVIRONMENT"
echo "   - Port: $PORT"
echo "   - Backup: $BACKUP_FILE"
```

### 📊 Monitoring et Logs

#### 1. Configuration des Logs

```python
# settings/production.py - Configuration des logs pour Plesk

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
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
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/www/vhosts/martialcomp.com/httpdocs/logs/security.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'martialcomp': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

#### 2. Script de Monitoring

```bash
#!/bin/bash
# monitor-plesk.sh
# Monitoring des services MartialComp sur Plesk

DOMAIN="martialcomp.com"
HTTPDOCS="/var/www/vhosts/$DOMAIN/httpdocs"
LOG_FILE="$HTTPDOCS/logs/monitoring.log"

echo "$(date): Début du monitoring" >> "$LOG_FILE"

# Vérifier Docker
if ! docker-compose -f "$HTTPDOCS/docker-compose.prod.yml" ps | grep -q "Up"; then
    echo "$(date): ❌ Services Docker non disponibles" >> "$LOG_FILE"
    # Redémarrer les services
    docker-compose -f "$HTTPDOCS/docker-compose.prod.yml" up -d
fi

# Vérifier l'application
if ! curl -f http://localhost:8002/health/ > /dev/null 2>&1; then
    echo "$(date): ❌ Application non disponible" >> "$LOG_FILE"
    # Notifier l'administrateur
    echo "MartialComp indisponible" | mail -s "Alerte MartialComp" admin@martialcomp.com
fi

# Vérifier l'espace disque
DISK_USAGE=$(df -h "$HTTPDOCS" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "$(date): ⚠️ Espace disque critique: $DISK_USAGE%" >> "$LOG_FILE"
fi

echo "$(date): Monitoring terminé" >> "$LOG_FILE"
```

### 🔧 Configuration Cron

```bash
# Ajouter au crontab root
# crontab -e

# Monitoring toutes les 5 minutes
*/5 * * * * /var/www/vhosts/martialcomp.com/httpdocs/monitor-plesk.sh

# Backup quotidien
0 2 * * * /var/www/vhosts/martialcomp.com/httpdocs/backup-daily.sh

# Nettoyage des logs hebdomadaire
0 3 * * 0 /usr/bin/find /var/www/vhosts/martialcomp.com/httpdocs/logs -name "*.log" -mtime +7 -delete

# Synchronisation des fichiers statiques
0 4 * * * /var/www/vhosts/martialcomp.com/httpdocs/sync-static-files.sh
```

### 📋 Checklist de Déploiement Plesk

- [ ] Configuration Nginx mise à jour
- [ ] Certificats SSL configurés
- [ ] Services Docker démarrés
- [ ] Base de données migrée
- [ ] Fichiers statiques synchronisés
- [ ] Permissions correctes
- [ ] Logs configurés
- [ ] Monitoring actif
- [ ] Backup automatique configuré
- [ ] Tests de santé réussis

Cette configuration permet de bénéficier des avantages de Docker tout en s'intégrant parfaitement avec Plesk pour la gestion des domaines, certificats SSL et monitoring.