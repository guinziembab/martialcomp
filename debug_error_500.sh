#!/bin/bash
# Script pour débugger l'erreur 500

echo "=== DEBUG ERREUR 500 ==="

ssh martialcomp-production << 'EOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Test direct de la vue..."
sudo -u www-data python3 << 'PYTHON_TEST'
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')

try:
    django.setup()
    
    # Tester l'import de la vue
    from apps.competitions.views.competitions import competition_detail
    print("✓ Import de competition_detail réussi")
    
    # Tester l'accès à la compétition
    from apps.competitions.models import Competition
    comp = Competition.objects.filter(id=4).first()
    if comp:
        print(f"✓ Compétition trouvée: {comp.title}")
    else:
        print("✗ Compétition ID=4 non trouvée")
        
except Exception as e:
    import traceback
    print(f"✗ Erreur: {type(e).__name__}: {e}")
    traceback.print_exc()
PYTHON_TEST

echo "2. Vérification des dernières requêtes dans les logs..."
tail -n 30 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_access.log | grep "/competitions/4"

echo "3. Activation temporaire du debug dans la vue..."
# Ajouter des logs de debug
sudo python3 << 'PYTHON_DEBUG'
with open('apps/competitions/views/competitions.py', 'r') as f:
    content = f.read()

# Ajouter du logging au début de competition_detail
if 'def competition_detail(request, pk):' in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def competition_detail(request, pk):' in line:
            # Insérer du debug après la définition
            indent = '    '
            debug_code = f'''
{indent}# DEBUG TEMPORAIRE
{indent}import logging
{indent}logger = logging.getLogger(__name__)
{indent}logger.error(f"DEBUG competition_detail: pk={{pk}}")
{indent}try:'''
            
            # Insérer le debug
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"""'):
                j += 1
            
            if j < len(lines):
                lines.insert(j + 1, debug_code)
                
                # Trouver la fin de la fonction pour ajouter except
                k = j + 2
                func_indent = len(lines[i]) - len(lines[i].lstrip())
                while k < len(lines):
                    if lines[k].strip() and len(lines[k]) - len(lines[k].lstrip()) == func_indent:
                        # Fin de la fonction
                        lines.insert(k, f'{indent}except Exception as e:')
                        lines.insert(k + 1, f'{indent}    logger.error(f"ERREUR competition_detail: {{type(e).__name__}}: {{e}}", exc_info=True)')
                        lines.insert(k + 2, f'{indent}    raise')
                        break
                    k += 1
                
                with open('apps/competitions/views/competitions.py', 'w') as f:
                    f.write('\n'.join(lines))
                print("✓ Debug ajouté à competition_detail")
                break
else:
    print("✗ competition_detail non trouvé")
PYTHON_DEBUG

echo "4. Redémarrage de Gunicorn..."
sudo pkill -HUP -f gunicorn

echo "5. Attente et test..."
sleep 3
curl -s https://martialcomp.com/fr/competitions/competitions/4/ | head -20

echo "6. Vérification des nouveaux logs..."
tail -n 20 /var/www/vhosts/martialcomp.com/httpdocs/logs/gunicorn_error.log | grep -E "DEBUG|ERREUR|ERROR"

EOF

echo ""
echo "=== ANALYSE TERMINÉE ==="