#!/bin/bash

echo "=== DEBUG PASSENGER/PLESK ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Vérifier les logs d'erreur Plesk
echo "1. Logs d'erreur Plesk..."
if [ -f /var/www/vhosts/martialcomp.com/logs/error_log ]; then
    echo "Dernières erreurs :"
    tail -30 /var/www/vhosts/martialcomp.com/logs/error_log
else
    echo "Logs alternatifs :"
    ls -la /var/www/vhosts/martialcomp.com/logs/
    tail -30 /var/log/apache2/error.log | grep martialcomp
fi

# 2. Vérifier la configuration Apache générée par Plesk
echo ""
echo "2. Configuration Apache active..."
if [ -f /var/www/vhosts/system/martialcomp.com/conf/httpd.conf ]; then
    echo "=== httpd.conf ==="
    grep -A5 -B5 "passenger\|wsgi\|python" /var/www/vhosts/system/martialcomp.com/conf/httpd.conf
fi

# 3. Vérifier si Passenger est configuré
echo ""
echo "3. Module Passenger dans Apache..."
apache2ctl -M 2>/dev/null | grep -i passenger || echo "Module Passenger non trouvé"

# 4. Créer un script WSGI de debug
echo ""
echo "4. Création d'un passenger_wsgi.py avec debug..."
cp passenger_wsgi.py passenger_wsgi.py.backup
cat > passenger_wsgi.py << 'EOF'
import sys
import os

# Logger pour debug
def log_debug(msg):
    with open('/var/www/vhosts/martialcomp.com/httpdocs/passenger_debug.log', 'a') as f:
        f.write(f"{msg}\n")

try:
    log_debug("=== Passenger Start ===")
    log_debug(f"Python: {sys.executable}")
    log_debug(f"Path: {sys.path}")
    
    # Configuration
    sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
    
    # Charger l'environnement
    env_file = '/var/www/vhosts/martialcomp.com/httpdocs/.env.production'
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip()
    
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
    
    log_debug("Environment loaded")
    
    # Importer Django
    import django
    django.setup()
    
    log_debug("Django setup complete")
    
    # Créer l'application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    
    log_debug("Application created successfully")
    
except Exception as e:
    log_debug(f"ERROR: {str(e)}")
    import traceback
    log_debug(traceback.format_exc())
    
    # Application d'erreur de fallback
    def application(environ, start_response):
        status = '500 Internal Server Error'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [b'Error loading Django application. Check passenger_debug.log']
EOF

touch passenger_debug.log
chown www-data:www-data passenger_wsgi.py passenger_debug.log
chmod 644 passenger_wsgi.py passenger_debug.log

# 5. Forcer le rechargement
echo ""
echo "5. Touch du fichier pour forcer le rechargement..."
touch tmp/restart.txt 2>/dev/null || mkdir -p tmp && touch tmp/restart.txt

# 6. Attendre et vérifier le log de debug
echo ""
echo "6. Test et vérification du log de debug..."
sleep 2
curl -s https://martialcomp.com > /dev/null
sleep 1

if [ -f passenger_debug.log ]; then
    echo "=== Log de debug Passenger ==="
    cat passenger_debug.log
fi

# 7. Alternative : utiliser mod_wsgi au lieu de Passenger
echo ""
echo "7. Vérification de mod_wsgi comme alternative..."
apache2ctl -M 2>/dev/null | grep -i wsgi || echo "mod_wsgi non installé"

echo ""
echo "=== ACTIONS SUGGÉRÉES ==="
echo ""
echo "Si Passenger ne fonctionne pas, options :"
echo "1. Installer mod_wsgi : apt-get install libapache2-mod-wsgi-py3"
echo "2. Utiliser Gunicorn avec un proxy Apache"
echo "3. Configurer Passenger dans Plesk UI > Paramètres Apache & nginx"