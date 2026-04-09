#!/bin/bash
# Script pour redémarrer le serveur Django en production
# Usage: ./REDEMARRER_SERVEUR_PRODUCTION.sh

set -e

SSH_TARGET="martialcomp-production"

echo "=========================================="
echo "Redémarrage du serveur de production"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Option 1: Redémarrer Gunicorn via systemctl
echo "Tentative de redémarrage de Gunicorn..."
if ssh $SSH_TARGET "sudo systemctl restart gunicorn 2>/dev/null"; then
    info "Gunicorn redémarré avec succès via systemctl"
    
    # Vérifier le statut
    echo ""
    echo "Vérification du statut..."
    ssh $SSH_TARGET "sudo systemctl status gunicorn --no-pager -l 2>/dev/null" || true
    
    exit 0
fi

# Option 2: Redémarrer via pkill (Gunicorn en mode daemon)
warning "systemctl a échoué, tentative avec pkill (Gunicorn en mode daemon)..."
if ssh $SSH_TARGET "sudo pkill -HUP -f 'gunicorn.*config.wsgi'"; then
    info "Signal HUP envoyé à Gunicorn"
    sleep 2
    
    # Vérifier que Gunicorn tourne toujours
    if ssh $SSH_TARGET "pgrep -f 'gunicorn.*config.wsgi' > /dev/null"; then
        info "Gunicorn fonctionne correctement"
        exit 0
    else
        error "Gunicorn ne semble pas fonctionner après le redémarrage"
        exit 1
    fi
fi

# Option 3: Toucher wsgi.py pour rechargement automatique
warning "pkill a échoué, tentative avec touch wsgi.py..."
if ssh $SSH_TARGET "touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py"; then
    info "Fichier wsgi.py touché - rechargement automatique déclenché"
    echo ""
    warning "Note: Cette méthode peut prendre quelques secondes pour prendre effet"
    exit 0
fi

# Option 4: Redémarrer tous les services Django
error "Toutes les méthodes automatiques ont échoué"
echo ""
echo "Veuillez vous connecter manuellement au serveur et exécuter:"
echo ""
echo "  ssh $SSH_TARGET"
echo "  sudo pkill -HUP -f 'gunicorn.*config.wsgi'"
echo "  # OU"
echo "  touch /var/www/vhosts/martialcomp.com/httpdocs/config/wsgi.py"
echo ""
echo "Ou vérifier le nom exact du service avec:"
echo "  ps aux | grep gunicorn"
echo "  sudo pkill -HUP -f 'gunicorn.*config.wsgi'"
echo ""

exit 1
