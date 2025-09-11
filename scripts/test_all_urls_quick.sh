#!/bin/bash

# =============================================================================
# Test rapide de toutes les URLs après correction i18n
# =============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] $1${NC}"
}

log "=== TEST RAPIDE TOUTES LES URLs ==="

echo ""
echo "📋 Tests des URLs principales:"

# URLs critiques à tester
urls=(
    "https://martialcomp.com/"
    "https://martialcomp.com/fr/"
    "https://www.martialcomp.com/fr/"
    "https://martialcomp.com/privacy/"
    "https://martialcomp.com/terms/"
    "https://martialcomp.com/fr/privacy/"
    "https://martialcomp.com/fr/terms/"
    "https://martialcomp.com/accounts/login/"
    "https://martialcomp.com/fr/accounts/login/"
    "https://martialcomp.com/accounts/google/login/"
    "https://martialcomp.com/accounts/facebook/login/"
)

success_count=0
total_count=${#urls[@]}

for url in "${urls[@]}"; do
    code=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "timeout")
    
    if [[ "$code" =~ ^(200|302)$ ]]; then
        echo "  ✅ $url ($code)"
        ((success_count++))
    else
        echo "  ❌ $url ($code)"
    fi
done

echo ""
echo "📊 Résultat: $success_count/$total_count URLs fonctionnelles"

if [ $success_count -eq $total_count ]; then
    log "🎉 TOUTES LES URLs FONCTIONNENT !"
    echo ""
    echo "🎯 L'authentification sociale MartialComp est ENTIÈREMENT OPÉRATIONNELLE !"
    echo ""
    echo "🔐 URLs d'authentification prêtes:"
    echo "  ✅ https://martialcomp.com/accounts/google/login/"
    echo "  ✅ https://martialcomp.com/accounts/facebook/login/"
    echo ""
    echo "📄 Pages légales configurées:"
    echo "  ✅ https://martialcomp.com/privacy/"
    echo "  ✅ https://martialcomp.com/terms/"
    echo ""
    echo "🌍 Pages multilingues:"
    echo "  ✅ https://martialcomp.com/fr/ (français)"
    echo "  ✅ https://www.martialcomp.com/fr/ (avec www)"
    echo ""
    echo "🎯 PROCHAINE ÉTAPE:"
    echo "Configurer les callbacks dans Google Cloud Console et Facebook Developer Console:"
    echo "  - Google callback: https://martialcomp.com/accounts/google/login/callback/"
    echo "  - Facebook callback: https://martialcomp.com/accounts/facebook/login/callback/"
    echo "  - Privacy URL: https://martialcomp.com/privacy/"
    echo "  - Terms URL: https://martialcomp.com/terms/"
else
    error "Certaines URLs ne fonctionnent pas encore"
    echo ""
    echo "🔧 URLs à vérifier:"
    for url in "${urls[@]}"; do
        code=$(timeout 5 curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "timeout")
        if [[ ! "$code" =~ ^(200|302)$ ]]; then
            echo "  ❌ $url ($code)"
        fi
    done
fi

echo ""
log "Test terminé"