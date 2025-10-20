#!/bin/bash
# Vérifier si un middleware interfère avec la redirection

echo "================================================"
echo "🔍 VÉRIFICATION MIDDLEWARE ET REDIRECTION"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Liste des middlewares actifs..."
echo "==================================="
python3 -c "
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.production'
import django
django.setup()
from django.conf import settings
print('Middlewares actifs:')
for m in settings.MIDDLEWARE:
    print(f'  - {m}')
"

echo ""
echo "2️⃣ Vérification du OnboardingRedirectMiddleware..."
echo "================================================="
echo "📋 Logique du middleware:"
grep -A30 "__call__" apps/competitions/middleware/__init__.py | head -40

echo ""
echo "3️⃣ Test de connexion direct avec curl..."
echo "========================================"
echo "Simulons une connexion et voyons les redirections:"

# D'abord obtenir le token CSRF
echo "Récupération du token CSRF..."
CSRF=$(curl -s -c cookies.txt https://martialcomp.com/accounts/login/ | grep -oP 'csrfmiddlewaretoken.*?value="\K[^"]+' | head -1)
echo "Token CSRF: ${CSRF:0:10}..."

# Tenter la connexion
echo ""
echo "Tentative de connexion..."
RESPONSE=$(curl -s -L -b cookies.txt -c cookies.txt \
  -d "csrfmiddlewaretoken=$CSRF" \
  -d "login=DT_bguinziemba" \
  -d "password=AQWZSX123ok," \
  -X POST https://martialcomp.com/accounts/login/ \
  -w "\n\nHTTP_CODE:%{http_code}\nFINAL_URL:%{url_effective}\n")

echo "Réponse de connexion:"
echo "$RESPONSE" | tail -3

# Tester l'accès au dashboard
echo ""
echo "Test d'accès au dashboard après connexion..."
curl -s -b cookies.txt -L https://martialcomp.com/competitions/dashboard/ \
  -w "\n\nHTTP_CODE:%{http_code}\nFINAL_URL:%{url_effective}\n" | tail -3

# Nettoyer
rm -f cookies.txt

echo ""
echo "4️⃣ Vérification d'autres redirections possibles..."
echo "================================================="
echo "📋 Recherche de redirections dans le code:"
grep -r "redirect.*spectator" apps/competitions/ --include="*.py" | grep -v "__pycache__" | head -5

echo ""
echo "================================================"
echo "📊 ANALYSE"
echo "================================================"
echo ""
echo "Le problème peut venir de:"
echo "1. OnboardingRedirectMiddleware qui force une redirection"
echo "2. Une vue login personnalisée qui redirige mal"
echo "3. Un signal ou hook qui modifie le comportement"
echo ""

REMOTE_COMMANDS