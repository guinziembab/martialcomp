#!/bin/bash
# Script to set up a wildcard certificate for *.martialcomp.com
# Usage: sudo ./setup_wildcard_cert.sh martialcomp.com

set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Check arguments
if [ $# -ne 1 ]; then
    echo "Usage: $0 domain.com"
    echo "Example: $0 martialcomp.com"
    exit 1
fi

DOMAIN=$1
CERT_PATH="/etc/letsencrypt/live"
WEBROOT="/var/www/html"

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "Certbot is not installed. Installing..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    echo "Certbot installed successfully."
fi

# Make sure webroot exists
mkdir -p "$WEBROOT"

# Check existing certificates
echo "Checking existing certificates..."
if [ -d "${CERT_PATH}/${DOMAIN}" ]; then
    echo "Certificate for ${DOMAIN} already exists. Checking wildcard..."
    
    if certbot certificates | grep -q "\*.${DOMAIN}"; then
        echo "Wildcard certificate for *.${DOMAIN} already exists."
        
        # Check expiration
        EXPIRY=$(openssl x509 -in "${CERT_PATH}/${DOMAIN}/cert.pem" -noout -enddate | cut -d= -f2)
        EXPIRY_EPOCH=$(date -d "${EXPIRY}" +%s)
        NOW_EPOCH=$(date +%s)
        DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
        
        echo "Certificate expires in ${DAYS_LEFT} days: ${EXPIRY}"
        
        if [ "${DAYS_LEFT}" -lt 30 ]; then
            echo "Certificate is expiring soon. Renewing..."
            certbot renew --force-renewal
        else
            echo "Certificate is still valid. No action needed."
            exit 0
        fi
    else
        echo "Wildcard certificate not found for *.${DOMAIN}. Requesting new certificate..."
    fi
else
    echo "No certificate found for ${DOMAIN}. Requesting new certificate..."
fi

# Inform user about DNS verification
echo ""
echo "======================================================================"
echo "WARNING: This script will request a wildcard certificate using DNS verification."
echo "You will need to create a DNS TXT record for your domain."
echo "The script will guide you through the process."
echo "======================================================================"
echo ""
echo "Ready to proceed? (y/n)"
read -r proceed

if [ "$proceed" != "y" ]; then
    echo "Aborted by user."
    exit 1
fi

# Request wildcard certificate
echo "Requesting wildcard certificate for ${DOMAIN} and *.${DOMAIN}..."
certbot certonly --manual --preferred-challenges dns \
    -d "${DOMAIN}" -d "*.${DOMAIN}" \
    --agree-tos --email admin@martialcomp.com

# Check if successful
if [ -d "${CERT_PATH}/${DOMAIN}" ]; then
    echo "Certificate generated successfully."
    
    # Configure Nginx for the wildcard domain
    NGINX_CONFIG="/etc/nginx/sites-available/martialcomp-wildcard"
    NGINX_ENABLED="/etc/nginx/sites-enabled/martialcomp-wildcard"
    
    echo "Creating Nginx configuration for wildcard domains..."
    cat > "${NGINX_CONFIG}" << EOF
# Wildcard configuration for *.${DOMAIN}
server {
    listen 80;
    server_name *.${DOMAIN};
    
    # Redirection HTTP vers HTTPS
    location / {
        return 301 https://\$host\$request_uri;
    }
    
    # Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root ${WEBROOT};
    }
}

server {
    listen 443 ssl;
    server_name *.${DOMAIN};
    
    # Certificats SSL
    ssl_certificate ${CERT_PATH}/${DOMAIN}/fullchain.pem;
    ssl_certificate_key ${CERT_PATH}/${DOMAIN}/privkey.pem;
    
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
    
    # Extract tenant schema from subdomain
    set \$tenant_schema "";
    if (\$host ~* ^([^.]+)\.${DOMAIN}$) {
        set \$tenant_schema \$1;
    }
    
    # Proxy pour l'application Django
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Tenant-Schema \$tenant_schema;
        
        # Timeout settings
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF
    
    # Create symbolic link
    ln -sf "${NGINX_CONFIG}" "${NGINX_ENABLED}"
    
    # Test Nginx configuration
    echo "Testing Nginx configuration..."
    nginx -t
    
    # Reload Nginx
    echo "Reloading Nginx..."
    systemctl reload nginx
    
    echo "==============================================================="
    echo "Wildcard certificate for ${DOMAIN} and *.${DOMAIN} is now set up!"
    echo "Nginx has been configured to handle all subdomains."
    echo "Certificate location: ${CERT_PATH}/${DOMAIN}"
    echo "Certificate will be automatically renewed by certbot."
    echo "==============================================================="
else
    echo "Failed to generate certificate."
    exit 1
fi

# Set up automatic renewal check
RENEWAL_SCRIPT="/usr/local/bin/check_ssl_expiry.sh"
echo "Creating renewal check script..."
cat > "${RENEWAL_SCRIPT}" << EOF
#!/bin/bash
# Script to check SSL certificate expiration

DOMAIN="${DOMAIN}"
DAYS_WARNING=30
EMAIL="admin@martialcomp.com"

# Check wildcard certificate
CERT_PATH="${CERT_PATH}/${DOMAIN}/cert.pem"
if [ -f "\${CERT_PATH}" ]; then
    EXPIRY=\$(openssl x509 -in "\${CERT_PATH}" -noout -enddate | cut -d= -f2)
    EXPIRY_EPOCH=\$(date -d "\${EXPIRY}" +%s)
    NOW_EPOCH=\$(date +%s)
    DAYS_LEFT=\$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
    
    if [ "\${DAYS_LEFT}" -lt "\${DAYS_WARNING}" ]; then
        echo "SSL Certificate Warning: The certificate for ${DOMAIN} and *.${DOMAIN} will expire in \${DAYS_LEFT} days on \${EXPIRY}" | mail -s "SSL Certificate Expiry Warning" "\${EMAIL}"
        echo "Certificate for ${DOMAIN} will expire in \${DAYS_LEFT} days on \${EXPIRY}"
    else
        echo "Certificate for ${DOMAIN} is valid for \${DAYS_LEFT} more days (expires on \${EXPIRY})"
    fi
else
    echo "Certificate file not found: \${CERT_PATH}"
    exit 1
fi
EOF

chmod +x "${RENEWAL_SCRIPT}"

# Add to crontab if not already there
if ! crontab -l | grep -q "${RENEWAL_SCRIPT}"; then
    (crontab -l 2>/dev/null; echo "0 8 * * * ${RENEWAL_SCRIPT}") | crontab -
    echo "Added renewal check to crontab. It will run daily at 8am."
fi

echo "Setup complete!"