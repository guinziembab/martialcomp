#!/bin/bash
# Script de diagnostic approfondi pour l'erreur WSGI
# MartialComp - Diagnostic complet du problème

echo "🔍 DIAGNOSTIC APPROFONDI ERREUR WSGI"
echo "===================================="
echo

# Variables
PRODUCTION_DIR="/var/www/vhosts/martialcomp.com/httpdocs"

echo "1. VÉRIFICATION DES LOGS APACHE..."
echo "Dernières erreurs Apache:"
echo "----------------------------------------"
tail -20 /var/log/apache2/error.log | grep -E "(martialcomp|WSGI|Python|Error)" || echo "Aucune erreur récente trouvée"
echo "----------------------------------------"

echo
echo "2. TEST DJANGO COMPLET..."
cd "$PRODUCTION_DIR"

echo "Test 1 - Django check:"
python3 manage.py check --settings=config.settings.production 2>&1 | head -10

echo
echo "Test 2 - Import principal:"
python3 -c "
import sys, os
sys.path.insert(0, '$PRODUCTION_DIR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    import django
    django.setup()
    print('✅ Django setup OK')
    
    # Test import URLs principales
    from config.urls import urlpatterns
    print(f'✅ URLs principales OK - {len(urlpatterns)} patterns')
    
    # Test import URLs competitions
    from apps.competitions.urls import urlpatterns as comp_urls
    print(f'✅ URLs competitions OK - {len(comp_urls)} patterns')
    
except Exception as e:
    print(f'❌ Erreur Django: {e}')
    import traceback
    traceback.print_exc()
"

echo
echo "3. VÉRIFICATION STRUCTURE FICHIERS CRITIQUES..."
CRITICAL_FILES=(
    "config/urls.py"
    "config/wsgi.py"
    "apps/competitions/urls/__init__.py"
    "apps/competitions/urls/qr.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file existe"
        # Vérifier syntaxe
        python3 -m py_compile "$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "   ✅ Syntaxe OK"
        else
            echo "   ❌ ERREUR SYNTAXE"
            python3 -m py_compile "$file"
        fi
    else
        echo "❌ $file MANQUANT"
    fi
done

echo
echo "4. VÉRIFICATION WSGI..."
echo "Contenu wsgi.py (premières lignes):"
echo "--------------------------------"
head -15 config/wsgi.py | cat -n
echo "--------------------------------"

echo
echo "Test WSGI:"
python3 -c "
import sys, os
sys.path.insert(0, '$PRODUCTION_DIR')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

try:
    from config.wsgi import application
    print('✅ WSGI application OK')
except Exception as e:
    print(f'❌ WSGI ERROR: {e}')
    import traceback
    traceback.print_exc()
"

echo
echo "5. VÉRIFICATION PERMISSIONS..."
echo "Permissions du répertoire:"
ls -la "$PRODUCTION_DIR" | head -5

echo "Propriétaire des fichiers Python:"
find "$PRODUCTION_DIR" -name "*.py" -exec ls -l {} \; | head -3

echo
echo "6. VÉRIFICATION ENVIRONNEMENT VIRTUEL..."
echo "Python actuel: $(which python3)"
echo "Pip packages critique:"
pip list | grep -E "(Django|gunicorn|mod-wsgi)" || echo "Packages non trouvés"

echo
echo "7. PROCESSUS APACHE/WSGI..."
echo "Processus Apache:"
ps aux | grep apache | head -3
echo "Processus Python/WSGI:"
ps aux | grep python | head -3

echo
echo "8. CONFIGURATION APACHE WSGI..."
echo "Configuration Apache (recherche WSGI):"
grep -r "WSGI" /etc/apache2/ 2>/dev/null | head -5 || echo "Config WSGI non trouvée dans /etc/apache2/"

# Vérifier configuration Plesk
echo "Configuration Plesk WSGI:"
find /var/www/vhosts/martialcomp.com -name "*.conf" -exec grep -l "WSGI" {} \; 2>/dev/null | head -3

echo
echo "9. TEST MANUEL SIMPLE..."
echo "Test import basique:"
python3 -c "
import sys
sys.path.insert(0, '$PRODUCTION_DIR')
try:
    import config.settings.production
    print('✅ Settings production OK')
except Exception as e:
    print(f'❌ Settings error: {e}')

try:
    import apps.competitions
    print('✅ App competitions OK')
except Exception as e:
    print(f'❌ App competitions error: {e}')
"

echo
echo "🔍 DIAGNOSTIC TERMINÉ"
echo "=================="
echo
echo "SOLUTIONS POSSIBLES:"
echo "1. Si erreur dans config/wsgi.py:"
echo "   - Vérifier DJANGO_SETTINGS_MODULE"
echo "   - Vérifier les imports"
echo
echo "2. Si problème permissions:"
echo "   chown -R www-data:www-data $PRODUCTION_DIR"
echo "   chmod -R 755 $PRODUCTION_DIR"
echo
echo "3. Si problème environnement virtuel:"
echo "   source .venv/bin/activate"
echo "   pip install -r requirements.txt"
echo
echo "4. Si problème configuration Apache:"
echo "   Vérifier la configuration WSGI dans Plesk"
echo
echo "LOGS À SURVEILLER:"
echo "tail -f /var/log/apache2/error.log"
echo
echo "=================="