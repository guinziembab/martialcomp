#!/bin/bash

echo "🔍 DIAGNOSTIC COMPLET - APACHE PROXY + DJANGO"
echo "=============================================="

# 1. Nettoyer tous les processus Django
echo "1. Nettoyage des processus Django en conflit..."
pkill -f "manage.py runserver"
sleep 3

echo "   Processus Django restants :"
ps aux | grep "manage.py runserver" | grep -v grep || echo "   ✅ Aucun processus Django en cours"

# 2. Vérifier les ports occupés
echo ""
echo "2. Vérification des ports..."
echo "   Port 80 :"
netstat -tlnp | grep ":80 " || echo "   ⚠️ Port 80 libre"
echo "   Port 8080 :"
netstat -tlnp | grep ":8080 " || echo "   ✅ Port 8080 libre"

# 3. Vérifier le statut Apache
echo ""
echo "3. Statut Apache..."
systemctl is-active apache2
systemctl status apache2 --no-pager -l

# 4. Vérifier la configuration Apache
echo ""
echo "4. Configuration Apache..."
apache2ctl configtest

# 5. Vérifier les sites Apache actifs
echo ""
echo "5. Sites Apache actifs..."
a2ensite --list 2>/dev/null || ls -la /etc/apache2/sites-enabled/

# 6. Vérifier les modules Apache
echo ""
echo "6. Modules Apache proxy..."
apache2ctl -M | grep proxy

# 7. Redémarrer Django proprement
echo ""
echo "7. Redémarrage Django sur port 8080..."
cd /var/www/vhosts/martialcomp.com/httpdocs
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="/var/www/vhosts/martialcomp.com/httpdocs"

# Démarrer Django en arrière-plan
nohup python manage.py runserver 127.0.0.1:8080 > /var/www/vhosts/martialcomp.com/logs/django_diagnostic.log 2>&1 &
DJANGO_PID=$!
echo "   Django PID: $DJANGO_PID"

sleep 5

# 8. Test Django interne
echo ""
echo "8. Test Django interne..."
curl -I http://127.0.0.1:8080/ 2>/dev/null | head -1 || echo "   ❌ Django ne répond pas sur 8080"

# 9. Test Apache proxy local
echo ""
echo "9. Test Apache proxy local..."
curl -I http://localhost/ 2>/dev/null | head -1 || echo "   ❌ Apache proxy ne répond pas"

# 10. Test depuis IP externe
echo ""
echo "10. Test depuis IP externe..."
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "    IP externe détectée: $EXTERNAL_IP"
curl -I http://$EXTERNAL_IP/ 2>/dev/null | head -1 || echo "   ❌ Pas de réponse depuis IP externe"

# 11. Vérifier les logs Apache
echo ""
echo "11. Logs Apache récents..."
tail -5 /var/log/apache2/error.log 2>/dev/null || echo "   Pas de logs d'erreur récents"
tail -5 /var/log/apache2/access.log 2>/dev/null || echo "   Pas de logs d'accès récents"

# 12. Vérifier les logs Django
echo ""
echo "12. Logs Django récents..."
tail -5 /var/www/vhosts/martialcomp.com/logs/django_diagnostic.log 2>/dev/null || echo "   Pas de logs Django récents"

# 13. Vérifier les règles firewall
echo ""
echo "13. Règles firewall..."
iptables -L INPUT -n | grep -E "(80|8080)" || echo "   Pas de règles firewall spécifiques pour ports 80/8080"

# 14. Vérifier la résolution DNS
echo ""
echo "14. Résolution DNS..."
dig +short martialcomp.com

echo ""
echo "🔧 ACTIONS DE CORRECTION AUTOMATIQUE"
echo "===================================="

# 15. Redémarrer Apache si nécessaire
if ! systemctl is-active --quiet apache2; then
    echo "15. Redémarrage Apache..."
    systemctl restart apache2
    sleep 3
    systemctl status apache2 --no-pager -l
else
    echo "15. Apache déjà actif"
fi

# 16. Test final
echo ""
echo "16. Test final de connectivité..."
echo "    Test local Django:"
curl -s -o /dev/null -w "    Status: %{http_code}\n" http://127.0.0.1:8080/
echo "    Test local Apache:"
curl -s -o /dev/null -w "    Status: %{http_code}\n" http://localhost/
echo "    Test externe:"
curl -s -o /dev/null -w "    Status: %{http_code}\n" http://$EXTERNAL_IP/

echo ""
echo "🎯 RÉSUMÉ DIAGNOSTIC"
echo "==================="
echo "   Django PID: $DJANGO_PID"
echo "   IP externe: $EXTERNAL_IP"
echo "   Logs Django: /var/www/vhosts/martialcomp.com/logs/django_diagnostic.log"
echo ""
echo "🌐 Tests manuels recommandés:"
echo "   curl http://martialcomp.com"
echo "   curl http://$EXTERNAL_IP" 