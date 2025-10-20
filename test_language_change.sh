#!/bin/bash

# Script pour tester le changement de langue

echo "=== TEST DU CHANGEMENT DE LANGUE ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Vérifier que CSRF_TRUSTED_ORIGINS est bien configuré
echo "1. VÉRIFICATION DE LA CONFIGURATION CSRF"
echo "======================================="

/var/www/vhosts/martialcomp.com/venv/bin/python manage.py shell --settings=config.settings.production << 'EOF'
from django.conf import settings

print("CSRF Configuration:")
print(f"- CSRF_COOKIE_NAME: {settings.CSRF_COOKIE_NAME}")
print(f"- CSRF_COOKIE_DOMAIN: {settings.CSRF_COOKIE_DOMAIN}")
print(f"- CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
print(f"- ALLOWED_HOSTS: {settings.ALLOWED_HOSTS[:3]}...")  # Premiers hosts seulement
EOF

echo ""

# 2. Test avec curl
echo "2. TEST AVEC CURL"
echo "================="

echo "Récupération du token CSRF..."

# Obtenir la page et extraire le token CSRF
response=$(curl -s -c cookies.txt https://martialcomp.com/fr/)
csrf_token=$(echo "$response" | grep -oP 'name="csrfmiddlewaretoken" value="\K[^"]+' | head -1)

if [ -z "$csrf_token" ]; then
    echo "⚠️ Token CSRF non trouvé dans la page"
    echo "Recherche alternative..."
    
    # Chercher dans les cookies
    csrf_token=$(grep "martialcomp_csrftoken" cookies.txt | awk '{print $7}')
    
    if [ -z "$csrf_token" ]; then
        echo "❌ Impossible de récupérer le token CSRF"
    else
        echo "✓ Token CSRF trouvé dans les cookies: ${csrf_token:0:20}..."
    fi
else
    echo "✓ Token CSRF trouvé dans le HTML: ${csrf_token:0:20}..."
fi

# Test de changement de langue
if [ ! -z "$csrf_token" ]; then
    echo ""
    echo "Test de changement vers l'anglais..."
    
    response_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST https://martialcomp.com/set_language/ \
        -H "Cookie: martialcomp_csrftoken=$csrf_token" \
        -H "X-CSRFToken: $csrf_token" \
        -H "Referer: https://martialcomp.com/" \
        -d "language=en&next=/")
    
    echo "Code de réponse: $response_code"
    
    if [ "$response_code" = "302" ] || [ "$response_code" = "200" ]; then
        echo "✓ Changement de langue réussi!"
    else
        echo "❌ Erreur lors du changement de langue"
    fi
fi

# Nettoyer
rm -f cookies.txt

echo ""

# 3. Vérifier les logs pour des erreurs
echo "3. VÉRIFICATION DES LOGS"
echo "========================"

echo "Dernières erreurs CSRF dans les logs:"
tail -n 50 logs/django.log | grep -i "csrf" | tail -5 || echo "Pas d'erreurs CSRF récentes"

echo ""

# 4. Créer un script de test simple
echo "4. CRÉATION D'UN FORMULAIRE DE TEST"
echo "==================================="

cat > test_language_form.html << 'TEST_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Test Language Change</title>
</head>
<body>
    <h1>Test du changement de langue</h1>
    
    <p>URL actuelle: <span id="current-url"></span></p>
    
    <form action="https://martialcomp.com/set_language/" method="post">
        <!-- Token CSRF à remplacer -->
        <input type="hidden" name="csrfmiddlewaretoken" value="REMPLACER_PAR_LE_TOKEN">
        <input type="hidden" name="next" value="/">
        
        <label>Choisir une langue:</label>
        <select name="language">
            <option value="fr">Français</option>
            <option value="en">English</option>
            <option value="es">Español</option>
        </select>
        
        <button type="submit">Changer</button>
    </form>
    
    <script>
        document.getElementById('current-url').textContent = window.location.href;
    </script>
    
    <hr>
    
    <p><strong>Instructions:</strong></p>
    <ol>
        <li>Ouvrez https://martialcomp.com/ dans votre navigateur</li>
        <li>Ouvrez les outils de développement (F12)</li>
        <li>Allez dans Application/Storage > Cookies</li>
        <li>Trouvez le cookie "martialcomp_csrftoken"</li>
        <li>Copiez sa valeur</li>
        <li>Remplacez "REMPLACER_PAR_LE_TOKEN" dans ce formulaire</li>
        <li>Soumettez le formulaire</li>
    </ol>
</body>
</html>
TEST_EOF

echo "✓ Formulaire de test créé: test_language_form.html"

echo ""
echo "============================================"
echo "RÉSUMÉ DU DIAGNOSTIC"
echo "============================================"
echo ""
echo "✅ Points vérifiés:"
echo "   - Template contient {% csrf_token %}"
echo "   - CSRF_TRUSTED_ORIGINS configuré"
echo "   - Service redémarré"
echo ""
echo "📋 Actions recommandées:"
echo ""
echo "1. TESTER DANS LE NAVIGATEUR:"
echo "   - Videz COMPLÈTEMENT le cache et les cookies"
echo "   - Ouvrez un nouvel onglet privé/incognito"
echo "   - Allez sur https://martialcomp.com/"
echo "   - Essayez de changer la langue"
echo ""
echo "2. SI L'ERREUR PERSISTE:"
echo "   - Vérifiez dans F12 > Network que le token est envoyé"
echo "   - Vérifiez dans F12 > Console les erreurs JavaScript"
echo "   - Regardez les cookies (martialcomp_csrftoken doit exister)"
echo ""
echo "3. SOLUTION ALTERNATIVE:"
echo "   Si le JavaScript pose problème, on peut modifier le template"
echo "   pour utiliser un submit classique au lieu du JavaScript"
echo ""
echo "============================================"