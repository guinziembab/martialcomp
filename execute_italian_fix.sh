#!/bin/bash

# Script pour exécuter la correction italienne sur la production

echo "=== EXÉCUTION DE LA CORRECTION ITALIENNE SUR PRODUCTION ==="
echo ""
echo "Ce script va:"
echo "1. Créer un nouveau fichier de traduction italien"
echo "2. Compiler les traductions"
echo "3. Redémarrer le service"
echo ""
echo "Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler..."
read

# Se connecter et exécuter le script
ssh martialcomp-production 'cd /var/www/vhosts/martialcomp.com/httpdocs && bash -s' < fix_italian_translations.sh

echo ""
echo "✅ Script exécuté!"
echo ""
echo "TESTEZ MAINTENANT:"
echo "1. Allez sur https://martialcomp.com/"
echo "2. Changez la langue en Italien"
echo "3. Vérifiez que les textes sont en italien et non en français"