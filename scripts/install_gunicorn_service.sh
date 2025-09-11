#!/bin/bash

# Script d'installation du service systemd pour gunicorn
echo "Installation du service systemd pour gunicorn..."

# Créer le fichier de service
cat > /etc/systemd/system/martialcomp-gunicorn.service << 'EOF'
[Unit]
Description=Gunicorn instance to serve MartialComp
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/vhosts/martialcomp.com/httpdocs
Environment="PATH=/var/www/vhosts/martialcomp.com/httpdocs/.venv/bin"
ExecStart=/var/www/vhosts/martialcomp.com/httpdocs/.venv/bin/gunicorn \
    --bind 127.0.0.1:8002 \
    --workers 2 \
    --timeout 30 \
    --access-logfile logs/gunicorn_access.log \
    --error-logfile logs/gunicorn_error.log \
    --log-level info \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Recharger systemd
systemctl daemon-reload

# Activer le service
systemctl enable martialcomp-gunicorn.service

# Démarrer le service
systemctl start martialcomp-gunicorn.service

echo "Service martialcomp-gunicorn installe et active."
echo "Pour gerer le service:"
echo "  systemctl start martialcomp-gunicorn.service"
echo "  systemctl stop martialcomp-gunicorn.service"
echo "  systemctl restart martialcomp-gunicorn.service"
echo "  systemctl status martialcomp-gunicorn.service" 