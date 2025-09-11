#!/bin/bash
# Script de test post-déploiement

echo "🧪 TESTS POST-DÉPLOIEMENT"
echo "========================="

# Variables (à adapter)
DOMAIN="your-domain.com"
PROTOCOL="https"

# URLs à tester
URLS=(
    "$PROTOCOL://$DOMAIN/"
    "$PROTOCOL://$DOMAIN/admin/"
    "$PROTOCOL://$DOMAIN/fr/admin/"
    "$PROTOCOL://$DOMAIN/rosetta/"
    "$PROTOCOL://$DOMAIN/set-language/"
)

echo "Test des URLs principales..."

for url in "${URLS[@]}"; do
    echo -n "Testing $url ... "
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    if [ "$status" -eq 200 ] || [ "$status" -eq 302 ]; then
        echo "✅ OK ($status)"
    else
        echo "❌ ERREUR ($status)"
    fi
done

echo ""
echo "🔍 Vérifications manuelles à faire:"
echo "  1. Connectez-vous à /admin/ avec vos identifiants"
echo "  2. Accédez à /rosetta/ pour tester l'interface de traduction"
echo "  3. Testez le sélecteur de langue sur la page d'accueil"
echo "  4. Vérifiez que les traductions s'affichent correctement"
