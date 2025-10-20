#!/bin/bash

echo "=== DIAGNOSTIC PASSENGER ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Vérifier que passenger_wsgi.py existe et a les bonnes permissions
echo "1. Vérification de passenger_wsgi.py..."
ls -la passenger_wsgi.py
echo ""

# 2. Vérifier le contenu actuel
echo "2. Contenu actuel de passenger_wsgi.py:"
echo "----------------------------------------"
cat passenger_wsgi.py
echo "----------------------------------------"
echo ""

# 3. Tester si Passenger trouve l'application
echo "3. Test de l'import de passenger_wsgi..."
/var/www/vhosts/martialcomp.com/venv/bin/python -c "
import sys
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
try:
    import passenger_wsgi
    if hasattr(passenger_wsgi, 'application'):
        print('✓ passenger_wsgi.application trouvé')
    else:
        print('✗ passenger_wsgi.application non trouvé')
except Exception as e:
    print(f'✗ Erreur import passenger_wsgi: {e}')
"

# 4. Vérifier la configuration Passenger d'Apache
echo ""
echo "4. Configuration Passenger dans Apache..."
grep -r "passenger" /etc/apache2/sites-enabled/ 2>/dev/null | grep -i "python" | head -5

# 5. Chercher les erreurs Passenger spécifiques
echo ""
echo "5. Dernières erreurs Passenger..."
grep -i "passenger" /var/log/apache2/error.log | tail -10

# 6. Tester avec une requête curl et capturer la réponse complète
echo ""
echo "6. Test avec curl pour voir l'erreur exacte..."
curl -s https://martialcomp.com | head -50

echo ""
echo "=== FIN DU DIAGNOSTIC ==="