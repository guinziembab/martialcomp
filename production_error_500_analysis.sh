#!/bin/bash
# Script complet d'analyse des erreurs 500 sur le serveur de production
# À exécuter sur le serveur via SSH

echo "====================================================================="
echo "ANALYSE COMPLÈTE DES ERREURS 500 - MARTIALCOMP PRODUCTION"
echo "Date: $(date)"
echo "====================================================================="
echo ""

# 1. ERREURS APACHE RÉCENTES
echo "1. ANALYSE DES LOGS APACHE (dernières 2 heures)"
echo "---------------------------------------------------------------------"
sudo tail -1000 /var/log/apache2/error.log | grep -E "(martialcomp|Discipline|get|Practitioner|500|Error|ERROR|Traceback)" -A 5 -B 2 | tail -100
echo ""

# 2. ERREURS DANS LES AUTRES LOGS
echo "2. RECHERCHE DANS TOUS LES LOGS APACHE"
echo "---------------------------------------------------------------------"
sudo grep -r "martialcomp.*500\|Discipline.*get\|Practitioner" /var/log/apache2/ --include="*.log" | tail -20
echo ""

# 3. VÉRIFIER L'ENVIRONNEMENT PYTHON
echo "3. ENVIRONNEMENT PYTHON ET DJANGO"
echo "---------------------------------------------------------------------"
cd /var/www/vhosts/martialcomp.com/httpdocs

# Chercher l'environnement virtuel
if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "Python utilisé: $PYTHON_BIN"
$PYTHON_BIN --version

# Vérifier Django
echo ""
echo "Test import Django et vérification de la configuration:"
$PYTHON_BIN -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
print('Django version:', django.get_version())

try:
    django.setup()
    print('✓ Django setup réussi')
except Exception as e:
    print('✗ Erreur Django setup:', e)

# Test import Discipline
try:
    from apps.competitions.models import Discipline
    print('✓ Import Discipline OK')
    
    # Vérifier si Discipline a une méthode get
    if hasattr(Discipline, 'get'):
        print('⚠️  ATTENTION: Discipline a une méthode get() personnalisée!')
    else:
        print('✓ Discipline n\'a pas de méthode get() personnalisée')
        
    # Test Discipline.objects.get
    try:
        Discipline.objects.first()
        print('✓ Discipline.objects fonctionne correctement')
    except Exception as e:
        print('✗ Erreur avec Discipline.objects:', e)
        
except Exception as e:
    print('✗ Erreur import Discipline:', e)

# Test import Practitioner
try:
    from apps.competitions.models import Practitioner
    print('✓ Import Practitioner OK')
except Exception as e:
    print('✗ Erreur import Practitioner:', e)
"

echo ""

# 4. VÉRIFIER LES FICHIERS CRITIQUES
echo "4. VÉRIFICATION DES FICHIERS CRITIQUES"
echo "---------------------------------------------------------------------"
echo "passenger_wsgi.py:"
if [ -f "passenger_wsgi.py" ]; then
    echo "✓ Fichier trouvé"
    echo "Dernière modification: $(stat -c %y passenger_wsgi.py)"
    echo "Premières lignes:"
    head -10 passenger_wsgi.py
else
    echo "✗ passenger_wsgi.py MANQUANT!"
fi

echo ""
echo "wsgi_startup_fix.py:"
if [ -f "wsgi_startup_fix.py" ]; then
    echo "✓ Fichier trouvé"
    cat wsgi_startup_fix.py
else
    echo "✗ wsgi_startup_fix.py non trouvé (référencé dans passenger_wsgi.py)"
fi

echo ""

# 5. TEST RAPIDE DES URLS
echo "5. TEST DES URLS PROBLÉMATIQUES"
echo "---------------------------------------------------------------------"
echo "Test avec curl (local):"

# Tester l'URL admin
echo "Test /admin/:"
curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" http://localhost/admin/

# Tester d'autres URLs
echo "Test /dashboard/:"
curl -s -o /dev/null -w "HTTP Code: %{http_code}\n" http://localhost/dashboard/

echo ""

# 6. PROCESSUS APACHE/PASSENGER
echo "6. ÉTAT DES PROCESSUS"
echo "---------------------------------------------------------------------"
echo "Processus Apache:"
ps aux | grep -E "(apache2|httpd)" | grep -v grep | wc -l
echo ""
echo "Processus Passenger:"
ps aux | grep -i passenger | grep -v grep | wc -l
echo ""

# 7. MÉMOIRE ET RESSOURCES
echo "7. UTILISATION DES RESSOURCES"
echo "---------------------------------------------------------------------"
free -h
echo ""
df -h | grep -E "(/$|httpdocs)"
echo ""

# 8. PERMISSIONS
echo "8. PERMISSIONS DES FICHIERS CRITIQUES"
echo "---------------------------------------------------------------------"
ls -la /var/www/vhosts/martialcomp.com/httpdocs/passenger_wsgi.py
ls -la /var/www/vhosts/martialcomp.com/httpdocs/config/settings/
ls -la /var/www/vhosts/martialcomp.com/httpdocs/.env.production 2>/dev/null || echo ".env.production non trouvé"
echo ""

# 9. TEST DIRECT DU PROBLÈME
echo "9. TEST DIRECT DU PROBLÈME DISCIPLINE.GET()"
echo "---------------------------------------------------------------------"
cd /var/www/vhosts/martialcomp.com/httpdocs
$PYTHON_BIN -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from apps.competitions.models import Discipline
from django.contrib import admin

print('Test accès direct:')
try:
    # Test comme dans l'erreur
    discipline = Discipline.get(pk=1)
    print('✗ Discipline.get() fonctionne (ne devrait pas!)')
except AttributeError as e:
    print('✓ AttributeError attendue:', e)
except Exception as e:
    print('? Autre erreur:', type(e).__name__, e)

print('\nTest correct:')
try:
    discipline = Discipline.objects.get(pk=1)
    print('✓ Discipline.objects.get() fonctionne')
except Discipline.DoesNotExist:
    print('✓ Discipline avec pk=1 n\'existe pas (normal)')
except Exception as e:
    print('✗ Erreur:', e)
"

echo ""
echo "====================================================================="
echo "FIN DE L'ANALYSE - Recherchez 'AttributeError' et 'Discipline.get'"
echo "====================================================================="