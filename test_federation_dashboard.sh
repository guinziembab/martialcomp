#!/bin/bash
# Test final du dashboard federation

echo "================================================"
echo "🔍 TEST DU DASHBOARD FEDERATION"
echo "================================================"
echo ""

# Test avec authentification
echo "1️⃣ Test avec authentification..."
echo "==============================="

# D'abord obtenir le CSRF token
CSRF_TOKEN=$(curl -s -c /tmp/cookies.txt https://martialcomp.com/accounts/login/ | grep -oP 'csrfmiddlewaretoken" value="\K[^"]*' | head -1)
echo "CSRF Token obtenu: ${CSRF_TOKEN:0:20}..."

# Se connecter
echo ""
echo "2️⃣ Connexion avec DT_bguinziemba..."
echo "==================================="
LOGIN_RESPONSE=$(curl -s -L -c /tmp/cookies.txt -b /tmp/cookies.txt \
  -X POST https://martialcomp.com/accounts/login/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "csrfmiddlewaretoken=${CSRF_TOKEN}&login=DT_bguinziemba&password=AQWZSX123ok%2C" \
  -w "\nSTATUS:%{http_code}")

STATUS=$(echo "$LOGIN_RESPONSE" | grep "STATUS:" | cut -d: -f2)
echo "Status de connexion: $STATUS"

# Tester l'accès au dashboard
echo ""
echo "3️⃣ Test d'accès au dashboard federation..."
echo "========================================"
DASHBOARD_RESPONSE=$(curl -s -L -b /tmp/cookies.txt \
  https://martialcomp.com/fr/competitions/dashboard/federation/41/ \
  -w "\nSTATUS:%{http_code}\nURL:%{url_effective}")

STATUS=$(echo "$DASHBOARD_RESPONSE" | grep "STATUS:" | cut -d: -f2)
URL=$(echo "$DASHBOARD_RESPONSE" | grep "URL:" | cut -d: -f2-)

echo "Status: $STATUS"
echo "URL finale: $URL"

if [ "$STATUS" = "200" ]; then
    echo ""
    echo "4️⃣ Analyse du contenu..."
    echo "======================"
    
    # Vérifier les éléments clés
    if echo "$DASHBOARD_RESPONSE" | grep -q "UBLP"; then
        echo "✅ Nom de la fédération présent"
    else
        echo "❌ Nom de la fédération absent"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "Tableau de bord"; then
        echo "✅ Titre du dashboard présent"
    else
        echo "❌ Titre du dashboard absent"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "federation_manage_clubs"; then
        echo "✅ Lien 'Gérer les clubs' présent"
    else
        echo "❌ Lien 'Gérer les clubs' absent"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "federation_manage_competitions"; then
        echo "✅ Lien 'Gérer les compétitions' présent"
    else
        echo "❌ Lien 'Gérer les compétitions' absent"
    fi
    
    # Compter les sections principales
    SECTIONS=$(echo "$DASHBOARD_RESPONSE" | grep -c "card-header")
    echo "📊 Nombre de sections: $SECTIONS"
    
    # Vérifier les erreurs
    if echo "$DASHBOARD_RESPONSE" | grep -q "NoReverseMatch"; then
        echo "❌ ERREUR: NoReverseMatch détecté"
        echo "$DASHBOARD_RESPONSE" | grep -A2 "NoReverseMatch"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "TemplateSyntaxError"; then
        echo "❌ ERREUR: TemplateSyntaxError détecté"
        echo "$DASHBOARD_RESPONSE" | grep -A2 "TemplateSyntaxError"
    fi
    
    if echo "$DASHBOARD_RESPONSE" | grep -q "500 Server Error"; then
        echo "❌ ERREUR: 500 Server Error détecté"
    fi
    
elif [ "$STATUS" = "500" ]; then
    echo ""
    echo "❌ ERREUR 500 - Extraction des détails..."
    echo "======================================"
    echo "$DASHBOARD_RESPONSE" | grep -E "(Exception|Error|Traceback)" | head -10
fi

# Nettoyer
rm -f /tmp/cookies.txt

echo ""
echo "================================================"
echo "📋 RÉSUMÉ"
echo "================================================"
if [ "$STATUS" = "200" ]; then
    echo "✅ Le dashboard federation est accessible"
    echo "📍 URL: https://martialcomp.com/fr/competitions/dashboard/federation/41/"
else
    echo "❌ Le dashboard federation n'est pas accessible"
    echo "📍 Status HTTP: $STATUS"
fi