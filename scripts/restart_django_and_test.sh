#!/bin/bash

# =============================================================================
# Script de redémarrage Django et test complet
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

# Nettoyer les processus Django existants
cleanup_django() {
    log "Nettoyage des processus Django..."
    
    # Arrêter tous les processus Django/Python
    pkill -f "runserver" 2>/dev/null || true
    pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
    pkill -f "python.*manage.py" 2>/dev/null || true
    
    sleep 5
    
    # Vérifier qu'ils sont bien arrêtés
    if pgrep -f "runserver\|gunicorn.*config.wsgi" >/dev/null; then
        warning "Processus Django encore actifs, force kill..."
        pkill -9 -f "runserver\|gunicorn.*config.wsgi" 2>/dev/null || true
        sleep 3
    fi
    
    log "Processus Django nettoyés"
}

# Redémarrer Django proprement
restart_django_clean() {
    log "Redémarrage propre de Django..."
    
    cd "$APP_DIR"
    
    # Activer l'environnement virtuel
    source venv/bin/activate
    
    # Vérifier la configuration avant de démarrer
    log "Vérification de la configuration Django..."
    python manage.py check
    
    if [ $? -ne 0 ]; then
        error "Erreurs de configuration Django détectées"
        return 1
    fi
    
    log "Configuration Django valide"
    
    # Démarrer Django en arrière-plan
    log "Démarrage de Django sur 127.0.0.1:8000..."
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_restart_$TIMESTAMP.log 2>&1 &
    
    # Attendre le démarrage
    sleep 15
    
    # Vérifier que Django est démarré
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django démarré avec succès (PID: $(pgrep -f 'runserver 127.0.0.1:8000'))"
    else
        error "Échec du démarrage de Django"
        echo "Contenu du log :"
        cat /tmp/django_restart_$TIMESTAMP.log
        return 1
    fi
}

# Test de connectivité Django
test_django_connectivity() {
    log "Test de connectivité Django..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS DJANGO ==="
    
    # Test 1: Connectivité basique
    if curl -s http://127.0.0.1:8000/ >/dev/null 2>&1; then
        echo "  ✅ Django répond"
    else
        echo "  ❌ Django ne répond pas"
        return 1
    fi
    
    # Test 2: Code de réponse
    code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null)
    echo "  Code de réponse: $code"
    
    # Test 3: URLs spécifiques Django
    django_urls=(
        "/"
        "/fr/"
        "/privacy/"
        "/terms/"
        "/accounts/login/"
    )
    
    for url in "${django_urls[@]}"; do
        code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000$url" 2>/dev/null)
        echo "  Django $url : $code"
    done
    
    echo ""
}

# Corriger la configuration Nginx simple
fix_nginx_simple() {
    log "Configuration Nginx simple..."
    
    # Sauvegarder
    cp /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf \
       /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup_restart_$TIMESTAMP
    
    # Configuration Nginx ultra-simple
    cat > /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf << 'EOF'
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
}
EOF

    # Test et rechargement Nginx
    nginx -t
    if [ $? -eq 0 ]; then
        log "Configuration Nginx valide"
        systemctl reload nginx
        log "Nginx rechargé"
    else
        error "Configuration Nginx invalide"
        return 1
    fi
}

# Test final complet
test_complete_chain() {
    log "Test complet de la chaîne Django → Nginx..."
    
    sleep 5
    
    echo ""
    echo "=== TESTS CHAÎNE COMPLÈTE ==="
    
    # Test Django direct
    django_code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ 2>/dev/null)
    echo "  Django direct: $django_code"
    
    # Test via Nginx HTTPS
    nginx_code=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ 2>/dev/null)
    echo "  Nginx HTTPS: $nginx_code"
    
    # Test URLs d'authentification
    echo ""
    echo "URLs d'authentification:"
    auth_urls=(
        "https://martialcomp.com/accounts/login/"
        "https://martialcomp.com/accounts/google/login/"
        "https://martialcomp.com/accounts/facebook/login/"
    )
    
    for url in "${auth_urls[@]}"; do
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url ($code)"
        else
            echo "  ❌ $url ($code)"
        fi
    done
    
    # Test pages légales
    echo ""
    echo "Pages légales:"
    legal_urls=(
        "https://martialcomp.com/privacy/"
        "https://martialcomp.com/terms/"
    )
    
    for url in "${legal_urls[@]}"; do
        code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
        if [[ "$code" =~ ^(200|302)$ ]]; then
            echo "  ✅ $url ($code)"
        else
            echo "  ❌ $url ($code)"
        fi
    done
    
    echo ""
}

# Afficher les informations finales
show_final_status() {
    log "🎉 REDÉMARRAGE ET TEST TERMINÉS!"
    echo ""
    echo "📊 Statut final:"
    
    # Django
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        echo "  ✅ Django actif (PID: $(pgrep -f 'runserver 127.0.0.1:8000'))"
    else
        echo "  ❌ Django inactif"
    fi
    
    # Nginx
    if systemctl is-active --quiet nginx; then
        echo "  ✅ Nginx actif"
    else
        echo "  ❌ Nginx inactif"
    fi
    
    # Test de connectivité finale
    final_test=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ 2>/dev/null)
    echo "  Test final https://martialcomp.com/ : $final_test"
    
    echo ""
    echo "🔐 URLs d'authentification à tester:"
    echo "  - https://martialcomp.com/accounts/login/"
    echo "  - https://martialcomp.com/accounts/google/login/"
    echo "  - https://martialcomp.com/accounts/facebook/login/"
    echo ""
    echo "📄 Pages légales:"
    echo "  - https://martialcomp.com/privacy/"
    echo "  - https://martialcomp.com/terms/"
    echo ""
    echo "💾 Logs et sauvegardes:"
    echo "  - Django: /tmp/django_restart_$TIMESTAMP.log"
    echo "  - Nginx: /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup_restart_$TIMESTAMP"
}

# Script principal
main() {
    log "=== REDÉMARRAGE DJANGO ET TEST COMPLET ==="
    
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        cd /var/www/vhosts/martialcomp.com/httpdocs
    fi
    
    cleanup_django
    restart_django_clean
    test_django_connectivity
    fix_nginx_simple
    test_complete_chain
    show_final_status
}

main "$@"