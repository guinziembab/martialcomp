#!/bin/bash

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs
sudo find apps -name "*.pyc" -delete
sudo rm -rf apps/competitions/__pycache__ apps/competitions/views/__pycache__
sudo pkill -f gunicorn
sleep 2
cd /var/www/vhosts/martialcomp.com
sudo -u www-data /var/www/vhosts/martialcomp.com/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8888 --access-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log --error-logfile /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log --log-level info --chdir /var/www/vhosts/martialcomp.com/httpdocs --daemon config.wsgi:application
sudo systemctl restart apache2
echo "✓ Redémarré"
EOF