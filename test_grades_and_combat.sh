#!/bin/bash

# Script pour tester les fonctionnalités Grades et Combat après corrections

echo "=== TEST DES FONCTIONNALITÉS GRADES ET COMBAT ==="
echo ""
echo "Date: $(date)"
echo ""

# 1. Test de l'URL Grades
echo "1. TEST DE LA FONCTIONNALITÉ GRADES"
echo "==================================="

echo "Test de l'URL: https://martialcomp.com/fr/competitions/grades/management/"
response=$(curl -s -o /tmp/grades_test.html -w "%{http_code}" -L https://martialcomp.com/fr/competitions/grades/management/)
echo "Réponse HTTP: $response"

if [ "$response" = "200" ]; then
    echo "✅ Page grades accessible avec succès !"
    echo ""
    echo "Aperçu du contenu:"
    grep -o "<title>.*</title>" /tmp/grades_test.html || echo "Pas de titre trouvé"
    grep -o "<h1>.*</h1>" /tmp/grades_test.html | head -1 || echo "Pas de H1 trouvé"
elif [ "$response" = "302" ]; then
    echo "⚠️ Redirection (probablement vers la page de connexion)"
    location=$(curl -s -I https://martialcomp.com/fr/competitions/grades/management/ | grep -i "^location:" | cut -d' ' -f2)
    echo "Redirige vers: $location"
elif [ "$response" = "404" ]; then
    echo "❌ Page non trouvée - l'URL n'existe pas"
elif [ "$response" = "500" ]; then
    echo "❌ Erreur 500 - Erreur serveur"
else
    echo "❌ Réponse inattendue: $response"
fi

echo ""

# 2. Test de l'URL Combat
echo "2. TEST DE LA FONCTIONNALITÉ COMBAT"
echo "===================================="

echo "Test de l'URL: https://martialcomp.com/fr/competitions/combat/combats/creer/"
response=$(curl -s -o /tmp/combat_test.html -w "%{http_code}" -L https://martialcomp.com/fr/competitions/combat/combats/creer/)
echo "Réponse HTTP: $response"

if [ "$response" = "200" ]; then
    echo "✅ Page combat accessible avec succès !"
    echo ""
    echo "Aperçu du contenu:"
    grep -o "<title>.*</title>" /tmp/combat_test.html || echo "Pas de titre trouvé"
    grep -o "<h1>.*</h1>" /tmp/combat_test.html | head -1 || echo "Pas de H1 trouvé"
elif [ "$response" = "302" ]; then
    echo "⚠️ Redirection (probablement vers la page de connexion)"
    location=$(curl -s -I https://martialcomp.com/fr/competitions/combat/combats/creer/ | grep -i "^location:" | cut -d' ' -f2)
    echo "Redirige vers: $location"
elif [ "$response" = "404" ]; then
    echo "❌ Page non trouvée - l'URL n'existe pas"
elif [ "$response" = "500" ]; then
    echo "❌ Erreur 500 - Erreur serveur"
else
    echo "❌ Réponse inattendue: $response"
fi

echo ""

# 3. Test avec authentification simulée
echo "3. TEST AVEC COOKIES D'AUTHENTIFICATION"
echo "========================================"

# Essayer de récupérer un cookie de session valide si possible
echo "Note: Pour un test complet, vous devez:"
echo "1. Vous connecter manuellement avec TESTBGA_USER1"
echo "2. Accéder au dashboard: https://martialcomp.com/fr/competitions/dashboard/club/"
echo "3. Cliquer sur 'Grades et Examens'"
echo "4. Essayer 'Créer un combat'"

echo ""

# 4. Vérifier le statut du service
echo "4. STATUT DU SERVICE"
echo "===================="

if command -v systemctl &> /dev/null; then
    echo "Service Gunicorn:"
    systemctl is-active martialcomp.service && echo "✅ Actif" || echo "❌ Inactif"
else
    echo "⚠️ systemctl non disponible sur ce système"
fi

echo ""

# 5. Test de la page d'accueil
echo "5. TEST DE LA PAGE D'ACCUEIL"
echo "============================"

echo "Test de https://martialcomp.com/"
response=$(curl -s -o /dev/null -w "%{http_code}" https://martialcomp.com/)
echo "Réponse HTTP: $response"

if [ "$response" = "200" ] || [ "$response" = "302" ]; then
    echo "✅ Site accessible"
else
    echo "❌ Problème d'accès au site"
fi

echo ""

# 6. Résumé
echo "============================================"
echo "RÉSUMÉ DES TESTS"
echo "============================================"
echo ""

# Nettoyer
rm -f /tmp/grades_test.html /tmp/combat_test.html

echo "Tests automatisés terminés."
echo ""
echo "Pour des tests complets:"
echo "1. Connectez-vous sur https://martialcomp.com/admin/ avec TESTBGA_USER1"
echo "2. Allez au dashboard club"
echo "3. Testez manuellement:"
echo "   - Le bouton 'Grades et Examens'"
echo "   - La création d'un combat"
echo ""
echo "Les codes HTTP 302 indiquent généralement que l'authentification"
echo "est requise, ce qui est normal pour ces pages protégées."
echo ""
echo "============================================"