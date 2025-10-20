#!/bin/bash

# Script pour rediriger vers le vrai système de grades

echo "=== REDIRECTION VERS LE VRAI SYSTÈME DE GRADES ==="
echo ""

cd /var/www/vhosts/martialcomp.com/httpdocs

# 1. Analyser la situation
echo "1. ANALYSE DE LA SITUATION ACTUELLE"
echo "==================================="

echo "Vérification des vues grades disponibles:"
echo ""

# Vérifier la vue temporaire
echo "Vue temporaire (competitions):"
ls -la apps/competitions/views/grades_management.py 2>/dev/null && echo "✓ Existe" || echo "✗ N'existe pas"

echo ""
echo "App grades (système réel):"
ls -la apps/grades/views/dashboard.py 2>/dev/null && echo "✓ dashboard.py existe" || echo "✗ dashboard.py n'existe pas"
ls -la apps/grades/urls.py 2>/dev/null && echo "✓ urls.py existe" || echo "✗ urls.py n'existe pas"

echo ""

# 2. Vérifier les URLs de l'app grades
echo "2. VÉRIFICATION DES URLS DE L'APP GRADES"
echo "========================================"

if [ -f "apps/grades/urls.py" ]; then
    echo "Contenu des URLs grades:"
    grep -E "path|name=" apps/grades/urls.py | head -20
fi

echo ""

# 3. Modifier la vue temporaire pour rediriger
echo "3. MODIFICATION DE LA VUE TEMPORAIRE"
echo "===================================="

# Remplacer la vue temporaire par une redirection
cat > apps/competitions/views/grades_management.py << 'EOF'
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

@login_required
def grades_management(request):
    """Redirection vers le vrai système de grades"""
    # Rediriger vers le dashboard grades de l'app grades
    return redirect('grades:dashboard')
EOF

echo "✓ Vue modifiée pour rediriger vers grades:dashboard"

echo ""

# 4. Vérifier que grades:dashboard fonctionne
echo "4. TEST DE L'URL GRADES:DASHBOARD"
echo "================================="

/var/www/vhosts/martialcomp.com/venv/bin/python << 'PYTHON_EOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()

from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

try:
    url = reverse('grades:dashboard')
    print(f"✓ URL grades:dashboard trouvée: {url}")
    
    # Vérifier que la vue existe
    from apps.grades.views.dashboard import grades_dashboard
    print("✓ Vue grades_dashboard existe et est importable")
    
    # Vérifier les permissions requises
    import inspect
    source = inspect.getsource(grades_dashboard)
    if 'permission_required' in source:
        print("⚠️ Note: La vue nécessite des permissions spécifiques")
    if 'club_manager_required' in source:
        print("⚠️ Note: La vue nécessite d'être manager de club")
        
except NoReverseMatch:
    print("✗ URL grades:dashboard non trouvée")
except ImportError as e:
    print(f"✗ Erreur d'import: {e}")
except Exception as e:
    print(f"✗ Erreur: {e}")
PYTHON_EOF

echo ""

# 5. Alternative : Mettre à jour directement le template
echo "5. ALTERNATIVE : MISE À JOUR DIRECTE DU TEMPLATE"
echo "==============================================="

# Sauvegarder le template
cp apps/competitions/templates/competitions/dashboard/club.html apps/competitions/templates/competitions/dashboard/club.html.bak2

# Modifier le template pour pointer directement vers grades:dashboard
sed -i 's/{% url .competitions:grades_management. %}/{% url "grades:dashboard" %}/g' apps/competitions/templates/competitions/dashboard/club.html

echo "✓ Template mis à jour pour pointer vers grades:dashboard"

echo ""

# 6. Redémarrer le service
echo "6. REDÉMARRAGE DU SERVICE"
echo "========================="

systemctl restart martialcomp.service
sleep 3

if systemctl is-active --quiet martialcomp.service; then
    echo "✓ Service actif"
else
    echo "❌ Service inactif"
fi

echo ""

# 7. Instructions
echo "============================================"
echo "REDIRECTION CONFIGURÉE"
echo "============================================"
echo ""
echo "Le système a été configuré pour utiliser le vrai"
echo "module de grades au lieu de la page temporaire."
echo ""
echo "Deux approches ont été appliquées:"
echo "1. La vue temporaire redirige maintenant vers grades:dashboard"
echo "2. Le template pointe directement vers grades:dashboard"
echo ""
echo "⚠️ IMPORTANT: Si vous obtenez une erreur de permissions,"
echo "   vérifiez que l'utilisateur TESTBGA_USER1 a les permissions"
echo "   requises pour accéder au module grades (manager de club)."
echo ""
echo "Pour tester:"
echo "1. Connectez-vous avec TESTBGA_USER1"
echo "2. Allez au dashboard club"
echo "3. Cliquez sur 'Grades et Examens'"
echo "4. Vous devriez être redirigé vers le vrai système de grades"
echo ""
echo "============================================"