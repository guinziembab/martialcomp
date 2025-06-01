# Guide d'Infrastructure Multi-Tenant

Ce guide détaille la configuration de l'infrastructure nécessaire pour prendre en charge l'architecture multi-tenant avec sous-domaines.

## Table des matières

1. [Configuration DNS](#configuration-dns)
2. [Configuration SSL](#configuration-ssl)
3. [Configuration du serveur web](#configuration-du-serveur-web)
4. [Configuration de Django](#configuration-de-django)
5. [Sécurité et isolation](#sécurité-et-isolation)
6. [Surveillance et monitoring](#surveillance-et-monitoring)
7. [Liste de contrôle de déploiement](#liste-de-contrôle-de-déploiement)

## Configuration DNS

### 1. Domaine Wildcard

Pour prendre en charge les sous-domaines dynamiques, vous devez configurer un enregistrement DNS wildcard.

#### Configuration chez le registraire (exemple avec OVH, Gandi, Cloudflare)

```
Type: A
Name: *
Value: 123.456.789.0  # Adresse IP de votre serveur
TTL: 3600
```

#### Validation de la configuration DNS

Pour vérifier que votre configuration DNS est correcte, utilisez la commande dig:

```bash
dig +short *.martialcomp.com
dig +short tenant1.martialcomp.com
dig +short tenant2.martialcomp.com
```

Toutes ces commandes devraient retourner la même adresse IP.

### 2. Enregistrements spécifiques

Certains tenants peuvent nécessiter des enregistrements spécifiques, notamment pour la validation SSL.

```
Type: CNAME
Name: tenant1
Value: martialcomp.com
TTL: 3600
```

### 3. Domaines personnalisés

Pour les domaines personnalisés (plan Champion), il faut configurer chaque domaine pour qu'il pointe vers votre serveur:

1. Le tenant devra créer un enregistrement CNAME chez son registraire:
   ```
   Type: CNAME
   Name: @
   Value: martialcomp.com
   ```

2. Alternativement, pour les domaines apex, ils devront configurer un enregistrement A:
   ```
   Type: A
   Name: @
   Value: 123.456.789.0  # Votre IP
   ```

## Configuration SSL

### 1. Certificat Wildcard

Générer un certificat SSL wildcard avec Let's Encrypt:

```bash
sudo certbot certonly --manual --preferred-challenges dns -d martialcomp.com -d *.martialcomp.com
```

Suivez les instructions pour valider votre propriété du domaine via des enregistrements DNS TXT.

### 2. Certificats pour domaines personnalisés

Pour les domaines personnalisés, vous pouvez automatiser avec certbot:

```bash
sudo certbot certonly --webroot -w /var/www/html -d custom-domain.com
```

### 3. Renouvellement automatique

Configurez le renouvellement automatique des certificats:

```bash
sudo crontab -e
```

Ajoutez la ligne suivante pour vérifier le renouvellement deux fois par jour:

```
0 0,12 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

## Configuration du serveur web

### 1. Configuration Nginx

Créez un fichier de configuration pour les sous-domaines:

```bash
sudo nano /etc/nginx/sites-available/martialcomp-tenants
```

Contenu:

```nginx
# Configuration pour les sous-domaines de tenant
server {
    listen 80;
    server_name *.martialcomp.com;
    
    # Redirection HTTP vers HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

# Configuration HTTPS pour les sous-domaines
server {
    listen 443 ssl;
    server_name *.martialcomp.com;
    
    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/martialcomp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/martialcomp.com/privkey.pem;
    
    # Optimisations SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # Paramètres HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Autres en-têtes de sécurité
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Racine du site
    root /var/www/martialcomp;
    
    # Fichiers statiques
    location /static/ {
        alias /var/www/martialcomp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Media uploads
    location /media/ {
        alias /var/www/martialcomp/media/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }
    
    # Proxy pour l'application Django
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout settings
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 2. Configuration pour domaines personnalisés

Créez un modèle de configuration pour les domaines personnalisés:

```bash
sudo nano /etc/nginx/sites-available/martialcomp-custom-domain.template
```

Contenu:

```nginx
# Template for custom domains
server {
    listen 80;
    server_name {{DOMAIN}};
    
    # Redirection HTTP vers HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
    
    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}

server {
    listen 443 ssl;
    server_name {{DOMAIN}};
    
    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/{{DOMAIN}}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{{DOMAIN}}/privkey.pem;
    
    # Optimisations SSL (identiques au template tenant)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    
    # En-têtes de sécurité
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    
    # Configuration identique au reste
    root /var/www/martialcomp;
    
    location /static/ {
        alias /var/www/martialcomp/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    location /media/ {
        alias /var/www/martialcomp/media/;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 3. Script d'automatisation pour les domaines personnalisés

Créez un script pour générer automatiquement les configurations Nginx:

```bash
sudo nano /usr/local/bin/create-tenant-domain.sh
```

Contenu:

```bash
#!/bin/bash
# Script for creating a new custom domain configuration

# Usage: create-tenant-domain.sh example.com

if [ $# -ne 1 ]; then
    echo "Usage: $0 domain.com"
    exit 1
fi

DOMAIN=$1
TEMPLATE="/etc/nginx/sites-available/martialcomp-custom-domain.template"
CONFIG="/etc/nginx/sites-available/$DOMAIN"
ENABLED="/etc/nginx/sites-enabled/$DOMAIN"

# Check if domain already exists
if [ -f "$CONFIG" ]; then
    echo "Configuration for $DOMAIN already exists"
    exit 1
fi

# Create the configuration file from template
cat "$TEMPLATE" | sed "s/{{DOMAIN}}/$DOMAIN/g" > "$CONFIG"

# Create symbolic link
ln -s "$CONFIG" "$ENABLED"

# Request SSL certificate
certbot certonly --webroot -w /var/www/html -d "$DOMAIN"

# Reload Nginx
systemctl reload nginx

echo "Domain $DOMAIN has been configured successfully"
```

Rendez le script exécutable:

```bash
sudo chmod +x /usr/local/bin/create-tenant-domain.sh
```

## Configuration de Django

### 1. Paramètres Django

Mettez à jour `settings.py` pour prendre en charge les sous-domaines:

```python
# Domaines autorisés
ALLOWED_HOSTS = [
    '.martialcomp.com',  # Wildcard pour tous les sous-domaines
    'localhost',
    '127.0.0.1',
]

# Paramètres spécifiques multi-tenant
MULTITENANT_DOMAIN = 'martialcomp.com'

# Secure cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SAMESITE = 'Lax'

# Pour gérer différents domaines
SESSION_COOKIE_DOMAIN = None  # Laissez Django gérer chaque domaine séparément

# Sécurité
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### 2. Configuration de WSGI/ASGI

Pour Gunicorn, ajustez la configuration pour gérer plus de connexions:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers=4 --threads=4 --timeout=300 --max-requests=1000 --max-requests-jitter=50
```

## Sécurité et isolation

### 1. Isolation des données

L'architecture utilise PostgreSQL schema-based pour l'isolation des données. Assurez-vous que:

1. Chaque tenant a son propre schéma PostgreSQL
2. Les permissions sont correctement configurées:

```sql
-- Script à exécuter pour chaque nouveau tenant
CREATE SCHEMA tenant_schema;
GRANT USAGE ON SCHEMA tenant_schema TO web_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA tenant_schema TO web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_schema GRANT ALL ON TABLES TO web_user;
```

### 2. Protection contre les attaques

Ajoutez une protection contre les attaques DDoS et limites de taux:

```nginx
# Dans la configuration Nginx
# Limites de taux globales
limit_req_zone $binary_remote_addr zone=tenant_limit:10m rate=10r/s;

# Dans la section server
location / {
    # Limiter à 10 requêtes/seconde avec une rafale de 20
    limit_req zone=tenant_limit burst=20 nodelay;
    
    # Autres configurations...
}
```

### 3. WAF (Web Application Firewall)

Considérez l'ajout de ModSecurity pour Nginx:

```bash
sudo apt-get install libmodsecurity3 nginx-module-security
```

Configuration de base ModSecurity:

```nginx
# Dans http block
modsecurity on;
modsecurity_rules_file /etc/nginx/modsecurity/main.conf;
```

## Surveillance et monitoring

### 1. Alertes pour expirations SSL

Configurez des alertes pour la surveillance des certificats SSL:

```bash
# Script de vérification d'expiration SSL
sudo nano /usr/local/bin/check_ssl_expiry.sh
```

```bash
#!/bin/bash
# Check SSL certificate expiration

DOMAINS=("martialcomp.com" "*.martialcomp.com" "custom1.com" "custom2.com")
DAYS=30
EMAIL="admin@martialcomp.com"

for domain in "${DOMAINS[@]}"; do
    expiry_date=$(openssl s_client -connect ${domain}:443 -servername ${domain} 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
    expiry_epoch=$(date -d "${expiry_date}" +%s)
    now_epoch=$(date +%s)
    diff_days=$(( (expiry_epoch - now_epoch) / 86400 ))
    
    if [ "${diff_days}" -lt "${DAYS}" ]; then
        echo "Certificate for ${domain} will expire in ${diff_days} days" | mail -s "SSL Certificate Expiry Warning" "${EMAIL}"
    fi
done
```

Ajoutez-le à cron:

```bash
0 8 * * * /usr/local/bin/check_ssl_expiry.sh
```

### 2. Surveillance des journaux Nginx

Configurez la surveillance des erreurs Nginx:

```bash
sudo apt-get install logwatch
sudo nano /etc/logwatch/conf/logfiles/nginx.conf
```

Contenu:

```
LogFile = /var/log/nginx/error.log
LogFile = /var/log/nginx/access.log
```

## Liste de contrôle de déploiement

Avant de déployer en production, vérifiez:

- [ ] Configuration DNS wildcard fonctionnelle
- [ ] Certificat SSL wildcard valide
- [ ] Configuration Nginx optimisée
- [ ] Script d'automatisation pour les domaines personnalisés
- [ ] Paramètres Django correctement configurés
- [ ] Isolation des données PostgreSQL vérifiée
- [ ] Protection WAF et limites de taux configurées
- [ ] Surveillance et monitoring en place
- [ ] Test de charge effectué
- [ ] Documentation complète pour l'équipe technique

## Commandes utiles

### Tester la configuration Nginx

```bash
sudo nginx -t
```

### Recharger Nginx

```bash
sudo systemctl reload nginx
```

### Forcer le renouvellement des certificats

```bash
sudo certbot renew --force-renewal
```

### Créer un nouveau domaine tenant

```bash
sudo create-tenant-domain.sh nouveau-tenant.com
```

### Vérifier l'état du certificat

```bash
sudo certbot certificates
```