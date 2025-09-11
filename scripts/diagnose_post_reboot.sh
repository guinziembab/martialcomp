#!/bin/bash

# Script de diagnostic post-reboot pour résoudre le 502 persistant
echo "🔍 DIAGNOSTIC POST-REBOOT 502 PERSISTANT"
echo "========================================"

# Se connecter au serveur
ssh root@martialcomp.com << 'EOF'

echo "📋 DIAGNOSTIC COMPLET SYSTÈME"
echo "============================="

# 1. Vérifier les logs de reboot
echo "🔍 1. LOGS POST-REBOOT:"
if [ -f /tmp/martialcomp_reboot.log ]; then
    echo "📄 Contenu martialcomp_reboot.log:"
    cat /tmp/martialcomp_reboot.log
else
    echo "❌ Fichier martialcomp_reboot.log non trouvé"
fi

echo ""
echo "🔍 2. STATUT SERVICES SYSTÈME:"
systemctl status nginx --no-pager -l
echo ""
systemctl status ssh --no-pager -l

echo ""
echo "🔍 3. PROCESSUS DJANGO:"
ps aux | grep manage.py
ps aux | grep python3

echo ""
echo "🔍 4. PORTS EN ÉCOUTE:"
netstat -tlnp | grep :8000
netstat -tlnp | grep :80

echo ""
echo "🔍 5. LOGS NGINX:"
tail -20 /var/log/nginx/error.log

echo ""
echo "🔍 6. TEST DJANGO MANUEL:"
cd /var/www/vhosts/martialcomp.com/httpdocs

if [ -d "venv" ]; then
    source venv/bin/activate
    export DJANGO_SETTINGS_MODULE=config.settings
    
    echo "🧪 Django check:"
    python3 manage.py check
    
    echo ""
    echo "🧪 Test import Django:"
    python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from competitions.views import pages
print('✅ Import Django réussi')
"
else
    echo "❌ Environnement virtuel non trouvé"
fi

echo ""
echo "🔍 7. CONFIGURATION NGINX:"
nginx -t
echo ""
echo "📄 Configuration nginx martialcomp:"
if [ -f /etc/nginx/sites-available/martialcomp ]; then
    cat /etc/nginx/sites-available/martialcomp
elif [ -f /etc/nginx/conf.d/martialcomp.conf ]; then
    cat /etc/nginx/conf.d/martialcomp.conf
else
    echo "❌ Configuration nginx martialcomp non trouvée"
    echo "📄 Configurations disponibles:"
    ls -la /etc/nginx/sites-available/
    ls -la /etc/nginx/conf.d/
fi

echo ""
echo "🔍 8. ESPACE DISQUE ET PERMISSIONS:"
df -h /
ls -la /var/www/vhosts/martialcomp.com/httpdocs/

echo ""
echo "========================================"
echo "🎯 DÉMARRAGE MANUEL DJANGO"
echo "========================================"

cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings

echo "🚀 Tentative démarrage Django..."
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_manual_start.log 2>&1 &

sleep 10

echo "🧪 Test connexion locale:"
curl -I http://localhost:8000/ 2>/dev/null | head -3

echo ""
echo "📋 PID processus Django démarrés:"
ps aux | grep manage.py

echo ""
echo "🔍 Si échec, logs Django:"
if [ -f /tmp/django_manual_start.log ]; then
    echo "📄 Contenu django_manual_start.log:"
    cat /tmp/django_manual_start.log
fi

echo ""
echo "========================================"
echo "📊 RÉSUMÉ DIAGNOSTIC TERMINÉ"
echo "========================================"

EOF

echo ""
echo "🌐 TEST URLS EXTERNES:"
echo "====================="

echo "🔍 Test URL principale:"
curl -I https://martialcomp.com/ 2>/dev/null | head -3

echo ""
echo "🔍 Test URL française:"  
curl -I https://martialcomp.com/fr/ 2>/dev/null | head -3

echo ""
echo "🔍 Test URL anglaise:"
curl -I https://martialcomp.com/en/ 2>/dev/null | head -3

echo ""
echo "📋 ANALYSE TERMINÉE"
echo "Si 502 persiste, problème probable:"
echo "1. Configuration nginx incorrecte"
echo "2. Django ne démarre pas du tout"
echo "3. Port 8000 bloqué/occupé"
echo "4. Permissions fichiers"