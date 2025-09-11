#!/bin/bash

# Script de configuration alternative pour Ionos - Port 80 non disponible
# À exécuter sur le serveur Ionos 212.227.78.104

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/www/vhosts/martialcomp.com/backups/port_alternative_$TIMESTAMP"

echo "=== Configuration MartialComp - Port Alternatif IONOS ==="
echo "Timestamp: $TIMESTAMP"

# Créer répertoire de sauvegarde
mkdir -p "$BACKUP_DIR"

# SOLUTION 1: Démarrage Django sur port 8080
setup_django_port_8080() {
    echo "1. Configuration Django sur port 8080..."
    
    cd /var/www/vhosts/martialcomp.com/httpdocs
    
    # Sauvegarder la configuration actuelle
    cp -r config/ "$BACKUP_DIR/"
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Arrêter les processus Django existants
    pkill -f "manage.py runserver" || true
    pkill -f "gunicorn" || true
    sleep 3
    
    # Créer script de démarrage pour port 8080
    cat > start_django_8080.sh << 'EOF'
#!/bin/bash
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

# Variables d'environnement
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH=/var/www/vhosts/martialcomp.com/httpdocs

# Créer les logs si nécessaire
mkdir -p /var/www/vhosts/martialcomp.com/logs/
touch /var/www/vhosts/martialcomp.com/logs/django.log
chown www-data:www-data /var/www/vhosts/martialcomp.com/logs/django.log

# Démarrer Django sur port 8080 (accessible depuis l'extérieur)
echo "Démarrage Django sur port 8080..."
python manage.py runserver 0.0.0.0:8080 > /var/www/vhosts/martialcomp.com/logs/django_8080.log 2>&1 &

echo "Django démarré sur http://martialcomp.com:8080"
echo "Logs: /var/www/vhosts/martialcomp.com/logs/django_8080.log"
EOF

    chmod +x start_django_8080.sh
    echo "Script créé: start_django_8080.sh"
}

# SOLUTION 2: Configuration avec Gunicorn + Systemd
setup_gunicorn_service() {
    echo "2. Configuration service Gunicorn..."
    
    # Installer gunicorn si nécessaire
    source /var/www/vhosts/martialcomp.com/httpdocs/venv/bin/activate
    pip install gunicorn
    
    # Créer configuration gunicorn
    cat > /var/www/vhosts/martialcomp.com/httpdocs/gunicorn.conf.py << 'EOF'
# Configuration Gunicorn pour MartialComp - Port alternatif
bind = "0.0.0.0:8080"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 60
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logs
accesslog = "/var/www/vhosts/martialcomp.com/logs/gunicorn_access.log"
errorlog = "/var/www/vhosts/martialcomp.com/logs/gunicorn_error.log"
loglevel = "info"

# Performance
preload_app = True
daemon = True
pidfile = "/var/www/vhosts/martialcomp.com/gunicorn.pid"

# Répertoire de travail
chdir = "/var/www/vhosts/martialcomp.com/httpdocs"
EOF

    # Créer service systemd
    cat > /etc/systemd/system/martialcomp.service << 'EOF'
[Unit]
Description=MartialComp Gunicorn Application Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
Environment="PATH=/var/www/vhosts/martialcomp.com/httpdocs/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings"
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/venv/bin/gunicorn --config gunicorn.conf.py config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    # Activer le service
    systemctl daemon-reload
    systemctl enable martialcomp
    echo "Service systemd créé: martialcomp.service"
}

# SOLUTION 3: Proxy Nginx vers Django
setup_nginx_proxy() {
    echo "3. Configuration proxy Nginx..."
    
    # Sauvegarder configuration nginx existante
    cp /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf "$BACKUP_DIR/"
    
    # Nouvelle configuration proxy
    cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf << 'EOF'
# Proxy vers Django sur port 8080
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Buffers
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 16 4k;
    proxy_busy_buffers_size 8k;
    
    # Headers pour HTTPS
    proxy_redirect off;
}

# Fichiers statiques directs (optionnel)
location /static/ {
    alias /var/www/vhosts/martialcomp.com/httpdocs/static/;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
}

location /media/ {
    alias /var/www/vhosts/martialcomp.com/httpdocs/media/;
    expires 7d;
    add_header Cache-Control "public, max-age=604800";
}
EOF

    echo "Configuration Nginx proxy créée"
}

# SOLUTION 4: Sous-domaine dédié
setup_subdomain() {
    echo "4. Préparation sous-domaine app.martialcomp.com..."
    
    cat > setup_subdomain_instructions.txt << 'EOF'
=== Configuration Sous-domaine dans Plesk ===

1. Dans Plesk, aller à "Domaines" -> "Ajouter un sous-domaine"
2. Créer: app.martialcomp.com
3. Document Root: /var/www/vhosts/martialcomp.com/app/
4. Dans les paramètres du sous-domaine:
   - Redirection -> Port personnalisé: 8080
   - OU Proxy pass: http://127.0.0.1:8080

Alternative: Configuration DNS
1. Ajouter enregistrement DNS:
   - Type: A
   - Nom: app
   - Valeur: IP serveur (212.227.78.104)
2. L'URL sera: http://app.martialcomp.com:8080

Alternative: CNAME
1. Ajouter enregistrement CNAME:
   - Nom: app
   - Valeur: martialcomp.com
EOF

    echo "Instructions sous-domaine créées: setup_subdomain_instructions.txt"
}

# Test de connectivité
test_connectivity() {
    echo "5. Tests de connectivité..."
    
    # Vérifier si port 8080 est libre
    if netstat -tlnp | grep :8080; then
        echo "⚠️  Port 8080 déjà utilisé"
        netstat -tlnp | grep :8080
    else
        echo "✅ Port 8080 disponible"
    fi
    
    # Tester autres ports disponibles
    for port in 8081 8082 8083 3000 9000; do
        if ! netstat -tlnp | grep :$port > /dev/null; then
            echo "✅ Port $port disponible"
        else
            echo "❌ Port $port occupé"
        fi
    done
}

# Firewall - ouvrir port 8080
configure_firewall() {
    echo "6. Configuration firewall pour port 8080..."
    
    # Ouvrir port 8080
    iptables -I INPUT -p tcp --dport 8080 -j ACCEPT
    
    # Sauvegarder règles firewall
    if command -v iptables-save >/dev/null 2>&1; then
        iptables-save > /etc/iptables/rules.v4
        echo "✅ Port 8080 ouvert et sauvegardé"
    else
        echo "⚠️  Port 8080 ouvert mais règles non sauvegardées"
        echo "   Exécutez manuellement: iptables-save > /etc/iptables/rules.v4"
    fi
}

# Exécution principale
main() {
    echo "Début de la configuration..."
    
    # Créer répertoire logs si nécessaire
    mkdir -p /var/www/vhosts/martialcomp.com/logs/
    chown -R www-data:www-data /var/www/vhosts/martialcomp.com/logs/
    
    # Tests préliminaires
    test_connectivity
    
    # Configurations alternatives
    setup_django_port_8080
    setup_gunicorn_service
    setup_nginx_proxy
    setup_subdomain
    configure_firewall
    
    echo ""
    echo "=== CONFIGURATION TERMINÉE ==="
    echo ""
    echo "🚀 MÉTHODES DE DÉMARRAGE:"
    echo "1. Django simple: ./start_django_8080.sh"
    echo "2. Service systemd: systemctl start martialcomp"
    echo "3. Manuel: cd /var/www/vhosts/martialcomp.com/httpdocs && source venv/bin/activate && python manage.py runserver 0.0.0.0:8080"
    echo ""
    echo "🌐 URLS D'ACCÈS:"
    echo "- Direct: http://martialcomp.com:8080"
    echo "- Via proxy: https://martialcomp.com (si nginx configuré)"
    echo "- Sous-domaine: http://app.martialcomp.com:8080 (après config Plesk)"
    echo ""
    echo "📋 ÉTAPES SUIVANTES:"
    echo "1. Tester une méthode de démarrage"
    echo "2. Vérifier accès depuis l'extérieur"
    echo "3. Configurer sous-domaine dans Plesk si souhaité"
    echo "4. Optionnel: Configurer SSL pour port 8080"
    echo ""
    echo "💾 Sauvegarde: $BACKUP_DIR"
}

# Exécuter le script principal
main

echo "Script terminé avec succès !" 