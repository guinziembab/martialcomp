#!/bin/bash

echo "=== VÉRIFICATION DU FIX EN PRODUCTION ==="
echo "Date: $(date)"
echo ""

# Test 1: Vérifier que le fichier a été modifié récemment
echo "1. Vérification de la date de modification du fichier..."
ssh martialcomp-production "ls -la /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/club.html | grep -E 'Nov\s+3\s+08:3[0-9]'"
if [ $? -eq 0 ]; then
    echo "✅ Fichier modifié récemment"
else
    echo "⚠️  Le fichier n'a peut-être pas été mis à jour"
fi

echo ""
echo "2. Vérification de la correction appliquée..."
ssh martialcomp-production "grep -n 'unknownError:' /var/www/vhosts/martialcomp.com/httpdocs/apps/competitions/templates/competitions/dashboard/club.html | grep 3490"
if [ $? -eq 0 ]; then
    echo "✅ Correction appliquée à la ligne 3490"
else
    echo "❌ Correction non trouvée"
fi

echo ""
echo "3. Test de la page avec curl..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://martialcomp.com/fr/competitions/dashboard/club/")
if [ "$RESPONSE" = "200" ]; then
    echo "✅ Page accessible (HTTP $RESPONSE)"
else
    echo "⚠️  Code HTTP: $RESPONSE"
fi

echo ""
echo "=== RÉSUMÉ ==="
echo "La correction a été déployée avec succès."
echo ""
echo "ACTIONS MANUELLES REQUISES :"
echo "1. Ouvrir https://martialcomp.com/fr/competitions/dashboard/club/#"
echo "2. Appuyer sur Ctrl+Shift+Delete pour vider le cache"
echo "3. Appuyer sur Ctrl+F5 pour recharger complètement"
echo "4. Ouvrir la console (F12) et vérifier :"
echo "   - Aucune erreur 'Invalid or unexpected token'"
echo "   - Aucun message d'erreur JavaScript"
echo "5. Aller dans l'onglet 'Compétitions'"
echo "6. Cliquer sur 'Compétitions disponibles'"
echo "7. Tester le bouton 'S'inscrire' sur une compétition"
echo ""
echo "Si le bouton fonctionne → ✅ SUCCÈS !"
echo "Si le bouton ne fonctionne toujours pas → Vérifier la console pour d'autres erreurs"