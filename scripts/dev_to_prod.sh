#!/bin/bash

# ============================================================================
# Script de Synchronisation Développement → Production MartialComp
# ============================================================================

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage coloré
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# ================================
# CONFIGURATION
# ================================

PROD_SERVER="martialcomp.com"
PROD_USER="deploy"
LOCAL_BRANCH="main"
REMOTE_BRANCH="main"
PROJECT_DIR="/home/deploy/martialcomp"

echo "🚀 SYNCHRONISATION DEV → PRODUCTION"
echo "===================================="
echo "Serveur : $PROD_SERVER"
echo "Branche : $LOCAL_BRANCH → $REMOTE_BRANCH"
echo "Date    : $(date)"
echo "===================================="

# ================================
# VÉRIFICATIONS LOCALES
# ================================

log_info "Vérifications du développement local..."

# Vérifier qu'on est dans un repo Git
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Ce répertoire n'est pas un repository Git"
    exit 1
fi

# Vérifier la branche courante
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
    log_warning "Branche courante: $CURRENT_BRANCH (attendue: $LOCAL_BRANCH)"
    read -p "Continuer avec la branche $CURRENT_BRANCH? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Changement vers la branche $LOCAL_BRANCH..."
        git checkout "$LOCAL_BRANCH"
    else
        LOCAL_BRANCH="$CURRENT_BRANCH"
    fi
fi

# Vérifier s'il y a des modifications non commitées
if ! git diff --quiet || ! git diff --staged --quiet; then
    log_warning "Modifications non commitées détectées"
    git status --porcelain
    
    read -p "Commiter automatiquement? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Message de commit: " COMMIT_MSG
        if [ -z "$COMMIT_MSG" ]; then
            COMMIT_MSG="Auto-commit before production deployment $(date +%Y-%m-%d_%H-%M)"
        fi
        
        git add .
        git commit -m "$COMMIT_MSG"
        log_success "Modifications commitées"
    else
        log_error "Veuillez commiter vos modifications avant le déploiement"
        exit 1
    fi
fi

log_success "Vérifications locales terminées"

# ================================
# TESTS LOCAUX
# ================================

log_info "Exécution des tests locaux..."

# Test de syntaxe Python
if command -v python &> /dev/null; then
    log_info "Vérification de la syntaxe Python..."
    if find . -name "*.py" -exec python -m py_compile {} \; 2>/dev/null; then
        log_success "Syntaxe Python OK"
    else
        log_error "Erreurs de syntaxe Python détectées"
        exit 1
    fi
fi

# Test Django check
if [ -f "manage.py" ]; then
    log_info "Vérification Django..."
    if python manage.py check --settings=config.settings_minimal 2>/dev/null; then
        log_success "Django check OK"
    else
        log_warning "Problèmes détectés par Django check"
        read -p "Continuer malgré les avertissements? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Tests unitaires (si disponibles)
if [ -d "tests" ] || find . -name "test_*.py" | grep -q .; then
    log_info "Exécution des tests unitaires..."
    read -p "Exécuter les tests? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if python manage.py test --settings=config.settings_minimal 2>/dev/null; then
            log_success "Tests unitaires réussis"
        else
            log_error "Tests unitaires échoués"
            read -p "Continuer malgré les échecs? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
fi

log_success "Tests locaux terminés"

# ================================
# PUSH VERS GIT
# ================================

log_info "Synchronisation avec Git..."

# Récupérer les dernières modifications
git fetch origin

# Vérifier s'il y a des conflits potentiels
if ! git merge-base --is-ancestor "origin/$REMOTE_BRANCH" HEAD; then
    log_warning "La branche locale n'est pas à jour avec origin/$REMOTE_BRANCH"
    log_info "Tentative de rebase..."
    
    if git rebase "origin/$REMOTE_BRANCH"; then
        log_success "Rebase réussi"
    else
        log_error "Conflits lors du rebase. Résolvez les conflits et relancez le script"
        exit 1
    fi
fi

# Push vers le repository
log_info "Push vers origin/$REMOTE_BRANCH..."
if git push origin "$LOCAL_BRANCH:$REMOTE_BRANCH"; then
    log_success "Code poussé vers Git"
else
    log_error "Erreur lors du push"
    exit 1
fi

COMMIT_HASH=$(git rev-parse --short HEAD)
log_success "Commit $COMMIT_HASH synchronisé"

# ================================
# VÉRIFICATION DE LA CONNEXION SERVEUR
# ================================

log_info "Vérification de la connexion au serveur de production..."

if ! ssh -o ConnectTimeout=10 "$PROD_USER@$PROD_SERVER" "echo 'Connexion OK'" >/dev/null 2>&1; then
    log_error "Impossible de se connecter au serveur $PROD_SERVER"
    log_info "Vérifiez :"
    log_info "  - Votre connexion Internet"
    log_info "  - Vos clés SSH"
    log_info "  - L'adresse du serveur"
    exit 1
fi

log_success "Connexion au serveur OK"

# ================================
# DÉPLOIEMENT SUR PRODUCTION
# ================================

log_info "Déploiement sur le serveur de production..."

# Afficher un résumé avant déploiement
echo
echo "📋 RÉSUMÉ DU DÉPLOIEMENT :"
echo "  🏠 Serveur    : $PROD_SERVER"
echo "  👤 Utilisateur: $PROD_USER"
echo "  🌿 Branche    : $LOCAL_BRANCH"
echo "  📝 Commit     : $COMMIT_HASH"
echo "  📅 Date       : $(date)"
echo

read -p "Confirmer le déploiement? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Déploiement annulé"
    exit 0
fi

# Exécution du script de déploiement sur le serveur
log_info "Exécution du déploiement sur $PROD_SERVER..."

ssh "$PROD_USER@$PROD_SERVER" << 'EOF'
# Variables pour le script distant
export BRANCH=main
export ENVIRONMENT=production

# Aller dans le répertoire du projet
cd /home/deploy/martialcomp

# Exécuter le script de déploiement
if [ -f "deployment/deploy.sh" ]; then
    echo "🚀 Lancement du déploiement..."
    bash deployment/deploy.sh
else
    echo "❌ Script de déploiement non trouvé"
    exit 1
fi
EOF

DEPLOY_EXIT_CODE=$?

if [ $DEPLOY_EXIT_CODE -eq 0 ]; then
    log_success "Déploiement réussi sur production !"
else
    log_error "Erreur lors du déploiement (code: $DEPLOY_EXIT_CODE)"
    exit 1
fi

# ================================
# VÉRIFICATIONS POST-DÉPLOIEMENT
# ================================

log_info "Vérifications post-déploiement..."

# Test de connectivité HTTPS
sleep 15  # Attendre que l'application soit complètement redémarrée

if curl -f -s "https://$PROD_SERVER/health/" >/dev/null 2>&1; then
    log_success "Site accessible en HTTPS"
else
    log_warning "Site non accessible immédiatement (peut nécessiter quelques minutes)"
fi

# Vérification de la version déployée
log_info "Vérification de la version déployée..."
DEPLOYED_COMMIT=$(ssh "$PROD_USER@$PROD_SERVER" "cd $PROJECT_DIR && git rev-parse --short HEAD")

if [ "$DEPLOYED_COMMIT" = "$COMMIT_HASH" ]; then
    log_success "Version correcte déployée: $DEPLOYED_COMMIT"
else
    log_warning "Version déployée ($DEPLOYED_COMMIT) différente de la version locale ($COMMIT_HASH)"
fi

# ================================
# NOTIFICATIONS
# ================================

log_info "Envoi des notifications..."

# Notification Slack (si webhook configuré)
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
if [ ! -z "$SLACK_WEBHOOK" ]; then
    curl -X POST -H 'Content-type: application/json' \
         --data "{\"text\":\"🚀 MartialComp déployé en production\n📝 Commit: $COMMIT_HASH\n🕒 $(date)\"}" \
         "$SLACK_WEBHOOK" 2>/dev/null || true
    log_success "Notification Slack envoyée"
fi

# Notification par email (si configuré)
if command -v mail &> /dev/null && [ ! -z "${ADMIN_EMAIL:-}" ]; then
    echo "Déploiement MartialComp réussi le $(date). Commit: $COMMIT_HASH" | \
    mail -s "Déploiement MartialComp Production" "$ADMIN_EMAIL" 2>/dev/null || true
    log_success "Notification email envoyée"
fi

# ================================
# RAPPORT FINAL
# ================================

echo
echo "=============================================="
echo "🎉 DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !"
echo "=============================================="
echo "📅 Date         : $(date)"
echo "📝 Commit local : $COMMIT_HASH"
echo "🚀 Commit prod  : $DEPLOYED_COMMIT"
echo "🌐 URL          : https://$PROD_SERVER"
echo "=============================================="

echo
echo "📋 Prochaines étapes recommandées :"
echo "  1. 🧪 Tester les fonctionnalités critiques"
echo "  2. 👥 Informer les utilisateurs pilotes"
echo "  3. 📊 Surveiller les logs et performances"
echo "  4. 📱 Tester sur différents navigateurs/devices"

echo
echo "🔧 Commandes utiles :"
echo "  Logs production    : ssh $PROD_USER@$PROD_SERVER 'tail -f /home/deploy/logs/django.log'"
echo "  Status services    : ssh $PROD_USER@$PROD_SERVER '/home/deploy/monitor.sh'"
echo "  Rollback (si pb)   : ssh $PROD_USER@$PROD_SERVER 'cd $PROJECT_DIR && git checkout HEAD~1 && bash deployment/deploy.sh'"

echo "=============================================="

# Sauvegarder l'historique du déploiement
echo "$(date +%Y-%m-%d_%H:%M:%S) - Commit: $COMMIT_HASH - Status: SUCCESS" >> .deployment_history

log_success "Synchronisation développement → production terminée !"

# Proposer d'ouvrir le site
read -p "Ouvrir le site en production? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v xdg-open &> /dev/null; then
        xdg-open "https://$PROD_SERVER"
    elif command -v open &> /dev/null; then
        open "https://$PROD_SERVER"
    else
        log_info "Ouvrez manuellement : https://$PROD_SERVER"
    fi
fi