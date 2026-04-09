#!/bin/bash
# Vérifier les erreurs de template

echo "=== VÉRIFICATION ERREUR TEMPLATE ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérification du template competition detail..."
ls -la apps/competitions/templates/competitions/competition/detail*.html

echo "2. Test avec DEBUG=True temporairement..."
# Activer temporairement DEBUG pour voir l'erreur
sudo python3 << 'PYTHON_DEBUG'
# Sauvegarder la config actuelle
with open('config/settings/production.py', 'r') as f:
    content = f.read()

# Chercher DEBUG = False et le remplacer temporairement
if 'DEBUG = False' in content:
    new_content = content.replace('DEBUG = False', 'DEBUG = True  # TEMPORAIRE')
    with open('config/settings/production.py', 'w') as f:
        f.write(new_content)
    print("✓ DEBUG activé temporairement")
PYTHON_DEBUG

echo "3. Redémarrage rapide..."
sudo pkill -HUP -f gunicorn
sleep 2

echo "4. Test de la page..."
curl -s https://martialcomp.com/fr/competitions/competitions/4/ | grep -A20 -B5 "Exception\|Error\|Traceback" | head -50

echo "5. Restauration de DEBUG=False..."
sudo python3 << 'PYTHON_RESTORE'
with open('config/settings/production.py', 'r') as f:
    content = f.read()

if 'DEBUG = True  # TEMPORAIRE' in content:
    new_content = content.replace('DEBUG = True  # TEMPORAIRE', 'DEBUG = False')
    with open('config/settings/production.py', 'w') as f:
        f.write(new_content)
    print("✓ DEBUG désactivé")
PYTHON_RESTORE

echo "6. Vérification spécifique du problème..."
# Chercher si JudgeAssignment est utilisé dans le template
grep -r "JudgeAssignment" apps/competitions/templates/competitions/competition/ || echo "Pas de JudgeAssignment dans les templates"

echo "7. Test de la vue directement..."
sudo -u www-data python3 << 'PYTHON_VIEW'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.test import RequestFactory
from apps.competitions.views.competitions import competition_detail
from apps.competitions.models import Competition
from apps.users.models import User

try:
    # Créer une requête de test
    factory = RequestFactory()
    request = factory.get('/competitions/4/')
    
    # Simuler un utilisateur
    user = User.objects.first()
    request.user = user
    
    # Appeler la vue
    response = competition_detail(request, pk=4)
    print(f"✓ Vue retourne status: {response.status_code}")
    
except Exception as e:
    import traceback
    print(f"✗ Erreur dans la vue: {type(e).__name__}: {e}")
    traceback.print_exc()
PYTHON_VIEW

EOF

echo ""
echo "=== ANALYSE TERMINÉE ==="