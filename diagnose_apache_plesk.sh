#!/bin/bash
# Script pour diagnostiquer le problème Apache/Plesk

echo "=== DIAGNOSTIC APACHE/PLESK ==="
echo ""

# 1. Vérifier la configuration Plesk
echo "1. Configuration Plesk pour martialcomp.com:"
ssh martialcomp-production "ls -la /var/www/vhosts/system/martialcomp.com/conf/"

echo ""
echo "2. Contenu de vhost_ssl.conf:"
ssh martialcomp-production "cat /var/www/vhosts/system/martialcomp.com/conf/vhost_ssl.conf | grep -A 10 -B 10 'ProxyPass'"

echo ""
echo "3. Vérifier les logs Apache récents:"
ssh martialcomp-production "sudo tail -20 /var/www/vhosts/system/martialcomp.com/logs/error_log"

echo ""
echo "4. Vérifier si Apache module proxy est activé:"
ssh martialcomp-production "apache2ctl -M | grep proxy"

echo ""
echo "5. Test direct sur Gunicorn (sans proxy):"
ssh martialcomp-production "curl -X POST http://127.0.0.1:8888/fr/ -H 'Host: martialcomp.com' -d '' -w '\nStatus: %{http_code}\n' -s | tail -5"