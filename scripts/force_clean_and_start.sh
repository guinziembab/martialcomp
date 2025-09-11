#!/bin/bash

# =============================================================================
# Script de nettoyage forcé et redémarrage Django
# =============================================================================

set -e

APP_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING: $1${NC}"
}

# Diagnostic du port 8000
diagnose_port_8000() {
    log "Diagnostic du port 8000..."
    
    echo ""
    echo "=== DIAGNOSTIC PORT 8000 ==="
    
    # Qui utilise le port 8000
    echo "Processus utilisant le port 8000:"
    lsof -i :8000 2>/dev/null || echo "  Aucun processus trouvé avec lsof"
    
    echo ""
    echo "Processus netstat:"
    netstat -tulpn | grep :8000 || echo "  Aucun processus trouvé avec netstat"
    
    echo ""
    echo "Tous les processus Python/Django:"
    ps aux | grep -E "(python|django|runserver|gunicorn)" | grep -v grep || echo "  Aucun processus Python trouvé"
    
    echo ""
}

# Nettoyage forcé de tous les processus
force_cleanup() {
    log "Nettoyage forcé de tous les processus..."
    
    # Méthode 1: Kill par nom de processus
    pkill -9 -f "runserver" 2>/dev/null || true
    pkill -9 -f "gunicorn" 2>/dev/null || true
    pkill -9 -f "python.*manage.py" 2>/dev/null || true
    pkill -9 -f "django" 2>/dev/null || true
    
    sleep 3
    
    # Méthode 2: Kill par port
    if lsof -t -i:8000 >/dev/null 2>&1; then
        log "Processus trouvé sur le port 8000, kill forcé..."
        kill -9 $(lsof -t -i:8000) 2>/dev/null || true
        sleep 3
    fi
    
    # Méthode 3: Kill par PID spécifique
    pids=$(ps aux | grep -E "(runserver|python.*manage)" | grep -v grep | awk '{print $2}' | tr '\n' ' ')
    if [[ -n "$pids" ]]; then
        log "PIDs Django trouvés: $pids"
        kill -9 $pids 2>/dev/null || true
        sleep 3
    fi
    
    log "Nettoyage forcé terminé"
}

# Vérification que le port est libre
verify_port_free() {
    log "Vérification que le port 8000 est libre..."
    
    if lsof -i :8000 >/dev/null 2>&1; then
        error "Port 8000 encore occupé"
        echo "Processus restants:"
        lsof -i :8000
        return 1
    else
        log "Port 8000 libre"
    fi
}

# Démarrage Django avec vérifications
start_django_verified() {
    log "Démarrage Django avec vérifications..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Test rapide de la configuration
    python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
print('✅ Configuration Django OK')
"
    
    if [ $? -ne 0 ]; then
        error "Problème de configuration Django"
        return 1
    fi
    
    # Démarrer Django en mode détaché
    log "Lancement de Django..."
    python manage.py runserver 127.0.0.1:8000 > /tmp/django_force_$TIMESTAMP.log 2>&1 &
    
    # Capturer le PID
    DJANGO_PID=$!
    log "Django démarré avec PID: $DJANGO_PID"
    
    # Attendre et vérifier
    sleep 10
    
    if kill -0 $DJANGO_PID 2>/dev/null; then
        log "Django fonctionne (PID: $DJANGO_PID)"
    else
        error "Django s'est arrêté"
        echo "Log de démarrage:"
        cat /tmp/django_force_$TIMESTAMP.log
        return 1
    fi
}

# Test immédiat de connectivité
test_immediate_connectivity() {
    log "Test immédiat de connectivité..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS IMMÉDIATS ==="
    
    # Test 1: Ping simple
    if curl -s http://127.0.0.1:8000/ >/dev/null 2>&1; then
        echo "  ✅ Django répond"
    else
        echo "  ❌ Django ne répond pas"
        return 1
    fi
    
    # Test 2: Code de réponse
    code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null)
    echo "  Code de réponse Django: $code"
    
    # Test 3: Via Nginx (si configuré)
    nginx_code=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ 2>/dev/null || echo "failed")
    echo "  Code de réponse Nginx: $nginx_code"
    
    echo ""
}

# Configuration Nginx finale
configure_nginx_final() {
    log "Configuration Nginx finale..."
    
    # Configuration ultra-simple pour éviter les erreurs
    cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf << 'EOF'
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}
EOF

    # Test et rechargement
    if nginx -t 2>/dev/null; then
        systemctl reload nginx
        log "Nginx reconfiguré"
    else
        warning "Problème de configuration Nginx"
    fi
}

# Test final des URLs d'authentification
test_auth_final() {
    log "Test final des URLs d'authentification..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS AUTHENTIFICATION FINALE ==="
    
    # URLs critiques à tester
    urls=(
        "https://martialcomp.com/"
        "https://martialcomp.com/fr/"
        "https://martialcomp.com/privacy/"
        "https://martialcomp.com/terms/"
        "https://martialcomp.com/accounts/login/"
        "https://martialcomp.com/accounts/google/login/"
        "https://martialcomp.com/accounts/facebook/login/"
    )
    
    for url in "${urls[@]}"; do
        code=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "timeout")
        
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url ($code)"
        else
            echo "  ❌ $url ($code)"
        fi
    done
    
    echo ""
}

# Résumé final
show_final_summary() {
    log "🎉 NETTOYAGE FORCÉ ET REDÉMARRAGE TERMINÉS!"
    echo ""
    echo "📊 Statut final:"
    
    # Vérifier Django
    if pgrep -f "runserver 127.0.0.1:8000" >/dev/null; then
        echo "  ✅ Django actif (PID: $(pgrep -f 'runserver 127.0.0.1:8000'))"
    else
        echo "  ❌ Django inactif"
    fi
    
    # Test de connectivité
    django_test=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null || echo "failed")
    echo "  Test Django direct: $django_test"
    
    nginx_test=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ 2>/dev/null || echo "failed")
    echo "  Test via Nginx: $nginx_test"
    
    echo ""
    echo "🎯 L'authentification sociale devrait maintenant fonctionner:"
    echo "  - Google: https://martialcomp.com/accounts/google/login/"
    echo "  - Facebook: https://martialcomp.com/accounts/facebook/login/"
    echo ""
    echo "💾 Log Django: /tmp/django_force_$TIMESTAMP.log"
}

# Script principal
main() {
    log "=== NETTOYAGE FORCÉ ET REDÉMARRAGE DJANGO ==="
    
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        cd /var/www/vhosts/martialcomp.com/httpdocs
    fi
    
    diagnose_port_8000
    force_cleanup
    verify_port_free
    start_django_verified
    test_immediate_connectivity
    configure_nginx_final
    test_auth_final
    show_final_summary
}

main "$@"