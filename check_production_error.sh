#!/bin/bash

# Script de vérification rapide des erreurs sur le serveur de production

echo "=== DIAGNOSTIC RAPIDE ERREUR 500 ==="
echo ""

# 1. Dernières erreurs Apache (uniquement les plus récentes)
echo "1. Dernières erreurs Apache :"
echo "------------------------------"
sudo tail -30 /var/log/apache2/error.log | grep -E "(Error|ERROR|Exception|Traceback|Fatal)" -A 3 | tail -20

echo ""
echo "2. Test Python et Django :"
echo "------------------------------"
cd /var/www/vhosts/martialcomp.com/httpdocs

# Vérifier Python
python3 --version

# Test rapide Django
python3 -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
try:
    import django
    django.setup()
    print('✓ Django chargé avec succès')
    
    # Test import des modèles problématiques
    from apps.competitions.models import Discipline
    print('✓ Modèle Discipline importé')
    
    # Vérifier si Discipline.get existe
    if hasattr(Discipline, 'get'):
        print('⚠️  ERREUR: Discipline.get() existe - ceci est incorrect!')
    else:
        print('✓ Discipline.get() n\'existe pas (correct)')
        
except Exception as e:
    print(f'✗ Erreur: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "3. Fichiers critiques :"
echo "------------------------------"
# Vérifier la présence des fichiers importants
for file in "passenger_wsgi.py" ".env.production" "wsgi_startup_fix.py"; do
    if [ -f "$file" ]; then
        echo "✓ $file existe"
    else
        echo "✗ $file MANQUANT"
    fi
done

echo ""
echo "4. Test direct de l'application :"
echo "------------------------------"
# Test avec curl local
curl -s -o /dev/null -w "Code HTTP local : %{http_code}\n" http://localhost:8000/ 2>/dev/null || echo "Pas de serveur local"

echo ""
echo "=== FIN DU DIAGNOSTIC ==="