#!/bin/bash

# Script pour tester le changement de langue

echo "=== TEST CHANGEMENT DE LANGUE ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# Obtenir un cookie de session et CSRF token
echo "1. Obtention des cookies..."
RESPONSE=$(curl -s -c cookies.txt -w "\n%{http_code}" https://martialcomp.com/)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
echo "   Code HTTP: $HTTP_CODE"

# Extraire le CSRF token
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')
echo "   CSRF Token: $CSRF"

# Tester chaque langue
echo ""
echo "2. Test de changement de langue:"
echo "================================"

for lang in fr en it es pt ar; do
    echo ""
    echo "→ Changement vers: $lang"
    
    # Faire la requête POST
    RESPONSE=$(curl -X POST https://martialcomp.com/set_language/ \
        -b cookies.txt \
        -c cookies.txt \
        -H "X-CSRFToken: $CSRF" \
        -H "Referer: https://martialcomp.com/" \
        -d "language=$lang" \
        -d "next=/" \
        -s -w "\nHTTP_CODE:%{http_code}" \
        -L)
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    
    # Vérifier le cookie de langue
    LANG_COOKIE=$(grep django_language cookies.txt | awk '{print $7}')
    
    echo "   Code HTTP: $HTTP_CODE"
    echo "   Cookie langue: $LANG_COOKIE"
    
    # Tester l'accès à la page dans cette langue
    echo "   Test accès /$lang/:"
    curl -s -b cookies.txt -o /dev/null -w "   → Code: %{http_code}\n" "https://martialcomp.com/$lang/"
done

# Nettoyer
rm -f cookies.txt

echo ""
echo "3. Vérification des traductions compilées:"
echo "=========================================="

source /var/www/vhosts/martialcomp.com/venv/bin/activate

python << 'PYTHON_TEST'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.utils import translation
from django.utils.translation import gettext as _

test_langs = ['fr', 'en', 'it', 'es', 'pt', 'ar']
test_words = {
    'Welcome': {
        'fr': 'Bienvenue',
        'en': 'Welcome',
        'it': 'Benvenuto',
        'es': 'Bienvenido',
        'pt': 'Bem-vindo',
        'ar': 'مرحبا'
    }
}

print("\nTest des traductions:")
for lang in test_langs:
    translation.activate(lang)
    current = translation.get_language()
    translated = _('Welcome')
    expected = test_words['Welcome'].get(lang, 'Welcome')
    status = "✓" if translated != 'Welcome' else "✗"
    print(f"  {lang}: '{translated}' {status} (attendu: '{expected}')")
PYTHON_TEST

echo ""
echo "=========================================="
echo "FIN DU TEST"