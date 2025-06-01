#!/bin/bash

# ============================================================================
# SCRIPT DE TEST POUR LE DÉPLOIEMENT MARTIALCOMP
# ============================================================================
# Ce script vérifie les prérequis et identifie les problèmes potentiels
# avant d'exécuter le déploiement complet
# ============================================================================

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🧪 TEST DU SCRIPT DE DÉPLOIEMENT MARTIALCOMP"
echo "============================================="

# ================================
# 1. VÉRIFICATION DES VARIABLES D'ENVIRONNEMENT
# ================================

log_info "1. Vérification des variables d'environnement..."

# Variables par défaut
export DB_HOST="${DB_HOST:-martialcomp-do-user-22855185-0.f.db.ondigitalocean.com}"
export DB_PORT="${DB_PORT:-25060}"
export DB_NAME="${DB_NAME:-defaultdb}"
export DB_USER="${DB_USER:-doadmin}"
export DOMAIN="${DOMAIN:-martialcomp.com}"
export SERVER_IP="${SERVER_IP:-165.232.94.248}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-bertrand.guinziemba@gmail.com}"

if [ -z "$DB_PASSWORD" ]; then
    log_error "Variable DB_PASSWORD manquante"
    echo "Utilisez: export DB_PASSWORD='YOUR_DB_PASSWORD'"
    exit 1
else
    log_success "DB_PASSWORD définie"
fi

log_success "Variables d'environnement validées"

# ================================
# 2. VÉRIFICATION DE L'ACCÈS ROOT
# ================================

log_info "2. Vérification de l'accès root..."

if [ "$EUID" -ne 0 ]; then
    log_error "Ce script de test doit être exécuté en tant que root"
    echo "Utilisez: sudo ./test_deployment_script.sh"
    exit 1
else
    log_success "Accès root confirmé"
fi

# ================================
# 3. TEST DE CONNEXION BASE DE DONNÉES
# ================================

log_info "3. Test de connexion à la base de données DigitalOcean..."

# Installer psql si nécessaire
if ! command -v psql &> /dev/null; then
    log_info "Installation de postgresql-client pour le test..."
    apt update -qq
    apt install -y postgresql-client
fi

# Test de connexion
log_info "Tentative de connexion à: $DB_HOST:$DB_PORT"
if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" >/dev/null 2>&1; then
    log_success "Connexion à la base DigitalOcean réussie"
    
    # Test SSL
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SHOW ssl;" 2>/dev/null | grep -q "on"; then
        log_success "SSL activé sur la base de données"
    else
        log_warning "SSL non détecté (peut être normal)"
    fi
else
    log_error "Impossible de se connecter à la base DigitalOcean"
    log_info "Vérifiez:"
    log_info "- Les paramètres de connexion dans votre dashboard DigitalOcean"
    log_info "- La liste des IPs autorisées"
    log_info "- L'état du cluster de base de données"
    exit 1
fi

# ================================
# 4. VÉRIFICATION DE L'ESPACE DISQUE
# ================================

log_info "4. Vérification de l'espace disque..."

AVAILABLE_GB=$(df / | awk 'NR==2 {print int($4/1024/1024)}')
if [ "$AVAILABLE_GB" -lt 2 ]; then
    log_error "Espace disque insuffisant: ${AVAILABLE_GB}GB disponible"
    log_info "Minimum requis: 2GB"
    exit 1
else
    log_success "Espace disque suffisant: ${AVAILABLE_GB}GB disponible"
fi

# ================================
# 5. VÉRIFICATION DE LA MÉMOIRE
# ================================

log_info "5. Vérification de la mémoire..."

MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$MEMORY_GB" -lt 3 ]; then
    log_warning "Mémoire limitée: ${MEMORY_GB}GB (recommandé: 4GB+)"
else
    log_success "Mémoire suffisante: ${MEMORY_GB}GB"
fi

# ================================
# 6. VÉRIFICATION DES PORTS
# ================================

log_info "6. Vérification des ports..."

# Port 80 (HTTP)
if netstat -tuln | grep -q ":80 "; then
    log_warning "Port 80 déjà utilisé (sera reconfiguré)"
else
    log_success "Port 80 disponible"
fi

# Port 8000 (Gunicorn)
if netstat -tuln | grep -q ":8000 "; then
    log_warning "Port 8000 déjà utilisé (sera reconfiguré)"
else
    log_success "Port 8000 disponible"
fi

# ================================
# 7. VÉRIFICATION PYTHON
# ================================

log_info "7. Vérification de Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_success "Python $PYTHON_VERSION installé"
    
    # Test génération SECRET_KEY
    if SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null); then
        log_success "Génération SECRET_KEY: OK"
        export SECRET_KEY
    else
        log_info "Django non installé, utilisation d'OpenSSL pour SECRET_KEY"
        export SECRET_KEY="django-insecure-$(openssl rand -hex 25)"
        log_success "SECRET_KEY générée avec OpenSSL"
    fi
else
    log_error "Python3 non installé"
    exit 1
fi

# ================================
# 8. VÉRIFICATION RÉSEAU
# ================================

log_info "8. Vérification du réseau..."

# Test accès internet
if curl -s --connect-timeout 5 https://google.com >/dev/null; then
    log_success "Accès internet: OK"
else
    log_error "Pas d'accès internet"
    exit 1
fi

# Test résolution DNS
if nslookup $DOMAIN >/dev/null 2>&1; then
    DOMAIN_IP=$(nslookup $DOMAIN | awk '/^Address: / { print $2 }' | tail -1)
    if [ "$DOMAIN_IP" = "$SERVER_IP" ]; then
        log_success "DNS: $DOMAIN pointe vers $SERVER_IP"
    else
        log_warning "DNS: $DOMAIN pointe vers $DOMAIN_IP (attendu: $SERVER_IP)"
        log_info "Configurez le DNS chez OVH après le déploiement"
    fi
else
    log_warning "Domaine $DOMAIN non résolu (configurez le DNS après)"
fi

# ================================
# 9. SIMULATION DES ÉTAPES CRITIQUES
# ================================

log_info "9. Simulation des étapes critiques..."

# Test création de répertoires
TEST_DIR="/tmp/martialcomp_test"
rm -rf $TEST_DIR
mkdir -p $TEST_DIR/{config,competitions,shop/{models,management/commands}}
if [ -d "$TEST_DIR" ]; then
    log_success "Création de répertoires: OK"
    rm -rf $TEST_DIR
else
    log_error "Erreur de création de répertoires"
    exit 1
fi

# Test création d'utilisateur (simulation)
if id "deploy" &>/dev/null; then
    log_info "Utilisateur deploy existe déjà"
else
    log_success "Utilisateur deploy sera créé"
fi

# ================================
# 10. IDENTIFICATION DES PROBLÈMES POTENTIELS
# ================================

log_info "10. Identification des problèmes potentiels..."

ISSUES=()

# Vérifier les services existants
if systemctl is-active nginx >/dev/null 2>&1; then
    ISSUES+=("Nginx déjà actif - sera reconfiguré")
fi

if systemctl is-active postgresql >/dev/null 2>&1; then
    ISSUES+=("PostgreSQL local détecté - risque de conflit")
fi

if [ -d "/home/deploy/martialcomp" ]; then
    ISSUES+=("Application existante détectée - sera écrasée")
fi

# Afficher les problèmes potentiels
if [ ${#ISSUES[@]} -eq 0 ]; then
    log_success "Aucun problème potentiel détecté"
else
    log_warning "Problèmes potentiels identifiés:"
    for issue in "${ISSUES[@]}"; do
        echo "  - $issue"
    done
fi

# ================================
# RAPPORT FINAL
# ================================

echo ""
echo "=============================================="
echo "📋 RAPPORT DE TEST DE DÉPLOIEMENT"
echo "=============================================="
echo ""
echo "✅ Tests réussis:"
echo "  - Variables d'environnement"
echo "  - Connexion base de données DigitalOcean"
echo "  - Espace disque et mémoire"
echo "  - Python et génération SECRET_KEY"
echo "  - Accès internet"
echo ""

if [ ${#ISSUES[@]} -gt 0 ]; then
    echo "⚠️  Problèmes potentiels:"
    for issue in "${ISSUES[@]}"; do
        echo "  - $issue"
    done
    echo ""
fi

echo "🎯 Paramètres de déploiement:"
echo "  DB_HOST: $DB_HOST"
echo "  DB_PORT: $DB_PORT"
echo "  DB_NAME: $DB_NAME"
echo "  DB_USER: $DB_USER"
echo "  DOMAIN: $DOMAIN"
echo "  SERVER_IP: $SERVER_IP"
echo "  ADMIN_EMAIL: $ADMIN_EMAIL"
echo ""

echo "✅ Le script de déploiement peut être exécuté:"
echo "  export DB_PASSWORD='YOUR_DB_PASSWORD'"
echo "  sudo ./deploy_complete_martialcomp.sh"
echo ""
echo "=============================================="

log_success "Test de déploiement terminé avec succès!"