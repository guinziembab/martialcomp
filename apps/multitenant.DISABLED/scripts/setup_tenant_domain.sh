#!/bin/bash
# Script for creating a new tenant domain configuration
# Usage: setup_tenant_domain.sh example.com [tenant_schema_name]

set -e

# Check parameters
if [ $# -lt 1 ]; then
    echo "Usage: $0 domain.com [tenant_schema_name]"
    echo "If tenant_schema_name is not provided, it will be derived from domain"
    exit 1
fi

DOMAIN=$1
if [ $# -ge 2 ]; then
    SCHEMA=$2
else
    # Convert domain to schema name (remove non-alphanumeric, replace dots with underscore)
    SCHEMA=$(echo "$DOMAIN" | sed 's/\./_/g' | sed 's/[^a-zA-Z0-9_]//g')
fi

# Configuration paths
NGINX_PATH="/etc/nginx"
SITES_AVAILABLE="${NGINX_PATH}/sites-available"
SITES_ENABLED="${NGINX_PATH}/sites-enabled"
TEMPLATE="${SITES_AVAILABLE}/martialcomp-tenant.template"
CONFIG="${SITES_AVAILABLE}/${DOMAIN}"
ENABLED="${SITES_ENABLED}/${DOMAIN}"
CERT_PATH="/etc/letsencrypt/live"
WEBROOT_PATH="/var/www/html"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Nginx is not installed. Please install it first."
    exit 1
fi

# Check if domain already exists
if [ -f "$CONFIG" ]; then
    echo "Configuration for $DOMAIN already exists"
    echo "If you want to update it, remove it first with: sudo rm $CONFIG $ENABLED"
    exit 1
fi

# Check if template exists
if [ ! -f "$TEMPLATE" ]; then
    echo "Template file not found: $TEMPLATE"
    echo "Creating template file..."
    
    mkdir -p "$SITES_AVAILABLE"
    
    cat > "$TEMPLATE" << EOF
# Template for tenant domains in MartialComp
server {
    listen 80;
    server_name {{DOMAIN}};
    
    # Redirection HTTP vers HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
    
    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root {{WEBROOT_PATH}};
    }
}

server {
    listen 443 ssl;
    server_name {{DOMAIN}};
    
    # Certificats SSL
    ssl_certificate {{CERT_PATH}}/{{DOMAIN}}/fullchain.pem;
    ssl_certificate_key {{CERT_PATH}}/{{DOMAIN}}/privkey.pem;
    
    # Optimisations SSL
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
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Tenant-Schema {{SCHEMA}};
        
        # Timeout settings
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF
    echo "Template created: $TEMPLATE"
fi

# Create the configuration file from template
cat "$TEMPLATE" | sed "s/{{DOMAIN}}/$DOMAIN/g" | sed "s/{{SCHEMA}}/$SCHEMA/g" | sed "s|{{WEBROOT_PATH}}|$WEBROOT_PATH|g" | sed "s|{{CERT_PATH}}|$CERT_PATH|g" > "$CONFIG"
echo "Created configuration: $CONFIG"

# Check if SSL certificate exists
if [ ! -d "${CERT_PATH}/${DOMAIN}" ]; then
    echo "SSL certificate not found for $DOMAIN"
    
    # Check if certbot is installed
    if command -v certbot &> /dev/null; then
        echo "Requesting SSL certificate with certbot..."
        mkdir -p "$WEBROOT_PATH"
        certbot certonly --webroot -w "$WEBROOT_PATH" -d "$DOMAIN" --non-interactive --agree-tos --email admin@martialcomp.com
    else
        echo "Certbot not found. Please install it to automatically generate SSL certificates."
        echo "After installing certbot, run: certbot certonly --webroot -w $WEBROOT_PATH -d $DOMAIN"
        echo "Then run this script again."
        rm "$CONFIG"
        exit 1
    fi
fi

# Create symbolic link
mkdir -p "$SITES_ENABLED"
ln -s "$CONFIG" "$ENABLED"
echo "Enabled configuration: $ENABLED"

# Create PostgreSQL schema if needed
if command -v psql &> /dev/null; then
    echo "Do you want to create PostgreSQL schema '$SCHEMA'? (y/n)"
    read -r create_schema
    
    if [ "$create_schema" = "y" ]; then
        echo "Enter PostgreSQL database name:"
        read -r db_name
        
        echo "Enter PostgreSQL username:"
        read -r db_user
        
        sudo -u postgres psql -d "$db_name" -c "CREATE SCHEMA IF NOT EXISTS $SCHEMA;"
        sudo -u postgres psql -d "$db_name" -c "GRANT USAGE ON SCHEMA $SCHEMA TO $db_user;"
        sudo -u postgres psql -d "$db_name" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA $SCHEMA TO $db_user;"
        sudo -u postgres psql -d "$db_name" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA $SCHEMA GRANT ALL ON TABLES TO $db_user;"
        
        echo "PostgreSQL schema $SCHEMA created and permissions granted to $db_user"
    fi
fi

# Test and reload Nginx
echo "Testing Nginx configuration..."
nginx -t
echo "Reloading Nginx..."
systemctl reload nginx

echo "Domain $DOMAIN has been configured successfully!"
echo "Schema: $SCHEMA"
echo "Configuration: $CONFIG"
echo "SSL certificate: ${CERT_PATH}/${DOMAIN}"
echo ""
echo "Next steps:"
echo "1. Ensure DNS is configured: $DOMAIN should point to your server IP"
echo "2. Register the tenant in the MartialComp admin interface with:"
echo "   - Domain: $DOMAIN"
echo "   - Schema name: $SCHEMA"
echo "3. If using a custom domain, inform the tenant owner to update their DNS records"