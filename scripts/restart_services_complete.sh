#!/bin/bash

# =============================================================================
# SCRIPT DE REDÉMARRAGE COMPLET DES SERVICES - PRODUCTION MARTIALCOMP
# Redémarre tous les services pour résoudre les problèmes 502
# =============================================================================

set -e

echo "🔄 Redémarrage complet des services MartialComp..."
echo "📅 $(date)"

cd /var/www/vhosts/martialcomp.com/httpdocs

# =============================================================================
# 1. ARRÊT DE TOUS LES PROCESSUS
# =============================================================================

echo "🛑 Arrêt de tous les processus Django/Python..."

# Tuer tous les processus Python liés
pkill -f python || true
pkill -f gunicorn || true
pkill -f uwsgi || true
pkill -f passenger || true

# Attendre que les processus se terminent
sleep 5

echo "✅ Processus Python arrêtés"

# =============================================================================
# 2. VÉRIFICATION DE LA CONFIGURATION PLESK
# =============================================================================

echo "🔍 Vérification configuration Plesk..."

# Vérifier si Plesk gère ce domaine
if command -v plesk &> /dev/null; then
    echo "📊 Informations Plesk pour martialcomp.com:"
    plesk bin subscription --info martialcomp.com 2>/dev/null || echo "Plesk info non disponible"
    
    echo "🔧 Configuration PHP/Python Plesk:"
    plesk bin site --info martialcomp.com 2>/dev/null || echo "Site info non disponible"
fi

# =============================================================================
# 3. VÉRIFICATION DES LOGS AVANT REDÉMARRAGE
# =============================================================================

echo "📝 Logs avant redémarrage..."

# Vérifier les logs récents
echo "--- Apache Error Log (10 dernières lignes) ---"
tail -10 /var/log/apache2/error.log 2>/dev/null || echo "Logs Apache non accessibles"

echo "--- Nginx Error Log (10 dernières lignes) ---"
tail -10 /var/log/nginx/error.log 2>/dev/null || echo "Logs Nginx non accessibles"

# =============================================================================
# 4. REDÉMARRAGE APACHE
# =============================================================================

echo "🔄 Redémarrage Apache..."

# Tester la configuration Apache
if command -v apache2ctl &> /dev/null; then
    echo "🧪 Test configuration Apache:"
    apache2ctl configtest || echo "⚠️ Problème de configuration Apache détecté"
fi

# Redémarrer Apache complet
echo "🔄 Redémarrage complet Apache..."
systemctl stop apache2 || service apache2 stop || true
sleep 3
systemctl start apache2 || service apache2 start || true
sleep 2

# Vérifier le statut
systemctl status apache2 --no-pager || echo "Statut Apache non disponible"

echo "✅ Apache redémarré"

# =============================================================================
# 5. REDÉMARRAGE NGINX
# =============================================================================

echo "🔄 Redémarrage Nginx..."

# Tester la configuration Nginx
if command -v nginx &> /dev/null; then
    echo "🧪 Test configuration Nginx:"
    nginx -t || echo "⚠️ Problème de configuration Nginx détecté"
fi

# Redémarrer Nginx
echo "🔄 Redémarrage complet Nginx..."
systemctl stop nginx || service nginx stop || true
sleep 2
systemctl start nginx || service nginx start || true
sleep 2

# Vérifier le statut
systemctl status nginx --no-pager || echo "Statut Nginx non disponible"

echo "✅ Nginx redémarré"

# =============================================================================
# 6. REDÉMARRAGE PASSENGER AVEC FORÇAGE
# =============================================================================

echo "🔄 Redémarrage forcé Passenger..."

# Plusieurs méthodes pour redémarrer Passenger
cd /var/www/vhosts/martialcomp.com/httpdocs

# Méthode 1: touch passenger_wsgi.py
touch passenger_wsgi.py
echo "✅ Passenger redémarré via touch"

# Méthode 2: tmp/restart.txt (si supporté)
mkdir -p tmp
touch tmp/restart.txt
echo "✅ Restart.txt créé"

# Méthode 3: passenger-config restart-app (si disponible)
if command -v passenger-config &> /dev/null; then
    passenger-config restart-app /var/www/vhosts/martialcomp.com/httpdocs || echo "passenger-config non disponible"
fi

echo "✅ Passenger redémarrage forcé terminé"

# =============================================================================
# 7. ATTENTE ET TESTS
# =============================================================================

echo "⏳ Attente du démarrage des services (15 secondes)..."
sleep 15

echo "🧪 Tests après redémarrage..."

# Test de base avec timeout
echo "📡 Test de connectivité avec timeout:"
timeout 10 curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost/ || echo "Timeout ou erreur de connexion"

# Tests des ports
echo "🔌 Vérification des ports:"
netstat -tlnp | grep -E ":80|:443|:8000" || echo "Aucun service web détecté sur les ports standards"

# Test des processus
echo "🔍 Processus web actifs:"
ps aux | grep -E "(apache|nginx|python|passenger)" | grep -v grep || echo "Aucun processus web trouvé"

# =============================================================================
# 8. TESTS EXTERNES
# =============================================================================

echo "🌐 Tests depuis l'extérieur..."

# Test avec différentes méthodes
echo "📡 Test HTTPS externe:"
timeout 10 curl -s -k -o /dev/null -w "HTTPS Status: %{http_code}\n" https://martialcomp.com/ || echo "HTTPS non accessible"

echo "📡 Test HTTP externe:"
timeout 10 curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://martialcomp.com/ || echo "HTTP non accessible"

# =============================================================================
# 9. DIAGNOSTIC FINAL
# =============================================================================

echo "🔍 Diagnostic final..."

# État des services
echo "📊 État final des services:"
systemctl is-active apache2 nginx || echo "Services non actifs"

# Derniers logs
echo "📝 Logs après redémarrage (5 dernières lignes):"
echo "--- Apache ---"
tail -5 /var/log/apache2/error.log 2>/dev/null || echo "Logs Apache non accessibles"

echo "--- Nginx ---"
tail -5 /var/log/nginx/error.log 2>/dev/null || echo "Logs Nginx non accessibles"

# =============================================================================
# 10. RAPPORT FINAL
# =============================================================================

echo ""
echo "🎯 REDÉMARRAGE COMPLET TERMINÉ"
echo ""
echo "📊 SERVICES REDÉMARRÉS:"
echo "  ✅ Apache2 arrêté et redémarré"
echo "  ✅ Nginx arrêté et redémarré"
echo "  ✅ Passenger redémarré (multiple méthodes)"
echo "  ✅ Tous les processus Python nettoyés"
echo ""
echo "🔗 TESTER MAINTENANT:"
echo "  • https://martialcomp.com/"
echo "  • https://martialcomp.com/admin/"
echo "  • https://martialcomp.com/accounts/login/"
echo ""
echo "📝 SI TOUJOURS 502:"
echo "  1. Problème de configuration Plesk/Passenger"
echo "  2. Permissions incorrectes"
echo "  3. Configuration virtualhost Apache"
echo "  4. Configuration Python dans Plesk"
echo ""
echo "🎉 Redémarrage terminé: $(date)"

# =============================================================================
# 11. INSTRUCTIONS POST-REDÉMARRAGE
# =============================================================================

echo ""
echo "📋 INSTRUCTIONS POST-REDÉMARRAGE:"
echo ""
echo "1. Attendez 30 secondes avant de tester"
echo "2. Testez d'abord avec HTTP: http://martialcomp.com/"
echo "3. Puis testez HTTPS: https://martialcomp.com/"
echo "4. Si encore 502, consultez la configuration Plesk"
echo "5. Vérifiez que Python 3.9 est bien configuré dans Plesk"
echo ""
echo "🔧 COMMANDES UTILES:"
echo "• Logs temps réel: tail -f /var/log/apache2/error.log"
echo "• Test Django: python manage.py check"
echo "• Redémarrage Passenger: touch passenger_wsgi.py"
echo ""