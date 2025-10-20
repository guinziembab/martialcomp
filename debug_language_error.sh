#!/bin/bash

# Script de debug pour l'erreur 500 sur set_language

echo "=== DEBUG DE L'ERREUR 500 SET_LANGUAGE ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Capturer l'erreur exacte
echo "1. CAPTURE DE L'ERREUR EXACTE"
echo "============================="

# Créer un script Python pour tester
cat > test_set_language.py << 'TEST_SCRIPT'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.views.i18n import set_language
from django.http import QueryDict

print("Test de la vue set_language...")

try:
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.post('/set_language/', {'language': 'en', 'next': '/'})
    
    # Ajouter la session (nécessaire pour CSRF)
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    # Ajouter CSRF token
    from django.middleware.csrf import get_token
    request.META['CSRF_COOKIE'] = get_token(request)
    
    print(f"Request créée: {request.method} {request.path}")
    print(f"POST data: {dict(request.POST)}")
    
    # Appeler la vue
    response = set_language(request)
    
    print(f"✅ Réponse: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
except Exception as e:
    print(f"❌ Erreur: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
TEST_SCRIPT

/var/www/vhosts/martialcomp.com/venv/bin/python test_set_language.py

rm test_set_language.py

echo ""

# 2. Vérifier les imports dans urls.py
echo "2. VÉRIFICATION DES IMPORTS"
echo "==========================="

echo "Imports dans config/urls.py:"
grep -E "^from|^import" config/urls.py | grep -E "i18n|set_language" | head -10

echo ""

# 3. Tester avec curl et capturer la réponse complète
echo "3. TEST AVEC CURL"
echo "================="

echo "Récupération du CSRF token..."
# Obtenir d'abord un cookie de session et le CSRF token
COOKIES=$(curl -s -c - https://martialcomp.com/ | grep -E "csrftoken|sessionid" | awk '{print $6"="$7}' | tr '\n' '; ')

echo "Test POST avec cookies:"
curl -X POST https://martialcomp.com/set_language/ \
    -H "Cookie: $COOKIES" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -H "X-Requested-With: XMLHttpRequest" \
    -d "language=en&next=/" \
    -s -D - | head -20

echo ""

# 4. Analyser les logs en temps réel
echo "4. ANALYSE DES LOGS"
echo "==================="

echo "Dernières erreurs liées à set_language:"
grep -A 20 -B 5 "set_language\|/set_language/\|500" logs/django.log | tail -50

echo ""

# 5. Vérifier si c'est un problème de module manquant
echo "5. VÉRIFICATION DES MODULES"
echo "==========================="

/var/www/vhosts/martialcomp.com/venv/bin/python << 'CHECK_MODULES'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

print("Vérification des imports critiques...")

try:
    from django.views import i18n
    print("✅ django.views.i18n importé")
    
    from django.conf import settings
    print(f"✅ settings importés")
    print(f"   - USE_I18N: {settings.USE_I18N}")
    print(f"   - LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
    
    # Vérifier les langues qui posent problème
    problematic_langs = ['am', 'zu', 'yo']
    current_langs = [code for code, _ in settings.LANGUAGES]
    
    for lang in problematic_langs:
        if lang in current_langs:
            print(f"⚠️  Langue problématique détectée: {lang}")
    
except Exception as e:
    print(f"❌ Erreur d'import: {e}")
CHECK_MODULES

echo ""
echo "============================================"
echo "DEBUG TERMINÉ"
echo "============================================"
echo ""
echo "Si l'erreur persiste, vérifiez:"
echo "1. Les langues problématiques (am, zu, yo) dans LANGUAGES"
echo "2. Le middleware OnboardingRedirectMiddleware"
echo "3. Les permissions sur les fichiers de locale/"
echo ""
echo "============================================"