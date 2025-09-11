#!/bin/bash

# =============================================================================
# Script de validation pré-déploiement pour l'authentification modernisée
# Vérifie que tous les fichiers sont prêts avant le déploiement
# =============================================================================

set -e

# Configuration
LOCAL_PROJECT_DIR="/mnt/c/martial_hub_django/martialcomp"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Fonction de logging
log() {
    echo -e "${GREEN}[✓] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[⚠] $1${NC}"
}

error() {
    echo -e "${RED}[✗] $1${NC}"
}

info() {
    echo -e "${BLUE}[ℹ] $1${NC}"
}

# Compteurs
ERRORS=0
WARNINGS=0

# Vérifier l'existence des fichiers critiques
check_files() {
    info "Vérification des fichiers critiques..."
    
    # Templates d'authentification
    if [ -f "$LOCAL_PROJECT_DIR/competitions/templates/registration/login.html" ]; then
        log "Template de login trouvé"
    else
        error "Template de login manquant"
        ((ERRORS++))
    fi
    
    if [ -f "$LOCAL_PROJECT_DIR/competitions/templates/registration/signup.html" ]; then
        log "Template d'inscription trouvé"
    else
        error "Template d'inscription manquant"
        ((ERRORS++))
    fi
    
    # Vues d'authentification
    if [ -f "$LOCAL_PROJECT_DIR/competitions/views/auth.py" ]; then
        log "Vues d'authentification trouvées"
    else
        error "Vues d'authentification manquantes"
        ((ERRORS++))
    fi
    
    # Fichiers CSS
    if [ -f "$LOCAL_PROJECT_DIR/competitions/static/css/auth.css" ]; then
        log "Fichier CSS d'authentification trouvé"
    else
        error "Fichier CSS d'authentification manquant"
        ((ERRORS++))
    fi
}

# Vérifier le contenu des templates
check_template_content() {
    info "Vérification du contenu des templates..."
    
    # Vérifier le template de login
    LOGIN_TEMPLATE="$LOCAL_PROJECT_DIR/competitions/templates/registration/login.html"
    if [ -f "$LOGIN_TEMPLATE" ]; then
        if grep -q "auth.css" "$LOGIN_TEMPLATE"; then
            log "Template de login utilise le nouveau CSS"
        else
            warning "Template de login ne semble pas utiliser le nouveau CSS"
            ((WARNINGS++))
        fi
        
        if grep -q "profile_info" "$LOGIN_TEMPLATE"; then
            log "Template de login inclut les informations contextuelles"
        else
            warning "Template de login ne semble pas inclure les informations contextuelles"
            ((WARNINGS++))
        fi
        
        if grep -q "socialaccount_login" "$LOGIN_TEMPLATE"; then
            log "Template de login inclut l'authentification sociale"
        else
            warning "Template de login ne semble pas inclure l'authentification sociale"
            ((WARNINGS++))
        fi
    fi
    
    # Vérifier le template d'inscription
    SIGNUP_TEMPLATE="$LOCAL_PROJECT_DIR/competitions/templates/registration/signup.html"
    if [ -f "$SIGNUP_TEMPLATE" ]; then
        if grep -q "auth.css" "$SIGNUP_TEMPLATE"; then
            log "Template d'inscription utilise le nouveau CSS"
        else
            warning "Template d'inscription ne semble pas utiliser le nouveau CSS"
            ((WARNINGS++))
        fi
        
        if grep -q "socialaccount_login" "$SIGNUP_TEMPLATE"; then
            log "Template d'inscription inclut l'authentification sociale"
        else
            warning "Template d'inscription ne semble pas inclure l'authentification sociale"
            ((WARNINGS++))
        fi
    fi
}

# Vérifier les vues
check_views() {
    info "Vérification des vues d'authentification..."
    
    AUTH_VIEWS="$LOCAL_PROJECT_DIR/competitions/views/auth.py"
    if [ -f "$AUTH_VIEWS" ]; then
        if grep -q "profile_info" "$AUTH_VIEWS"; then
            log "Vues incluent la logique de profil contextuel"
        else
            warning "Vues ne semblent pas inclure la logique de profil contextuel"
            ((WARNINGS++))
        fi
        
        if grep -q "tenant" "$AUTH_VIEWS" || grep -q "organization" "$AUTH_VIEWS"; then
            log "Vues incluent la logique multi-tenant"
        else
            warning "Vues ne semblent pas inclure la logique multi-tenant"
            ((WARNINGS++))
        fi
    fi
}

# Vérifier le CSS
check_css() {
    info "Vérification du fichier CSS..."
    
    CSS_FILE="$LOCAL_PROJECT_DIR/competitions/static/css/auth.css"
    if [ -f "$CSS_FILE" ]; then
        # Vérifier la taille du fichier (doit être substantiel)
        FILE_SIZE=$(wc -c < "$CSS_FILE")
        if [ "$FILE_SIZE" -gt 5000 ]; then
            log "Fichier CSS a une taille appropriée ($FILE_SIZE bytes)"
        else
            warning "Fichier CSS semble petit ($FILE_SIZE bytes)"
            ((WARNINGS++))
        fi
        
        # Vérifier les classes importantes
        if grep -q "auth-container" "$CSS_FILE"; then
            log "CSS contient les styles de conteneur d'authentification"
        else
            error "CSS ne contient pas les styles de conteneur d'authentification"
            ((ERRORS++))
        fi
        
        if grep -q "btn-social" "$CSS_FILE"; then
            log "CSS contient les styles de boutons sociaux"
        else
            error "CSS ne contient pas les styles de boutons sociaux"
            ((ERRORS++))
        fi
        
        if grep -q "profile-info" "$CSS_FILE"; then
            log "CSS contient les styles de profil contextuel"
        else
            warning "CSS ne contient pas les styles de profil contextuel"
            ((WARNINGS++))
        fi
    fi
}

# Vérifier les dépendances
check_dependencies() {
    info "Vérification des dépendances..."
    
    # Vérifier django-allauth dans requirements.txt
    if [ -f "$LOCAL_PROJECT_DIR/requirements.txt" ]; then
        if grep -q "django-allauth" "$LOCAL_PROJECT_DIR/requirements.txt"; then
            log "django-allauth présent dans requirements.txt"
        else
            warning "django-allauth non trouvé dans requirements.txt"
            ((WARNINGS++))
        fi
    else
        warning "Fichier requirements.txt non trouvé"
        ((WARNINGS++))
    fi
    
    # Vérifier la configuration dans settings.py
    if [ -f "$LOCAL_PROJECT_DIR/config/settings.py" ]; then
        if grep -q "allauth" "$LOCAL_PROJECT_DIR/config/settings.py"; then
            log "Configuration allauth trouvée dans settings.py"
        else
            warning "Configuration allauth non trouvée dans settings.py"
            ((WARNINGS++))
        fi
    fi
}

# Résumé des vérifications
show_summary() {
    echo ""
    echo "=== RÉSUMÉ DE LA VALIDATION ==="
    
    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        log "✅ Tous les contrôles sont passés avec succès!"
        log "Le déploiement peut être effectué en toute sécurité."
    elif [ $ERRORS -eq 0 ]; then
        warning "⚠️  $WARNINGS avertissement(s) détecté(s)"
        warning "Le déploiement peut être effectué mais vérifiez les avertissements."
    else
        error "❌ $ERRORS erreur(s) et $WARNINGS avertissement(s) détecté(s)"
        error "Corrigez les erreurs avant de déployer."
        return 1
    fi
    
    echo ""
    info "Fichiers à déployer:"
    info "- competitions/templates/registration/login.html"
    info "- competitions/templates/registration/signup.html"
    info "- competitions/views/auth.py"
    info "- competitions/static/css/auth.css"
    
    echo ""
    info "Pour déployer, exécutez:"
    info "./deploy_auth_modernization.sh"
}

# Script principal
main() {
    echo "=== VALIDATION PRÉ-DÉPLOIEMENT DE L'AUTHENTIFICATION ==="
    echo ""
    
    check_files
    check_template_content
    check_views
    check_css
    check_dependencies
    show_summary
}

# Exécuter la validation
main "$@"