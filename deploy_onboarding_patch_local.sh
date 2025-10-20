#!/bin/bash
# Script de déploiement local du patch d'urgence onboarding
# À exécuter dans l'environnement de développement

echo "=========================================="
echo "🚀 DÉPLOIEMENT PATCH ONBOARDING - LOCAL"
echo "=========================================="
echo ""

# Variables
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Fonction de log
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

# 1. Vérifier les fichiers créés
log "📁 Vérification des fichiers du patch..."

files_to_check=(
    "apps/competitions/management/commands/init_disciplines.py"
    "apps/competitions/views/onboarding/emergency_views.py"
    "apps/competitions/templates/competitions/onboarding/error.html"
    "apps/competitions/tests/test_onboarding_emergency.py"
)

all_files_exist=true
for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file MANQUANT!"
        all_files_exist=false
    fi
done

if [ "$all_files_exist" = false ]; then
    log_error "Des fichiers sont manquants. Arrêt du déploiement."
    exit 1
fi

# 2. Vérifier la modification des URLs
log "🔗 Vérification des URLs..."
if grep -q "safe_club_creation" apps/competitions/urls/onboarding.py; then
    echo "   ✅ Routes d'urgence configurées"
else
    echo "   ❌ Routes d'urgence non trouvées"
    exit 1
fi

# 3. Résumé du patch
log "📊 Résumé du patch d'urgence"
echo ""
echo "FONCTIONNALITÉS AJOUTÉES:"
echo "  ✅ Commande init_disciplines pour initialiser les disciplines"
echo "  ✅ Vues sécurisées avec gestion d'erreurs robuste"
echo "  ✅ Page d'erreur gracieuse pour meilleure UX"
echo "  ✅ Tests unitaires complets"
echo ""
echo "ROUTES AJOUTÉES:"
echo "  📍 /onboarding/club/creation/safe/ -> Vue sécurisée création club"
echo "  📍 /onboarding/federation/safe/ -> Vue sécurisée création fédération"
echo "  📍 /onboarding/error/ -> Page d'erreur"
echo "  📍 /onboarding/complete/ -> Finalisation onboarding"
echo ""

# 4. Instructions pour tester
echo "=========================================="
echo "📋 INSTRUCTIONS POUR TESTER"
echo "=========================================="
echo ""
echo "1. Installer les dépendances manquantes (si nécessaire) :"
echo "   pip install channels django-formtools"
echo ""
echo "2. Initialiser les disciplines :"
echo "   python manage.py init_disciplines"
echo ""
echo "3. Exécuter les tests unitaires :"
echo "   python manage.py test apps.competitions.tests.test_onboarding_emergency"
echo ""
echo "4. Lancer le serveur de développement :"
echo "   python manage.py runserver"
echo ""
echo "5. Tester les nouvelles URLs :"
echo "   - http://localhost:8000/competitions/onboarding/club/creation/safe/"
echo "   - http://localhost:8000/competitions/onboarding/federation/safe/"
echo "   - http://localhost:8000/competitions/onboarding/error/"
echo ""
echo "6. Pour utiliser les nouvelles vues, remplacer temporairement :"
echo "   - club.handle_club_creation -> emergency_views.safe_club_creation"
echo "   - federations.handle_federation_creation -> emergency_views.safe_federation_creation"
echo ""

log "✅ Patch d'urgence prêt à être testé!"
echo ""
echo "⚠️  IMPORTANT: Ce patch est une solution temporaire."
echo "Une refonte complète avec SessionWizardView est recommandée (Phase 2)."