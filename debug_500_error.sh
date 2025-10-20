#!/bin/bash
# Debug de l'erreur 500 avec plus de détails

echo "================================================"
echo "🔍 DEBUG ERREUR 500"
echo "================================================"
echo ""

# Test direct avec curl pour capturer l'erreur
echo "1️⃣ Test direct de l'URL..."
echo "=========================="
RESPONSE=$(curl -s -w "\nSTATUS:%{http_code}\n" https://martialcomp.com/fr/competitions/dashboard/federation/41/)
STATUS=$(echo "$RESPONSE" | grep "STATUS:" | cut -d: -f2)
echo "Status: $STATUS"

if [ "$STATUS" = "500" ]; then
    echo ""
    echo "2️⃣ Extraction du message d'erreur..."
    echo "==================================="
    # Chercher les patterns d'erreur Django
    if echo "$RESPONSE" | grep -q "NoReverseMatch"; then
        echo "❌ Erreur NoReverseMatch détectée:"
        echo "$RESPONSE" | grep -A3 "NoReverseMatch" | head -10
    fi
    
    if echo "$RESPONSE" | grep -q "TemplateDoesNotExist"; then
        echo "❌ Erreur TemplateDoesNotExist détectée:"
        echo "$RESPONSE" | grep -A3 "TemplateDoesNotExist" | head -10
    fi
    
    if echo "$RESPONSE" | grep -q "ImportError"; then
        echo "❌ Erreur ImportError détectée:"
        echo "$RESPONSE" | grep -A3 "ImportError" | head -10
    fi
    
    if echo "$RESPONSE" | grep -q "AttributeError"; then
        echo "❌ Erreur AttributeError détectée:"
        echo "$RESPONSE" | grep -A3 "AttributeError" | head -10
    fi
    
    # Si DEBUG est activé, extraire le traceback
    if echo "$RESPONSE" | grep -q "Traceback"; then
        echo ""
        echo "📋 Traceback complet:"
        echo "$RESPONSE" | grep -A20 "Traceback" | head -30
    fi
fi

echo ""
echo "3️⃣ Vérification directe sur le serveur..."
echo "======================================="
ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

# Vérifier les dernières erreurs
echo "Dernières lignes des logs d'erreur:"
if [ -f /var/log/apache2/error.log ]; then
    sudo tail -20 /var/log/apache2/error.log | grep -E "(ERROR|federation)" | tail -10
fi

echo ""
echo "Journalctl dernières erreurs:"
sudo journalctl -u martialcomp -n 100 --no-pager | grep -B2 -A5 "Internal Server Error" | tail -20

echo ""
echo "Test Python direct:"
# Tester directement avec Python
/usr/bin/python3 << 'PYTHON'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
django.setup()

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

# Tester toutes les URLs federation
urls_to_test = [
    'federation_manage_clubs',
    'federation_manage_judges', 
    'federation_manage_competitions',
    'federation_manage_licenses',
    'federation_manage_certifications',
    'federation_manage_reports',
    'federation_manage_settings',
]

print("Test des URLs federation:")
for url_name in urls_to_test:
    try:
        url = reverse(f'competitions:dashboard:{url_name}', kwargs={'federation_id': 41})
        print(f"✅ {url_name}: {url}")
    except NoReverseMatch as e:
        print(f"❌ {url_name}: {e}")
PYTHON

EOF

echo ""
echo "================================================"
echo "📊 ANALYSE"
echo "================================================"