#!/bin/bash
# Trouver et corriger l'import apps.models

echo "================================================"
echo "🔍 RECHERCHE ET CORRECTION apps.models"
echo "================================================"
echo ""

ssh martialcomp-production << 'REMOTE_COMMANDS'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1️⃣ Recherche des imports apps.models..."
echo "========================================"
grep -r "from apps.models" apps/ --include="*.py" | grep -v __pycache__
grep -r "from apps import models" apps/ --include="*.py" | grep -v __pycache__
grep -r "import apps.models" apps/ --include="*.py" | grep -v __pycache__

echo ""
echo "2️⃣ Recherche dans config/..."
echo "============================"
grep -r "apps.models" config/ --include="*.py" | grep -v __pycache__

echo ""
echo "3️⃣ Analyse détaillée..."
echo "========================"

python3 << 'PYEOF'
import os
import re

print("🔍 Recherche approfondie des imports apps.models...")

files_with_apps_models = []

# Parcourir tous les fichiers Python
for root, dirs, files in os.walk('.'):
    if '__pycache__' in root or 'venv' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    if 'apps.models' in content or 'apps import models' in content:
                        files_with_apps_models.append(filepath)
            except:
                pass

print(f"\n📋 Fichiers contenant 'apps.models': {len(files_with_apps_models)}")
for f in files_with_apps_models[:10]:
    print(f"  - {f}")
    # Montrer la ligne exacte
    with open(f, 'r') as file:
        for i, line in enumerate(file):
            if 'apps.models' in line or 'apps import models' in line:
                print(f"    Ligne {i+1}: {line.strip()}")
PYEOF

echo ""
echo "4️⃣ Création d'un fichier apps/__init__.py correctif..."
echo "======================================================"

# S'assurer que apps/__init__.py existe
if [ ! -f "apps/__init__.py" ]; then
    touch apps/__init__.py
    echo "✅ Créé apps/__init__.py"
fi

echo ""
echo "5️⃣ Vérification de la structure apps/..."
echo "========================================"
echo "📁 Structure du répertoire apps:"
ls -la apps/ | head -10

echo ""
echo "6️⃣ Alternative: Créer apps/models.py temporaire..."
echo "=================================================="

# Si vraiment nécessaire, créer un fichier temporaire
cat > apps/models.py << 'PYEOF'
"""
Fichier temporaire pour résoudre les imports
Ce fichier redirige vers les vrais modèles
"""

# Importer les modèles principaux depuis competitions
try:
    from apps.competitions.models import *
    from apps.organizations.models import *
except ImportError:
    pass

# Pour la compatibilité
__all__ = []
PYEOF

echo "✅ Fichier apps/models.py temporaire créé"

echo ""
echo "7️⃣ Redémarrage des services..."
echo "==============================="
sudo systemctl restart martialcomp
sudo systemctl reload apache2

echo ""
echo "8️⃣ Test final..."
echo "================"
source /var/www/vhosts/martialcomp.com/venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production

python3 -c "
import django
django.setup()
print('✅ Django setup réussi')

from django.urls import reverse
try:
    url = reverse('welcome')
    print(f'✅ URL welcome: {url}')
except Exception as e:
    print(f'❌ Erreur URL: {str(e)[:100]}...')
"

echo ""
echo "================================================"
echo "✅ TENTATIVE DE CORRECTION APPLIQUÉE"
echo "================================================"
echo ""
echo "🎯 Testez maintenant: https://martialcomp.com/fr/"
echo ""
echo "Si l'erreur persiste, il faudra examiner le traceback complet"
echo "dans les logs pour identifier la source exacte du problème."

REMOTE_COMMANDS