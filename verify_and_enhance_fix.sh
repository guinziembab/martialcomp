#\!/bin/bash
# Vérifier et améliorer le fix

echo "=== VÉRIFICATION ET AMÉLIORATION DU FIX ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier le template create.html..."
grep -n "extends\ < /dev/null | dropdown\|extra_js" apps/competitions/templates/competitions/competition/create.html | head -10

echo "2. Chercher les conflits JavaScript potentiels..."
grep -n "event.preventDefault\|stopPropagation\|dropdown" apps/competitions/templates/competitions/competition/create.html | head -20

echo "3. Améliorer le fix avec une solution plus robuste..."
sudo python3 << 'PYTHON_ENHANCE'
with open('apps/competitions/templates/base.html', 'r') as f:
    content = f.read()

# Remplacer le fix existant par une version améliorée
if 'Fix temporaire pour les dropdowns' in content:
    # Supprimer l'ancien fix
    start = content.find('<\!-- Fix temporaire pour les dropdowns -->')
    end = content.find('</script>', start) + len('</script>')
    content = content[:start] + content[end + 1:]

# Ajouter le nouveau fix amélioré
enhanced_fix = '''
    <\!-- Fix amélioré pour les dropdowns Bootstrap 5 -->
    <script>
    (function() {
        // Attendre que Bootstrap soit chargé
        function initDropdowns() {
            if (typeof bootstrap === 'undefined') {
                setTimeout(initDropdowns, 50);
                return;
            }
            
            // Réinitialiser tous les dropdowns
            document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(function(dropdownToggle) {
                // Supprimer les anciens event listeners
                var newDropdown = dropdownToggle.cloneNode(true);
                dropdownToggle.parentNode.replaceChild(newDropdown, dropdownToggle);
                
                // Créer une nouvelle instance
                new bootstrap.Dropdown(newDropdown);
            });
            
            // Fix spécifique pour le dropdown utilisateur
            var userDropdown = document.getElementById('userDropdown');
            if (userDropdown) {
                userDropdown.addEventListener('click', function(e) {
                    e.preventDefault();
                    var dropdownMenu = this.nextElementSibling;
                    if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
                        dropdownMenu.classList.toggle('show');
                    }
                });
                
                // Fermer le dropdown en cliquant ailleurs
                document.addEventListener('click', function(e) {
                    if (\!userDropdown.contains(e.target)) {
                        var dropdownMenu = userDropdown.nextElementSibling;
                        if (dropdownMenu && dropdownMenu.classList.contains('show')) {
                            dropdownMenu.classList.remove('show');
                        }
                    }
                });
            }
            
            console.log('Dropdowns Bootstrap 5 initialisés avec succès');
        }
        
        // Lancer l'initialisation
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initDropdowns);
        } else {
            initDropdowns();
        }
    })();
    </script>
'''

content = content.replace('</body>', enhanced_fix + '\n</body>')

with open('apps/competitions/templates/base.html', 'w') as f:
    f.write(content)

print("✓ Fix amélioré appliqué")
PYTHON_ENHANCE

echo "4. Vérifier s'il y a des CSS qui pourraient bloquer..."
grep -n "pointer-events\|user-select\|disabled" apps/competitions/static/competitions/css/*.css 2>/dev/null | grep -i "dropdown\|nav" | head -10

echo "5. Redémarrage final..."
sudo pkill -HUP -f gunicorn
sleep 2

echo "✓ Fix dropdown amélioré appliqué"
echo ""
echo "Le dropdown profil devrait maintenant fonctionner correctement."
echo "Si le problème persiste, il faudrait vérifier la console JavaScript du navigateur."

SSHEOF

echo ""
echo "=== TERMINÉ ==="
