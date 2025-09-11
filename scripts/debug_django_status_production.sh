#!/bin/bash

################################################################################
# DEBUG DJANGO STATUS - DIAGNOSTIC PRODUCTION
################################################################################

echo "🔍 DEBUG DJANGO STATUS - DIAGNOSTIC PRODUCTION"
echo "==============================================="
echo "Date: $(date)"
echo ""

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

cd "$PROD_DIR"

# Activation de l'environnement virtuel
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
fi

echo "🔍 DIAGNOSTIC COMPLET DU SERVEUR"
echo "================================"

echo "📋 1. Processus Django en cours..."
ps aux | grep -E "(python|django|runserver)" | grep -v grep || echo "Aucun processus Django détecté"

echo ""
echo "📋 2. Ports en écoute..."
netstat -tlnp 2>/dev/null | grep ":8000" || echo "Port 8000 non en écoute"

echo ""
echo "📋 3. Logs Django récents..."
if [ -f "/tmp/django_registrations_fix.log" ]; then
    echo "--- Logs django_registrations_fix.log ---"
    tail -20 /tmp/django_registrations_fix.log
else
    echo "Fichier de logs django_registrations_fix.log non trouvé"
fi

echo ""
echo "📋 4. Autres logs Django..."
find /tmp -name "*django*.log" -mtime -1 | head -3 | while read log_file; do
    echo "--- Logs $(basename $log_file) ---"
    tail -10 "$log_file" 2>/dev/null
    echo ""
done

echo ""
echo "🔧 TENTATIVE DE REDÉMARRAGE MANUEL"
echo "=================================="

# Arrêter tous les processus Django
echo "📋 Arrêt de tous les processus Django..."
pkill -f "python.*manage.py" 2>/dev/null || true
pkill -f "runserver" 2>/dev/null || true
pkill -f "django" 2>/dev/null || true
sleep 5

echo "📋 Vérification que tous les processus sont arrêtés..."
if pgrep -f "runserver" > /dev/null; then
    echo "⚠️ Des processus Django sont encore actifs"
    ps aux | grep -E "(runserver|django)" | grep -v grep
else
    echo "✅ Tous les processus Django arrêtés"
fi

echo ""
echo "📋 Test de la configuration Django..."
export DJANGO_SETTINGS_MODULE=config.settings

python3 manage.py check 2>&1 | head -10

echo ""
echo "🚀 REDÉMARRAGE DJANGO AVEC DEBUGGING"
echo "===================================="

# Redémarrer Django avec plus de verbosité
echo "📋 Démarrage Django avec logs détaillés..."

LOG_FILE="/tmp/django_manual_restart_$(date +%Y%m%d_%H%M%S).log"

# Démarrer Django en mode verbose
nohup python3 manage.py runserver 0.0.0.0:8000 --verbosity=2 > "$LOG_FILE" 2>&1 &
DJANGO_PID=$!

echo "📋 Django PID: $DJANGO_PID"
echo "📋 Logs dans: $LOG_FILE"

# Attendre et surveiller le démarrage
echo "📋 Surveillance du démarrage (30 secondes)..."

for i in {1..30}; do
    echo -n "."
    sleep 1
    
    # Vérifier si le processus existe encore
    if ! kill -0 $DJANGO_PID 2>/dev/null; then
        echo ""
        echo "❌ Le processus Django s'est arrêté prématurément"
        echo "📋 Logs d'erreur:"
        cat "$LOG_FILE"
        exit 1
    fi
    
    # Vérifier si le port est ouvert
    if netstat -tln 2>/dev/null | grep -q ":8000"; then
        echo ""
        echo "✅ Django écoute sur le port 8000"
        break
    fi
done

echo ""

# Vérification finale du statut
if pgrep -f "runserver" > /dev/null; then
    echo "✅ Django est actif"
    
    # Afficher les premières lignes des logs
    echo "📋 Logs de démarrage:"
    head -20 "$LOG_FILE"
    
else
    echo "❌ Django ne semble pas actif"
    echo "📋 Logs complets:"
    cat "$LOG_FILE"
fi

echo ""
echo "🧪 TESTS DE CONNECTIVITÉ"
echo "========================"

echo "📋 Test de connectivité locale..."

# Test avec plusieurs méthodes
echo "  Test 1: curl avec timeout court..."
timeout 5 curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://localhost:8000/" 2>/dev/null || echo "Échec curl"

echo "  Test 2: telnet sur port 8000..."
timeout 3 telnet localhost 8000 2>/dev/null | head -2 || echo "Échec telnet"

echo "  Test 3: netcat sur port 8000..."
timeout 3 nc -z localhost 8000 && echo "Port 8000 accessible" || echo "Port 8000 inaccessible"

echo ""
echo "📋 Test d'une URL spécifique..."
for attempt in {1..3}; do
    echo "  Tentative $attempt: test URL practitioners..."
    
    response=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/club/practitioners/" 2>/dev/null)
    
    if [ "$response" != "000" ] && [ "$response" != "" ]; then
        echo "  ✅ Réponse HTTP: $response"
        break
    else
        echo "  ⚠️ Tentative $attempt échouée (code: $response)"
        sleep 5
    fi
done

echo ""
echo "🎯 RÉSUMÉ DU DIAGNOSTIC"
echo "======================="

if pgrep -f "runserver" > /dev/null && netstat -tln 2>/dev/null | grep -q ":8000"; then
    echo "✅ DJANGO FONCTIONNE CORRECTEMENT"
    echo ""
    echo "📋 URLs à tester dans le navigateur:"
    echo "  • https://martialcomp.com/fr/competitions/club/practitioners/"
    echo "  • https://martialcomp.com/fr/competitions/club/registrations/"
    echo "  • https://martialcomp.com/fr/competitions/club/practitioners/add/"
    echo ""
    echo "🔗 Si les tests curl échouent mais Django fonctionne,"
    echo "   cela peut être normal (firewall, proxy, etc.)"
    echo "   Testez directement dans le navigateur web."
else
    echo "⚠️ PROBLÈME DÉTECTÉ AVEC DJANGO"
    echo ""
    echo "📋 Actions recommandées:"
    echo "  1. Vérifier les logs: tail -f $LOG_FILE"
    echo "  2. Vérifier la configuration réseau"
    echo "  3. Redémarrer manuellement: python3 manage.py runserver 0.0.0.0:8000"
fi

echo ""
echo "📋 Logs actifs pour monitoring:"
echo "  • Logs Django: tail -f $LOG_FILE"
echo "  • Logs système: tail -f /var/log/syslog"
echo ""
echo "Date: $(date)"