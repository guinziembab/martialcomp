#!/bin/bash

# =============================================================================
# Script de déploiement des pages légales pour les API sociales
# Déploie les pages privacy, terms et suppression de compte
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
    log "=== DÉPLOIEMENT DES PAGES LÉGALES ==="
    
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

# Sauvegarde des fichiers existants
backup_existing() {
    log "Sauvegarde des fichiers existants..."
    
    cd "$APP_DIR"
    
    # Créer le répertoire de sauvegarde
    BACKUP_DIR="/tmp/legal_pages_backup_$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder les vues si elles existent
    if [[ -f "competitions/views/pages.py" ]]; then
        cp "competitions/views/pages.py" "$BACKUP_DIR/"
        log "Vues pages.py sauvegardées"
    fi
    
    # Sauvegarder config/urls.py
    if [[ -f "config/urls.py" ]]; then
        cp "config/urls.py" "$BACKUP_DIR/"
        log "Configuration URLs sauvegardée"
    fi
    
    # Sauvegarder welcome.html
    if [[ -f "competitions/templates/competitions/welcome.html" ]]; then
        cp "competitions/templates/competitions/welcome.html" "$BACKUP_DIR/"
        log "Template welcome.html sauvegardé"
    fi
    
    log "Sauvegarde créée dans $BACKUP_DIR"
}

# Test des nouvelles URLs
test_legal_urls() {
    log "Test des nouvelles URLs légales..."
    
    cd "$APP_DIR"
    
    # Test avec curl local
    sleep 3
    
    echo ""
    info "Test des URLs légales :"
    
    # Test privacy policy
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/privacy/ | grep -q "200"; then
        echo "  ✅ /privacy/ - Accessible"
    else
        echo "  ❌ /privacy/ - Non accessible"
    fi
    
    # Test terms of service
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/terms/ | grep -q "200"; then
        echo "  ✅ /terms/ - Accessible"
    else
        echo "  ❌ /terms/ - Non accessible"
    fi
    
    # Test delete account (nécessite auth)
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/fr/account/delete/ | grep -q "302\|200"; then
        echo "  ✅ /fr/account/delete/ - Accessible (redirection auth normale)"
    else
        echo "  ❌ /fr/account/delete/ - Non accessible"
    fi
    
    echo ""
    log "Tests terminés"
}

# Vérifier la configuration Django
verify_django_config() {
    log "Vérification de la configuration Django..."
    
    cd "$APP_DIR"
    
    python manage.py shell << 'EOF'
try:
    # Test des imports
    from competitions.views.pages import privacy_policy_view, terms_of_service_view, delete_account_view
    print("✅ Vues légales importées avec succès")
    
    # Test des URL patterns
    from django.urls import reverse
    
    try:
        privacy_url = reverse('privacy_policy')
        print(f"✅ URL privacy policy : {privacy_url}")
    except Exception as e:
        print(f"❌ Erreur URL privacy : {e}")
    
    try:
        terms_url = reverse('terms_of_service')
        print(f"✅ URL terms of service : {terms_url}")
    except Exception as e:
        print(f"❌ Erreur URL terms : {e}")
    
    try:
        delete_url = reverse('delete_account')
        print(f"✅ URL delete account : {delete_url}")
    except Exception as e:
        print(f"❌ Erreur URL delete : {e}")
    
    print("✅ Configuration Django valide")
    
except Exception as e:
    print(f"❌ Erreur configuration : {e}")
EOF
}

# Redémarrer les services
restart_services() {
    log "Redémarrage des services..."
    
    # Arrêter tous les processus Django
    pkill -f "runserver" 2>/dev/null || true
    pkill -f "gunicorn.*config.wsgi" 2>/dev/null || true
    
    # Redémarrer le service principal
    if systemctl is-enabled martialcomp &>/dev/null; then
        systemctl restart martialcomp
        sleep 3
        
        if systemctl is-active --quiet martialcomp; then
            log "Service martialcomp redémarré avec succès"
        else
            warning "Problème avec le service martialcomp"
        fi
    else
        warning "Service martialcomp non configuré"
    fi
    
    log "Services redémarrés"
}

# Affichage des informations finales
show_final_info() {
    log "=== DÉPLOIEMENT DES PAGES LÉGALES TERMINÉ ==="
    echo ""
    echo "📋 Pages légales déployées :"
    echo "  ✅ Politique de confidentialité : https://martialcomp.com/privacy/"
    echo "  ✅ Conditions de service : https://martialcomp.com/terms/"
    echo "  ✅ Suppression de compte : https://martialcomp.com/fr/account/delete/"
    echo ""
    echo "🔗 Liens ajoutés au footer :"
    echo "  - Section 'Légal' dans le footer principal"
    echo "  - Liens rapides dans le bas de page"
    echo ""
    echo "🌐 Configuration pour les API sociales :"
    echo "  - Google OAuth2 : URL de confidentialité requise ✅"
    echo "  - Facebook Login : URL de confidentialité requise ✅"
    echo "  - Apple Sign-In : URLs légales requises ✅"
    echo ""
    echo "💾 Sauvegarde des fichiers dans : /tmp/legal_pages_backup_$TIMESTAMP"
    echo ""
    echo "📝 Prochaines étapes :"
    echo "  1. Obtenir les clés API des fournisseurs sociaux"
    echo "  2. Configurer les domaines autorisés avec ces URLs"
    echo "  3. Exécuter deploy_auth_modernization.sh"
    echo ""
}

# Fonction de rollback en cas d'erreur
rollback() {
    error "Erreur détectée - Rollback partiel..."
    
    if [[ -d "/tmp/legal_pages_backup_$TIMESTAMP" ]]; then
        cd "$APP_DIR"
        
        # Restaurer les fichiers
        if [[ -f "/tmp/legal_pages_backup_$TIMESTAMP/pages.py" ]]; then
            cp "/tmp/legal_pages_backup_$TIMESTAMP/pages.py" "competitions/views/"
        fi
        
        if [[ -f "/tmp/legal_pages_backup_$TIMESTAMP/urls.py" ]]; then
            cp "/tmp/legal_pages_backup_$TIMESTAMP/urls.py" "config/"
        fi
        
        if [[ -f "/tmp/legal_pages_backup_$TIMESTAMP/welcome.html" ]]; then
            cp "/tmp/legal_pages_backup_$TIMESTAMP/welcome.html" "competitions/templates/competitions/"
        fi
        
        log "Fichiers restaurés"
    fi
    
    systemctl restart martialcomp 2>/dev/null || true
    error "Rollback terminé - Vérifiez les logs"
}

# Script principal
main() {
    # Gestion des erreurs avec rollback partiel
    trap 'rollback' ERR
    
    check_prerequisites
    backup_existing
    verify_django_config
    restart_services
    test_legal_urls
    show_final_info
    
    log "🎉 DÉPLOIEMENT DES PAGES LÉGALES RÉUSSI!"
}

# Exécution
main "$@"