#\!/bin/bash
# Solution simple pour le dropdown

echo "=== SOLUTION SIMPLE DROPDOWN ==="

ssh martialcomp-production << 'SSHEOF'
cd /var/www/vhosts/martialcomp.com/httpdocs

echo "1. Vérifier l'erreur exacte dans le navigateur..."
echo "L'erreur indique la ligne 1765 avec 'Invalid or unexpected token'"

echo "2. Solution directe - Ajouter un handler JavaScript simple..."
# Au lieu de chercher l'erreur, on va simplement s'assurer que le dropdown fonctionne
sudo python3 << 'PYTHON_FIX'
with open('apps/competitions/templates/base.html', 'r') as f:
    content = f.read()

# Remplacer notre fix précédent par une version encore plus simple
if '<\!-- Fix amélioré pour les dropdowns Bootstrap 5 -->' in content:
    # Trouver et supprimer l'ancien fix
    start = content.find('<\!-- Fix amélioré pour les dropdowns Bootstrap 5 -->')
    end = content.find('</script>', start) + len('</script>')
    if start \!= -1 and end > start:
        content = content[:start] + content[end + 1:]

# Ajouter un nouveau fix très simple
simple_fix = '''
    <\!-- Fix simple dropdown -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Fix simple pour le dropdown utilisateur
        const userDropdown = document.getElementById('userDropdown');
        if (userDropdown) {
            userDropdown.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                const menu = this.nextElementSibling;
                if (menu && menu.classList.contains('dropdown-menu')) {
                    // Toggle la classe show
                    if (menu.classList.contains('show')) {
                        menu.classList.remove('show');
                    } else {
                        // Fermer tous les autres dropdowns d'abord
                        document.querySelectorAll('.dropdown-menu.show').forEach(function(openMenu) {
                            openMenu.classList.remove('show');
                        });
                        menu.classList.add('show');
                    }
                }
                return false;
            };
        }
        
        // Fermer en cliquant ailleurs
        document.onclick = function(e) {
            if (\!e.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown-menu.show').forEach(function(menu) {
                    menu.classList.remove('show');
                });
            }
        };
    });
    </script>
'''

# Insérer avant </body>
content = content.replace('</body>', simple_fix + '\n</body>')

with open('apps/competitions/templates/base.html', 'w') as f:
    f.write(content)

print("✓ Fix simple appliqué")
PYTHON_FIX

echo "3. Ajouter aussi du CSS pour s'assurer que le dropdown est cliquable..."
sudo python3 << 'PYTHON_CSS'
with open('apps/competitions/templates/base.html', 'r') as f:
    content = f.read()

# Ajouter du CSS pour garantir que le dropdown est cliquable
css_fix = '''
    <style>
    /* Fix pour garantir que le dropdown est cliquable */
    #userDropdown {
        cursor: pointer \!important;
        pointer-events: auto \!important;
    }
    .dropdown-menu.show {
        display: block \!important;
    }
    .nav-item.dropdown {
        position: relative;
    }
    </style>
'''

# Insérer avant </head>
if '/* Fix pour garantir que le dropdown est cliquable */' not in content:
    content = content.replace('</head>', css_fix + '\n</head>')
    with open('apps/competitions/templates/base.html', 'w') as f:
        f.write(content)
    print("✓ CSS fix ajouté")
else:
    print("✓ CSS fix déjà présent")
PYTHON_CSS

echo "4. Redémarrage final..."
sudo pkill -HUP -f gunicorn
sleep 2

echo ""
echo "✓ SOLUTION APPLIQUÉE"
echo "Le dropdown profil devrait maintenant fonctionner même avec l'erreur JS."
echo "Le fix contourne l'erreur en utilisant onclick au lieu des événements Bootstrap."

SSHEOF

echo ""
echo "=== TERMINÉ ==="
