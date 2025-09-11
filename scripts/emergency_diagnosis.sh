#!/bin/bash

# =============================================================================
# Diagnostic d'urgence pour voir les erreurs exactes Django
# =============================================================================

APP_DIR="/opt/martialcomp/app"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR: $1${NC}"
}

log "=== DIAGNOSTIC D'URGENCE DJANGO ==="

# 1. Voir les erreurs exactes
echo ""
echo "=== ERREURS DJANGO 500 ==="
echo "Test avec contenu de l'erreur 500:"
curl -s http://127.0.0.1:8000/privacy/ | head -50

echo ""
echo "=== ERREURS DJANGO 404 ==="
echo "Test avec contenu de l'erreur 404:"
curl -s http://127.0.0.1:8000/fr/ | head -50

# 2. Logs Django récents
echo ""
echo "=== LOGS DJANGO RÉCENTS ==="
find /tmp -name "django_*.log" -type f -exec ls -la {} \; | head -3
latest_log=$(find /tmp -name "django_*.log" -type f | head -1)
if [[ -n "$latest_log" ]]; then
    echo "Dernières lignes du log Django:"
    tail -20 "$latest_log"
fi

# 3. Test configuration Python direct
echo ""
echo "=== TEST CONFIGURATION PYTHON ==="
cd "$APP_DIR"
source venv/bin/activate

python << 'EOF'
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== DIAGNOSTIC DJANGO ===")

# Test des imports
try:
    from competitions.views.welcome import welcome
    print("✅ Import welcome OK")
except Exception as e:
    print(f"❌ Import welcome ERREUR: {e}")

try:
    from competitions.views.pages import privacy_policy_view
    print("✅ Import privacy_policy_view OK")
except Exception as e:
    print(f"❌ Import privacy_policy_view ERREUR: {e}")

# Test des templates
try:
    from django.template.loader import get_template
    template = get_template('competitions/welcome.html')
    print("✅ Template welcome.html trouvé")
except Exception as e:
    print(f"❌ Template welcome.html ERREUR: {e}")

try:
    template = get_template('competitions/pages/privacy_policy.html')
    print("✅ Template privacy_policy.html trouvé")
except Exception as e:
    print(f"❌ Template privacy_policy.html ERREUR: {e}")

# Test des URLs
try:
    from django.urls import reverse
    
    welcome_url = reverse('welcome')
    print(f"✅ URL welcome: {welcome_url}")
    
    privacy_url = reverse('privacy_policy')
    print(f"✅ URL privacy: {privacy_url}")
    
except Exception as e:
    print(f"❌ URLs ERREUR: {e}")

# Test middleware
from django.conf import settings
print(f"DEBUG: {settings.DEBUG}")
print(f"INSTALLED_APPS: {[app for app in settings.INSTALLED_APPS if 'competitions' in app or 'allauth' in app]}")
print(f"LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
print(f"USE_I18N: {settings.USE_I18N}")

print("=== FIN DIAGNOSTIC ===")
EOF

echo ""
log "Diagnostic terminé"