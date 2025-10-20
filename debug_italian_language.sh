#!/bin/bash

# Script de debug spécifique pour le problème italien

echo "=== DEBUG DU PROBLÈME ITALIEN ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Vérifier la configuration
echo "1. CONFIGURATION DES LANGUES"
echo "============================"

/var/www/vhosts/martialcomp.com/venv/bin/python << 'CHECK_CONFIG'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.conf import settings

print("Langues configurées:")
for code, name in settings.LANGUAGES:
    print(f"  {code}: {name}")

print(f"\nLANGUAGE_CODE par défaut: {settings.LANGUAGE_CODE}")
print(f"Prefixe de langue dans URLs: {getattr(settings, 'PREFIX_DEFAULT_LANGUAGE', 'Non défini')}")
CHECK_CONFIG

# 2. Vérifier les fichiers de locale
echo ""
echo "2. FICHIERS DE TRADUCTION"
echo "========================="

echo "Structure locale/it/:"
if [ -d "locale/it" ]; then
    find locale/it -type f -name "*.po" -o -name "*.mo" | sort
else
    echo "⚠️ Répertoire locale/it/ n'existe pas!"
fi

echo ""
echo "Taille des fichiers:"
ls -lh locale/it/LC_MESSAGES/*.mo 2>/dev/null || echo "Pas de fichiers .mo"

# 3. Tester directement l'activation de l'italien
echo ""
echo "3. TEST D'ACTIVATION DIRECTE"
echo "============================"

/var/www/vhosts/martialcomp.com/venv/bin/python << 'TEST_IT'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.utils import translation
from django.utils.translation import gettext as _

# Test 1: Activer l'italien
print("Test 1: Activation de l'italien")
translation.activate('it')
current = translation.get_language()
print(f"Langue active: {current}")

# Test 2: Traduire quelques chaînes
print("\nTest 2: Traductions de base")
test_strings = [
    "Welcome",
    "Login", 
    "Logout",
    "Language",
    "Home"
]

for s in test_strings:
    translated = _(s)
    print(f"  '{s}' → '{translated}'")
    
# Test 3: Vérifier le fallback
from django.utils.translation import get_language_info
info = get_language_info('it')
print(f"\nInfo langue italienne: {info}")

# Test 4: Vérifier les chemins de traduction
from django.conf import settings
print(f"\nLOCALE_PATHS: {settings.LOCALE_PATHS}")
TEST_IT

# 4. Vérifier le middleware LocaleMiddleware
echo ""
echo "4. ORDRE DES MIDDLEWARES"
echo "======================="

grep -n "middleware" config/settings/base.py -A 20 | grep -E "Locale|Session|locale"

# 5. Créer un fichier de traduction minimal pour l'italien
echo ""
echo "5. CRÉATION D'UN FICHIER DE TRADUCTION MINIMAL"
echo "=============================================="

# Créer un fichier po minimal si nécessaire
cat > create_italian_minimal.py << 'CREATE_IT'
import os
os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')

# Créer le répertoire
os.makedirs('locale/it/LC_MESSAGES', exist_ok=True)

# Créer un fichier .po minimal
po_content = '''# Italian translations
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: it\\n"

msgid "Welcome"
msgstr "Benvenuto"

msgid "Login"
msgstr "Accesso"

msgid "Logout"
msgstr "Esci"

msgid "Language"
msgstr "Lingua"

msgid "Home"
msgstr "Home"

msgid "Dashboard"
msgstr "Pannello di controllo"
'''

with open('locale/it/LC_MESSAGES/django.po', 'w', encoding='utf-8') as f:
    f.write(po_content)

print("✅ Fichier .po italien créé")

# Compiler
import subprocess
result = subprocess.run([
    '/var/www/vhosts/martialcomp.com/venv/bin/python',
    'manage.py', 'compilemessages', '-l', 'it'
], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Fichier .mo compilé")
else:
    print(f"❌ Erreur de compilation: {result.stderr}")
CREATE_IT

/var/www/vhosts/martialcomp.com/venv/bin/python create_italian_minimal.py
rm create_italian_minimal.py

# 6. Vérifier les cookies
echo ""
echo "6. TEST AVEC CURL"
echo "================="

echo "Test changement vers italien:"
# Obtenir un cookie de session
COOKIES=$(curl -s -c - https://martialcomp.com/ | grep -E "csrftoken|sessionid" | awk '{print $6"="$7}' | tr '\n' '; ')

# Changer en italien
curl -X POST https://martialcomp.com/set_language/ \
    -H "Cookie: $COOKIES" \
    -d "language=it&next=/" \
    -s -D - | grep -E "Set-Cookie|Location" | head -5

echo ""
echo "============================================"
echo "DIAGNOSTIC TERMINÉ"
echo "============================================"
echo ""
echo "Points à vérifier:"
echo "1. Les fichiers .mo italiens existent-ils?"
echo "2. La langue italienne est-elle dans LANGUAGES?"
echo "3. Y a-t-il un fallback vers le français?"
echo ""
echo "Solutions possibles:"
echo "- Régénérer les fichiers de traduction italiens"
echo "- Vérifier PREFIX_DEFAULT_LANGUAGE dans settings"
echo "- Forcer la création de traductions minimales"
echo ""
echo "============================================"