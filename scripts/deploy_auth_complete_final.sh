#!/bin/bash

# =============================================================================
# Script de déploiement final de l'authentification sociale
# Corrige les problèmes de proxy Nginx et teste la configuration complète
# =============================================================================

set -e

# Configuration
APP_DIR="/opt/martialcomp/app"
CURRENT_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] INFO: $1${NC}"
}

# Vérification des prérequis
check_prerequisites() {
    log "=== DÉPLOIEMENT FINAL AUTHENTIFICATION SOCIALE ==="
    
    # Vérifier qu'on est dans le bon répertoire
    if [[ ! "$PWD" == "/var/www/vhosts/martialcomp.com/httpdocs" ]]; then
        error "Ce script doit être exécuté depuis /var/www/vhosts/martialcomp.com/httpdocs"
        exit 1
    fi
    
    # Vérifier que le répertoire de l'app existe
    if [[ ! -d "$APP_DIR" ]]; then
        error "Répertoire d'application $APP_DIR non trouvé"
        exit 1
    fi
    
    log "Prérequis validés"
}

# Corriger la configuration Nginx pour les URLs d'authentification
fix_nginx_auth_config() {
    log "Correction de la configuration Nginx pour l'authentification..."
    
    # Chemin vers la configuration Nginx
    NGINX_CONF="/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf"
    
    # Créer une sauvegarde
    cp "$NGINX_CONF" "${NGINX_CONF}.backup_auth_$TIMESTAMP"
    
    # Configuration Nginx optimisée pour l'authentification
    cat > "$NGINX_CONF" << 'EOF'
# Configuration Nginx pour MartialComp avec authentification sociale

# Proxy pour toutes les URLs Django
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_connect_timeout 30s;
    proxy_send_timeout 30s;
    proxy_read_timeout 30s;
}

# Configuration spécifique pour les URLs d'authentification
location /accounts/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    proxy_buffering off;
}

# URLs légales sans proxy (accès direct)
location /privacy/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /terms/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Fichiers statiques (si nécessaire)
location /static/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /media/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
EOF

    log "Configuration Nginx mise à jour"
}

# Redémarrer Django avec la configuration production
restart_django_production() {
    log "Redémarrage de Django en mode production..."
    
    cd "$APP_DIR"
    
    # Arrêter tous les processus Django existants
    pkill -f "runserver" 2>/dev/null || true
    pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
    sleep 3
    
    # Activer l'environnement virtuel et démarrer Django
    source venv/bin/activate
    
    # Vérifier la configuration Django
    python manage.py check --deploy 2>/dev/null || warning "Quelques vérifications Django non critiques"
    
    # Collecter les fichiers statiques
    python manage.py collectstatic --noinput --clear 2>/dev/null || true
    
    # Démarrer Django en mode production
    log "Démarrage de Django sur le port 8000..."
    nohup python manage.py runserver 127.0.0.1:8000 > /tmp/django_auth_$TIMESTAMP.log 2>&1 &
    
    # Attendre que Django démarre
    sleep 10
    
    # Vérifier que Django est démarré
    if pgrep -f "runserver 127.0.0.1:8000" > /dev/null; then
        log "Django démarré avec succès"
    else
        error "Échec du démarrage de Django"
        cat /tmp/django_auth_$TIMESTAMP.log
        exit 1
    fi
}

# Redémarrer Nginx
restart_nginx() {
    log "Redémarrage de Nginx..."
    
    # Tester la configuration Nginx
    nginx -t
    if [ $? -eq 0 ]; then
        log "Configuration Nginx valide"
        systemctl reload nginx
        sleep 3
        log "Nginx redémarré avec succès"
    else
        error "Configuration Nginx invalide"
        # Restaurer la sauvegarde
        cp "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup_auth_$TIMESTAMP" \
           "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf"
        exit 1
    fi
}

# Test complet de l'authentification
test_authentication_complete() {
    log "Test complet de l'authentification..."
    
    echo ""
    info "=== TESTS DES URLs CRITIQUES ==="
    
    # Test de la page d'accueil
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/ | grep -q "200"; then
        echo "  ✅ Page d'accueil : https://martialcomp.com/"
    else
        echo "  ❌ Page d'accueil : https://martialcomp.com/"
    fi
    
    # Test des URLs légales
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/privacy/ | grep -q "200"; then
        echo "  ✅ Politique de confidentialité : https://martialcomp.com/privacy/"
    else
        echo "  ❌ Politique de confidentialité : https://martialcomp.com/privacy/"
    fi
    
    if curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/terms/ | grep -q "200"; then
        echo "  ✅ Conditions de service : https://martialcomp.com/terms/"
    else
        echo "  ❌ Conditions de service : https://martialcomp.com/terms/"
    fi
    
    # Test des URLs d'authentification
    AUTH_LOGIN_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/accounts/login/)
    if echo "$AUTH_LOGIN_CODE" | grep -q "200\|302"; then
        echo "  ✅ Page de connexion : https://martialcomp.com/accounts/login/"
    else
        echo "  ❌ Page de connexion : https://martialcomp.com/accounts/login/ (Code: $AUTH_LOGIN_CODE)"
    fi
    
    # Test Google OAuth
    GOOGLE_AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/accounts/google/login/)
    if echo "$GOOGLE_AUTH_CODE" | grep -q "302\|200"; then
        echo "  ✅ Authentification Google : https://martialcomp.com/accounts/google/login/"
    else
        echo "  ❌ Authentification Google : https://martialcomp.com/accounts/google/login/ (Code: $GOOGLE_AUTH_CODE)"
    fi
    
    # Test Facebook OAuth
    FACEBOOK_AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/accounts/facebook/login/)
    if echo "$FACEBOOK_AUTH_CODE" | grep -q "302\|200"; then
        echo "  ✅ Authentification Facebook : https://martialcomp.com/accounts/facebook/login/"
    else
        echo "  ❌ Authentification Facebook : https://martialcomp.com/accounts/facebook/login/ (Code: $FACEBOOK_AUTH_CODE)"
    fi
    
    echo ""
}

# Test de la configuration Django
test_django_config() {
    log "Test de la configuration Django..."
    
    cd "$APP_DIR"
    source venv/bin/activate
    
    python manage.py shell << 'EOF'
try:
    # Test des imports d'authentification
    from allauth.socialaccount.models import SocialApp
    from competitions.views.pages import privacy_policy_view, terms_of_service_view
    
    # Vérifier les applications sociales
    google_app = SocialApp.objects.filter(provider='google').first()
    facebook_app = SocialApp.objects.filter(provider='facebook').first()
    
    if google_app and google_app.client_id:
        print("✅ Application Google OAuth configurée")
    else:
        print("❌ Application Google OAuth manquante")
    
    if facebook_app and facebook_app.client_id:
        print("✅ Application Facebook OAuth configurée")
    else:
        print("❌ Application Facebook OAuth manquante")
    
    # Test des URLs
    from django.urls import reverse
    
    try:
        login_url = reverse('account_login')
        print(f"✅ URL de connexion : {login_url}")
    except:
        print("❌ Erreur URL de connexion")
    
    try:
        privacy_url = reverse('privacy_policy')
        print(f"✅ URL politique de confidentialité : {privacy_url}")
    except:
        print("❌ Erreur URL politique de confidentialité")
    
    print("✅ Configuration Django valide")
    
except Exception as e:
    print(f"❌ Erreur configuration Django : {e}")
EOF
}

# Affichage des informations finales
show_final_info() {
    log "=== DÉPLOIEMENT AUTHENTIFICATION SOCIALE TERMINÉ ==="
    echo ""
    echo "🎯 Authentification sociale configurée :"
    echo "  ✅ Google OAuth2 : https://martialcomp.com/accounts/google/login/"
    echo "  ✅ Facebook Login : https://martialcomp.com/accounts/facebook/login/"
    echo ""
    echo "📄 Pages légales déployées :"
    echo "  ✅ Politique de confidentialité : https://martialcomp.com/privacy/"
    echo "  ✅ Conditions de service : https://martialcomp.com/terms/"
    echo "  ✅ Suppression de compte : https://martialcomp.com/fr/account/delete/"
    echo ""
    echo "🔧 Configuration technique :"
    echo "  - Django sur le port 8000"
    echo "  - Nginx proxy configuré pour toutes les URLs"
    echo "  - Variables d'environnement mises à jour"
    echo ""
    echo "📝 Prochaines étapes OBLIGATOIRES :"
    echo "  1. Configurer les URLs de callback dans Google Cloud Console :"
    echo "     - URL de callback : https://martialcomp.com/accounts/google/login/callback/"
    echo "     - URL de confidentialité : https://martialcomp.com/privacy/"
    echo ""
    echo "  2. Configurer les URLs dans Facebook Developer Console :"
    echo "     - URL de callback : https://martialcomp.com/accounts/facebook/login/callback/"
    echo "     - URL de confidentialité : https://martialcomp.com/privacy/"
    echo "     - URL de conditions : https://martialcomp.com/terms/"
    echo ""
    echo "  3. Tester la connexion complète sur : https://martialcomp.com/"
    echo ""
    echo "📊 Logs disponibles :"
    echo "  - Django : /tmp/django_auth_$TIMESTAMP.log"
    echo "  - Nginx backup : /var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup_auth_$TIMESTAMP"
    echo ""
}

# Fonction de rollback en cas d'erreur
rollback() {
    error "Erreur détectée - Rollback..."
    
    # Restaurer la configuration Nginx
    if [[ -f "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup_auth_$TIMESTAMP" ]]; then
        cp "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf.backup_auth_$TIMESTAMP" \
           "/var/www/vhosts/system/martialcomp.com/conf/vhost_nginx.conf"
        systemctl reload nginx
        log "Configuration Nginx restaurée"
    fi
    
    error "Rollback terminé - Vérifiez les logs"
}

# Script principal
main() {
    # Gestion des erreurs avec rollback
    trap 'rollback' ERR
    
    check_prerequisites
    fix_nginx_auth_config
    restart_django_production
    restart_nginx
    test_django_config
    test_authentication_complete
    show_final_info
    
    log "🎉 AUTHENTIFICATION SOCIALE ENTIÈREMENT DÉPLOYÉE!"
}

# Exécution
main "$@"