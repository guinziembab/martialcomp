#\!/bin/bash
# Recherche approfondie du template update

echo "=== RECHERCHE APPROFONDIE TEMPLATE UPDATE ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Recherche du render dans competition_update..."
sed -n '/def competition_update/,/^def /p' apps/competitions/views/competitions.py  < /dev/null |  grep -B2 -A2 "render" | tail -20

echo "2. Recherche de tous les templates competition form..."
find apps/competitions/templates -name "*.html" | xargs grep -l "competition.*form\|form.*competition" | grep -v ".py" | head -10

echo "3. Identifier le template exact..."
# Il est probable que ce soit competition_form.html ou similar
ls -la apps/competitions/templates/competitions/competition/*form*.html 2>/dev/null || echo "Pas de *form*.html dans competition/"

echo "4. Chercher dans les templates club..."
ls -la apps/competitions/templates/competitions/club/*competition*.html | grep -E "form|update|edit" | head -10

echo "5. Test direct - Ajouter le fix JS à base.html temporairement..."
# Sauvegarder base.html
cp apps/competitions/templates/base.html apps/competitions/templates/base.html.backup_dropdown_fix

# Ajouter le script de fix avant </body>
sudo python3 << 'PYTHON_FIX'
with open('apps/competitions/templates/base.html', 'r') as f:
    content = f.read()

# Chercher où ajouter le script (avant </body>)
if '</body>' in content and 'Fix pour les dropdowns Bootstrap' not in content:
    fix_script = '''
    <\!-- Fix temporaire pour les dropdowns -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Fix pour les dropdowns Bootstrap 5
        setTimeout(function() {
            var dropdownElementList = [].slice.call(document.querySelectorAll('[data-bs-toggle="dropdown"]'));
            dropdownElementList.forEach(function(dropdownToggleEl) {
                // Forcer la réinitialisation
                dropdownToggleEl.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    var dropdown = bootstrap.Dropdown.getInstance(dropdownToggleEl) || new bootstrap.Dropdown(dropdownToggleEl);
                    dropdown.toggle();
                });
            });
            console.log('Dropdowns fix appliqué');
        }, 100);
    });
    </script>
'''
    content = content.replace('</body>', fix_script + '\n</body>')
    
    with open('apps/competitions/templates/base.html', 'w') as f:
        f.write(content)
    print("✓ Fix dropdown ajouté à base.html")
else:
    print("✗ Impossible d'ajouter le fix ou déjà présent")
PYTHON_FIX

echo "6. Redémarrage pour appliquer les changements..."
sudo pkill -HUP -f gunicorn

echo "✓ Fix appliqué - Les dropdowns devraient fonctionner maintenant"

SSHEOF

echo ""
echo "=== FIN ==="
