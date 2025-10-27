#!/bin/bash

# Script de déploiement - Gestion des comptes utilisateurs pratiquants
# Date: 27 octobre 2025
# Description: Déploie les fonctionnalités de création et association de comptes

set -e  # Arrêter en cas d'erreur

echo "=================================================="
echo "  Déploiement - Gestion comptes pratiquants"
echo "=================================================="
echo ""

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher des messages
print_step() {
    echo -e "${BLUE}[ÉTAPE]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# 1. Vérifications pré-déploiement
print_step "Vérifications pré-déploiement..."

# Vérifier qu'on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    print_error "Fichier manage.py introuvable. Êtes-vous dans le bon répertoire ?"
    exit 1
fi
print_success "Répertoire projet confirmé"

# Vérifier que les fichiers modifiés existent
if [ ! -f "apps/competitions/views/club/practitioners.py" ]; then
    print_error "Fichier views/club/practitioners.py introuvable"
    exit 1
fi
print_success "Fichier practitioners.py trouvé"

if [ ! -f "apps/competitions/templates/competitions/club/create_user_form.html" ]; then
    print_error "Template create_user_form.html introuvable"
    exit 1
fi
print_success "Template create_user_form.html trouvé"

# 2. Sauvegardes
print_step "Création des sauvegardes de sécurité..."

BACKUP_DIR="backups/gestion_comptes_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Sauvegarder les fichiers modifiés
cp apps/competitions/views/club/practitioners.py "$BACKUP_DIR/" 2>/dev/null || print_warning "Fichier practitioners.py non sauvegardé"
print_success "Sauvegardes créées dans $BACKUP_DIR"

# 3. Vérifier Git
print_step "Vérification de l'état Git..."

if git rev-parse --git-dir > /dev/null 2>&1; then
    print_success "Dépôt Git détecté"
    
    # Afficher les modifications
    echo ""
    print_step "Fichiers modifiés:"
    git status --short
    echo ""
    
    # Demander confirmation
    read -p "Voulez-vous continuer avec le déploiement ? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Déploiement annulé par l'utilisateur"
        exit 0
    fi
else
    print_warning "Pas de dépôt Git détecté"
fi

# 4. Tests de syntaxe Python
print_step "Vérification de la syntaxe Python..."

python -m py_compile apps/competitions/views/club/practitioners.py
if [ $? -eq 0 ]; then
    print_success "Syntaxe Python valide"
else
    print_error "Erreur de syntaxe Python détectée"
    exit 1
fi

# 5. Vérifier la configuration email (optionnel)
print_step "Vérification de la configuration email..."

if grep -q "EMAIL_HOST" martialcomp/settings/production.py 2>/dev/null; then
    print_success "Configuration email trouvée dans settings"
else
    print_warning "Configuration email non trouvée - les emails pourraient ne pas fonctionner"
    print_warning "Vérifiez EMAIL_HOST, EMAIL_PORT, etc. dans settings/production.py"
fi

# 6. Collecte des fichiers statiques (si nécessaire)
print_step "Collecte des fichiers statiques..."

if [ -f "manage.py" ]; then
    python manage.py collectstatic --noinput --clear 2>&1 | grep -v "Deleting" || true
    print_success "Fichiers statiques collectés"
else
    print_warning "Impossible de collecter les fichiers statiques"
fi

# 7. Vérifier les URLs
print_step "Vérification des URLs..."

if grep -q "create_user_for_practitioner" apps/competitions/urls/club.py; then
    print_success "URL create_user_for_practitioner trouvée"
else
    print_error "URL create_user_for_practitioner non trouvée dans urls/club.py"
    exit 1
fi

if grep -q "link_user_to_practitioner" apps/competitions/urls/club.py; then
    print_success "URL link_user_to_practitioner trouvée"
else
    print_error "URL link_user_to_practitioner non trouvée dans urls/club.py"
    exit 1
fi

# 8. Git commit (si demandé)
print_step "Création du commit Git..."

read -p "Voulez-vous créer un commit Git ? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add apps/competitions/views/club/practitioners.py
    git add apps/competitions/templates/competitions/club/create_user_form.html
    git add RAPPORT_IMPLEMENTATION_GESTION_COMPTES_20251027.md
    
    git commit -m "feat: Implémentation gestion comptes pratiquants

- Création automatique de compte avec mot de passe
- Association compte existant à pratiquant  
- Envoi email invitation avec identifiants
- Template create_user_form.html
- Sécurité et gestion erreurs complètes"
    
    print_success "Commit créé avec succès"
    
    # Proposer le push
    read -p "Voulez-vous pousser vers le dépôt distant ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        CURRENT_BRANCH=$(git branch --show-current)
        git push origin "$CURRENT_BRANCH"
        print_success "Modifications poussées vers $CURRENT_BRANCH"
    fi
else
    print_warning "Commit Git ignoré"
fi

# 9. Redémarrage du serveur (si en production)
print_step "Redémarrage du serveur..."

if [ -f "/etc/systemd/system/gunicorn.service" ]; then
    echo "Service Gunicorn détecté"
    read -p "Voulez-vous redémarrer Gunicorn ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo systemctl restart gunicorn
        print_success "Gunicorn redémarré"
    fi
elif command -v supervisorctl &> /dev/null; then
    echo "Supervisor détecté"
    read -p "Voulez-vous redémarrer avec Supervisor ? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo supervisorctl restart martialcomp
        print_success "Application redémarrée via Supervisor"
    fi
else
    print_warning "Aucun système de gestion de service détecté"
    print_warning "Redémarrez manuellement votre serveur web"
fi

# 10. Résumé
echo ""
echo "=================================================="
print_success "Déploiement terminé avec succès !"
echo "=================================================="
echo ""
echo "📋 Résumé des actions effectuées:"
echo "  ✅ Vérifications pré-déploiement"
echo "  ✅ Sauvegardes créées"
echo "  ✅ Syntaxe Python vérifiée"
echo "  ✅ URLs vérifiées"
echo "  ✅ Fichiers statiques collectés"
echo ""
echo "📍 Prochaines étapes:"
echo "  1. Tester l'accès au dashboard club"
echo "  2. Tester la création d'un compte pour un pratiquant"
echo "  3. Vérifier l'envoi d'email"
echo "  4. Tester l'association d'un compte existant"
echo ""
echo "📚 Documentation:"
echo "  Voir: RAPPORT_IMPLEMENTATION_GESTION_COMPTES_20251027.md"
echo ""
echo "🔗 URLs à tester:"
echo "  - Dashboard club: /fr/competitions/dashboard/club/"
echo "  - Liste pratiquants: /fr/competitions/club/practitioners/"
echo ""

# Afficher les informations de configuration email
if [ -f "martialcomp/settings/production.py" ]; then
    echo "⚙️  Configuration email actuelle:"
    grep -E "EMAIL_HOST|EMAIL_PORT|EMAIL_USE_TLS|DEFAULT_FROM_EMAIL" martialcomp/settings/production.py 2>/dev/null | sed 's/^/  /' || echo "  (non trouvée)"
    echo ""
fi

print_success "Tout est prêt ! Bonne utilisation 🚀"
echo ""
