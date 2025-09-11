#!/bin/bash

# =============================================================================
# Nettoyage rapide du port et test de la page welcome
# =============================================================================

APP_DIR="/opt/martialcomp/app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

# Force kill du port 8000
force_kill_port() {
    log "Force kill du port 8000..."
    
    # Multiple méthodes de kill
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    pkill -9 -f "runserver" 2>/dev/null || true
    pkill -9 -f "gunicorn" 2>/dev/null || true
    
    sleep 5
    
    # Vérification
    if lsof -i:8000 >/dev/null 2>&1; then
        echo "Port encore occupé par:"
        lsof -i:8000
        error "Impossible de libérer le port"
        return 1
    else
        log "Port 8000 libéré"
    fi
}

# Redémarrage simple
simple_restart() {
    log "Redémarrage simple de Django..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    # Démarrage en arrière-plan
    python manage.py runserver 127.0.0.1:8000 > /tmp/django_quick_$TIMESTAMP.log 2>&1 &
    
    sleep 15
    
    # Vérification
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django redémarré"
    else
        error "Django n'a pas démarré"
        tail -10 /tmp/django_quick_$TIMESTAMP.log
        return 1
    fi
}

# Test rapide de la nouvelle page welcome
test_new_welcome() {
    log "Test de la nouvelle page welcome..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS RAPIDES ==="
    
    # Test Django direct
    django_code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000/" 2>/dev/null)
    echo "  Django welcome: $django_code"
    
    # Test via Nginx
    nginx_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/" 2>/dev/null)
    echo "  Nginx welcome: $nginx_code"
    
    # Test authentification
    google_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/accounts/google/login/" 2>/dev/null)
    echo "  Google OAuth: $google_code"
    
    facebook_code=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/accounts/facebook/login/" 2>/dev/null)
    echo "  Facebook OAuth: $facebook_code"
    
    echo ""
    
    if [[ "$django_code" == "200" && "$nginx_code" == "200" ]]; then
        log "✅ Nouvelle page welcome fonctionne !"
        
        # Afficher un extrait de la page pour voir si c'est la bonne
        echo ""
        echo "Extrait de la page welcome:"
        curl -s "http://127.0.0.1:8000/" | grep -i "martialcomp\|authentification\|google\|facebook" | head -5
        
    else
        error "Problème avec la page welcome"
    fi
    
    if [[ "$google_code" == "200" && "$facebook_code" == "200" ]]; then
        log "✅ Authentification sociale opérationnelle !"
    else
        error "Problème avec l'authentification sociale"
    fi
}

# Test complet final
final_complete_test() {
    log "Test complet final..."
    
    echo ""
    echo "=== TEST COMPLET FINAL ==="
    
    # Toutes les URLs importantes
    urls=(
        "https://martialcomp.com/"
        "https://martialcomp.com/fr/"
        "https://martialcomp.com/privacy/"
        "https://martialcomp.com/terms/"
        "https://martialcomp.com/accounts/google/login/"
        "https://martialcomp.com/accounts/facebook/login/"
    )
    
    success_count=0
    for url in "${urls[@]}"; do
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url ($code)"
            ((success_count++))
        else
            echo "  ❌ $url ($code)"
        fi
    done
    
    echo ""
    echo "Résultat final: $success_count/6 URLs fonctionnelles"
    
    if [ $success_count -eq 6 ]; then
        log "🎉🎉🎉 SUCCÈS TOTAL ! 🎉🎉🎉"
        echo ""
        echo "L'AUTHENTIFICATION SOCIALE MARTIALCOMP EST ENTIÈREMENT OPÉRATIONNELLE !"
        echo ""
        echo "🎨 Page welcome professionnelle restaurée"
        echo "🔐 Authentification Google/Facebook fonctionnelle"
        echo "📄 Pages légales accessibles"
        echo ""
        echo "🎯 PROCHAINE ÉTAPE: Configurer les callbacks dans les consoles API"
    else
        echo ""
        echo "Problèmes restants à résoudre:"
        for url in "${urls[@]}"; do
            code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
            if [[ ! "$code" =~ ^(200|302)$ ]]; then
                echo "  ❌ $url ($code)"
            fi
        done
    fi
}

# Script principal
main() {
    log "=== NETTOYAGE RAPIDE ET TEST ==="
    
    force_kill_port
    simple_restart
    test_new_welcome
    final_complete_test
    
    log "🎉 TEST TERMINÉ !"
    echo ""
    echo "💾 Log Django: /tmp/django_quick_$TIMESTAMP.log"
}

main "$@"