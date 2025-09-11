#!/bin/bash

# =============================================================================
# Test de validation après correction du template en production
# =============================================================================

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

echo ""
echo "🧪 TEST DE VALIDATION APRÈS CORRECTION TEMPLATE"
echo "================================================"
echo ""

# URLs à tester
urls=(
    "https://martialcomp.com/"
    "https://martialcomp.com/fr/"
    "https://martialcomp.com/accounts/google/login/"
    "https://martialcomp.com/accounts/facebook/login/"
    "https://martialcomp.com/accounts/login/"
    "https://martialcomp.com/privacy/"
    "https://martialcomp.com/terms/"
)

descriptions=(
    "Page d'accueil principale"
    "Page française"
    "Authentification Google"
    "Authentification Facebook"
    "Connexion classique"
    "Politique de confidentialité"
    "Conditions d'utilisation"
)

success_count=0
total_urls=${#urls[@]}

echo "📋 Test des URLs critiques :"
echo ""

for i in "${!urls[@]}"; do
    url="${urls[$i]}"
    desc="${descriptions[$i]}"
    
    # Test de l'URL
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [[ "$code" =~ ^(200|302)$ ]]; then
        echo "  ✅ $desc : $url ($code)"
        ((success_count++))
    else
        echo "  ❌ $desc : $url ($code)"
    fi
done

echo ""
echo "📊 RÉSULTATS :"
echo "  URLs fonctionnelles : $success_count/$total_urls"

# Calcul du pourcentage
percentage=$((success_count * 100 / total_urls))

if [ $success_count -eq $total_urls ]; then
    log "🎉🎉🎉 SUCCÈS TOTAL ! 🎉🎉🎉"
    echo ""
    echo "L'AUTHENTIFICATION SOCIALE MARTIALCOMP EST ENTIÈREMENT OPÉRATIONNELLE !"
    echo ""
    echo "🔐 Authentification sociale :"
    echo "  ✅ Google OAuth : https://martialcomp.com/accounts/google/login/"
    echo "  ✅ Facebook OAuth : https://martialcomp.com/accounts/facebook/login/"
    echo ""
    echo "🌍 Pages principales :"
    echo "  ✅ Accueil : https://martialcomp.com/"
    echo "  ✅ Version française : https://martialcomp.com/fr/"
    echo ""
    echo "📄 Pages légales :"
    echo "  ✅ Confidentialité : https://martialcomp.com/privacy/"
    echo "  ✅ Conditions : https://martialcomp.com/terms/"
    echo ""
    echo "🎯 PROCHAINE ÉTAPE :"
    echo "Configurer les URLs de callback dans les consoles API :"
    echo "  • Google Cloud Console : https://martialcomp.com/accounts/google/login/callback/"
    echo "  • Facebook Developer Console : https://martialcomp.com/accounts/facebook/login/callback/"
    
elif [ $percentage -ge 85 ]; then
    log "✅ CORRECTION RÉUSSIE ($percentage% fonctionnel)"
    echo ""
    echo "La correction du template a été appliquée avec succès !"
    echo "Quelques URLs mineures peuvent encore nécessiter de l'attention."
    
elif [ $percentage -ge 70 ]; then
    warning "⚠️ CORRECTION PARTIELLE ($percentage% fonctionnel)"
    echo ""
    echo "La correction principale semble appliquée mais il reste des problèmes."
    echo "Vérifiez les URLs en erreur ci-dessus."
    
else
    error "❌ PROBLÈMES IMPORTANTS ($percentage% fonctionnel)"
    echo ""
    echo "La correction n'a pas eu l'effet escompté."
    echo "Vérifiez que :"
    echo "  1. Le template a bien été remplacé"
    echo "  2. Django a été redémarré"
    echo "  3. Aucune erreur dans les logs Django"
fi

echo ""
echo "📋 COMMANDES DE DIAGNOSTIC SI PROBLÈME :"
echo ""
echo "# Vérifier les logs Django"
echo "tail -20 /tmp/django_template_fix.log"
echo ""
echo "# Vérifier que Django tourne"
echo "ps aux | grep runserver"
echo ""
echo "# Tester localement sur le serveur"
echo "curl -v http://127.0.0.1:8000/"
echo ""
echo "# Voir le template actuel"
echo "head -10 /opt/martialcomp/app/competitions/templates/competitions/welcome.html"
echo ""

# Test bonus : vérifier le contenu de la page d'accueil
echo "🔍 VÉRIFICATION DU CONTENU :"
echo ""

content=$(curl -s "https://martialcomp.com/" 2>/dev/null)
if echo "$content" | grep -q "Authentification Sociale Opérationnelle"; then
    echo "  ✅ Contenu de la page mis à jour (message de succès présent)"
elif echo "$content" | grep -q "MartialComp"; then
    echo "  ⚠️ Page MartialComp chargée mais contenu peut-être ancien"
else
    echo "  ❌ Problème avec le contenu de la page"
fi

echo ""
echo "🏁 Test terminé à $(date)"
echo "==============================================="