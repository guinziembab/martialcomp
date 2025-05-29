# Configuration des Sous-domaines pour Multi-Tenant

Ce guide explique comment configurer votre serveur web et DNS pour gérer les sous-domaines multi-tenant.

## Configuration DNS

### 1. Wildcard DNS

Ajoutez un enregistrement wildcard DNS pour capturer tous les sous-domaines :

```
*.martialcomp.com.  IN  A  YOUR_SERVER_IP
```

Ou pour le développement local :
```
*.martialcomp.local  IN  A  127.0.0.1
```

### 2. Domaines spécifiques

Pour chaque tenant avec un domaine personnalisé :
```
clubname.com.  IN  A  YOUR_SERVER_IP
www.clubname.com.  IN  CNAME  clubname.com.
```

## Configuration Nginx

### Production avec SSL

```nginx
# Configuration pour tous les sous-domaines *.martialcomp.com
server {
    listen 80;
    server_name *.martialcomp.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name *.martialcomp.com;

    # Certificat SSL wildcard
    ssl_certificate /etc/letsencrypt/live/martialcomp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/martialcomp.com/privkey.pem;
    
    # Configuration SSL standard
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers "EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH";
    
    # Logs
    access_log /var/log/nginx/martialcomp.access.log;
    error_log /var/log/nginx/martialcomp.error.log;
    
    # Fichiers statiques et media
    location /static/ {
        alias /var/www/martialcomp/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/martialcomp/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    # Proxy vers l'application Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout pour les longues requêtes
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Configuration pour les domaines personnalisés
server {
    listen 80;
    server_name clubname.com www.clubname.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name clubname.com www.clubname.com;
    
    # Certificat SSL spécifique au domaine
    ssl_certificate /etc/letsencrypt/live/clubname.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/clubname.com/privkey.pem;
    
    # Même configuration que ci-dessus
    # ...
}
```

### Développement local

```nginx
server {
    listen 80;
    server_name *.martialcomp.local;
    
    location /static/ {
        alias /home/user/martialcomp/static/;
    }
    
    location /media/ {
        alias /home/user/martialcomp/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Configuration Apache

### Production avec SSL

```apache
<VirtualHost *:80>
    ServerName martialcomp.com
    ServerAlias *.martialcomp.com
    
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName martialcomp.com
    ServerAlias *.martialcomp.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/martialcomp.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/martialcomp.com/privkey.pem
    
    DocumentRoot /var/www/martialcomp
    
    # Fichiers statiques
    Alias /static /var/www/martialcomp/static
    <Directory /var/www/martialcomp/static>
        Require all granted
    </Directory>
    
    Alias /media /var/www/martialcomp/media
    <Directory /var/www/martialcomp/media>
        Require all granted
    </Directory>
    
    # Proxy vers Django
    ProxyPreserveHost On
    ProxyPass /static/ !
    ProxyPass /media/ !
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    
    ErrorLog ${APACHE_LOG_DIR}/martialcomp.error.log
    CustomLog ${APACHE_LOG_DIR}/martialcomp.access.log combined
</VirtualHost>
```

## Configuration du fichier hosts (développement local)

Pour tester en local, ajoutez dans `/etc/hosts` (Linux/Mac) ou `C:\Windows\System32\drivers\etc\hosts` (Windows) :

```
127.0.0.1  martialcomp.local
127.0.0.1  club1.martialcomp.local
127.0.0.1  club2.martialcomp.local
127.0.0.1  test.martialcomp.local
```

## Configuration Django

### 1. Settings.py

```python
# Domaines autorisés
ALLOWED_HOSTS = [
    '.martialcomp.com',  # Wildcard pour tous les sous-domaines
    '.martialcomp.local',  # Pour le développement local
    'localhost',
    '127.0.0.1',
]

# Domaines de base pour la validation
TENANT_BASE_DOMAINS = ['martialcomp.com', 'martialcomp.local']

# URL du site principal
SITE_URL = 'https://martialcomp.com'
if DEBUG:
    SITE_URL = 'http://martialcomp.local:8000'
```

### 2. Middleware

Le middleware est déjà configuré dans `multitenant/middleware.py` pour identifier les tenants par sous-domaine.

## Test de configuration

### 1. Test local

```bash
# Démarrer le serveur de développement
python manage.py runserver 0.0.0.0:8000

# Tester avec curl
curl -H "Host: club1.martialcomp.local" http://localhost:8000
```

### 2. Test de production

```bash
# Test DNS
dig club1.martialcomp.com

# Test HTTPS
curl -v https://club1.martialcomp.com
```

## Certificats SSL

### Let's Encrypt wildcard

```bash
# Obtenir un certificat wildcard
certbot certonly --manual -d *.martialcomp.com -d martialcomp.com

# Renouvellement automatique
certbot renew --dry-run
```

### Certificat pour domaine personnalisé

```bash
# Pour chaque domaine client
certbot certonly -d clubname.com -d www.clubname.com
```

## Dépannage

### Problèmes courants

1. **404 sur les sous-domaines**
   - Vérifier la configuration DNS
   - Vérifier ALLOWED_HOSTS dans Django
   - Vérifier les logs Nginx/Apache

2. **Tenant non trouvé**
   - Vérifier que le tenant existe en base
   - Vérifier le slug correspond au sous-domaine
   - Vérifier que is_active = True

3. **Certificat SSL invalide**
   - Vérifier que le certificat couvre le sous-domaine
   - Utiliser un certificat wildcard *.martialcomp.com

### Logs utiles

```bash
# Logs Django
tail -f /var/log/martialcomp/django.log

# Logs Nginx
tail -f /var/log/nginx/martialcomp.error.log

# Logs Apache
tail -f /var/log/apache2/martialcomp.error.log
```

## Sécurité

1. **Isolation des données**
   - Le middleware garantit l'isolation par schéma PostgreSQL
   - Tester régulièrement avec `python manage.py test_tenant_isolation`

2. **CORS**
   - Configurer CORS pour autoriser uniquement les domaines des tenants
   - Utiliser django-cors-headers si nécessaire

3. **CSP (Content Security Policy)**
   - Définir des politiques CSP strictes
   - Autoriser uniquement les ressources du domaine du tenant

## Prochaines étapes

1. Configurer le serveur web selon votre environnement
2. Mettre en place les certificats SSL
3. Créer un premier tenant de test
4. Tester l'accès via sous-domaine
5. Configurer le monitoring et les alertes