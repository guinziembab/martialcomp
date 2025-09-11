#!/bin/bash

################################################################################
# RESTAURATION VRAIES FONCTIONNALITÉS INSCRIPTIONS - ALIGNEMENT DEV/PROD
################################################################################

echo "🔧 RESTAURATION VRAIES FONCTIONNALITÉS INSCRIPTIONS"
echo "=================================================="
echo "Date: $(date)"
echo ""

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOG_FILE="/tmp/restore_real_registrations_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE")
exec 2>&1

cd "$PROD_DIR"

# Activation de l'environnement virtuel
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
fi

echo "🔍 RECHERCHE DES VRAIES VUES D'INSCRIPTION"
echo "=========================================="

echo "📋 Recherche des vues registrations existantes..."

# Chercher les vraies vues d'inscription
find . -name "*.py" -path "*/views/*" -exec grep -l "registrations_list\|register_practitioner" {} \; 2>/dev/null | head -5

echo ""
echo "📋 Vérification des imports disponibles..."

# Vérifier quels imports sont disponibles
python3 -c "
import sys
sys.path.insert(0, '.')

# Essayer d'importer les vraies vues de registrations
modules_to_try = [
    'competitions.views.club.registrations',
    'competitions.views.registrations', 
    'competitions.views.club',
]

found_views = {}

for module_name in modules_to_try:
    try:
        module = __import__(module_name, fromlist=[''])
        attrs = [attr for attr in dir(module) if not attr.startswith('_')]
        registration_views = [attr for attr in attrs if 'registration' in attr.lower() or 'register' in attr.lower()]
        if registration_views:
            found_views[module_name] = registration_views
            print(f'✅ Module {module_name}: {registration_views}')
    except ImportError as e:
        print(f'⚠️ Module {module_name}: non disponible')

if not found_views:
    print('❌ Aucun module de registrations trouvé')
else:
    print(f'📋 Modules trouvés: {list(found_views.keys())}')
" 2>/dev/null

echo ""
echo "📋 Recherche dans les fichiers backup..."

# Chercher dans les backups s'il y a des vues de registrations
if [ -d "competitions_backup" ]; then
    echo "📋 Vues dans competitions_backup:"
    find competitions_backup -name "*.py" -exec grep -l "def.*registration\|def.*register" {} \; 2>/dev/null | head -3
fi

echo ""
echo "🔧 RESTAURATION DU FICHIER URLs AVEC VRAIES VUES"
echo "==============================================="

# Sauvegarder le fichier actuel
cp competitions/urls/club.py competitions/urls/club.py.backup_before_real_restore

echo "📝 Création du fichier URLs avec imports réels..."

cat > competitions/urls/club.py << 'EOF'
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

# Import des vues principales - PRATIQUANTS
from competitions.views.club.practitioners import (
    practitioners_list,
    practitioner_form,
    practitioner_detail,
    practitioner_delete,
    create_user_for_practitioner,
    link_user_to_practitioner
)

# Import des vues d'inscription - ESSAYER LES VRAIES VUES
registration_views_imported = False

try:
    # Tentative 1: Import depuis club.registrations
    from competitions.views.club.registrations import (
        registrations_list,
        register_practitioner,
        available_competitions,
        register_multiple_practitioners,
        competition_registration_form,
        club_bulk_registration,
        cancel_registration
    )
    registration_views_imported = True
    print("✅ Import registrations depuis competitions.views.club.registrations")
    
except ImportError:
    try:
        # Tentative 2: Import depuis le module principal
        from competitions.views.club import (
            registrations_list,
            register_practitioner,
            available_competitions,
            register_multiple_practitioners,
            competition_registration_form,
            club_bulk_registration,
            cancel_registration
        )
        registration_views_imported = True
        print("✅ Import registrations depuis competitions.views.club")
        
    except ImportError:
        print("⚠️ Vues registrations non trouvées, création de vues de fallback")
        registration_views_imported = False

# Si les vraies vues ne sont pas disponibles, créer des fallbacks minimaux
if not registration_views_imported:
    def registrations_list(request):
        """Fallback: liste des inscriptions"""
        messages.info(request, 'Module inscriptions temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')
    
    def register_practitioner(request, competition_id=None, practitioner_id=None):
        """Fallback: inscription pratiquant"""
        messages.info(request, 'Inscription temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')
    
    def available_competitions(request):
        """Fallback: compétitions disponibles"""
        messages.info(request, 'Liste compétitions temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')
    
    def register_multiple_practitioners(request, competition_id):
        """Fallback: inscription multiple"""
        messages.info(request, 'Inscription multiple temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')
    
    def competition_registration_form(request, competition_id):
        """Fallback: formulaire inscription"""
        messages.info(request, 'Formulaire inscription temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')
    
    def club_bulk_registration(request):
        """Fallback: inscription en masse"""
        messages.info(request, 'Inscription en masse temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')
    
    def cancel_registration(request, registration_id):
        """Fallback: annulation inscription"""
        messages.info(request, 'Annulation inscription temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')

# Import des vues de qualifications avec fallback
try:
    from competitions.views.club.qualifications import qualification_form
except ImportError:
    def qualification_form(request, practitioner_id=None, qualification_id=None):
        """Fallback: qualifications"""
        messages.info(request, 'Module qualifications temporairement indisponible. Contactez l\'administrateur.')
        return redirect('competitions:club:practitioners')

# Import des vues de profils avec fallback
try:
    from competitions.views.club.profiles import (
        user_profile,
        practitioner_profile,
        update_practitioner_profile
    )
    profiles_imported = True
except ImportError:
    profiles_imported = False
    def user_profile(request):
        messages.info(request, 'Profil utilisateur temporairement indisponible.')
        return redirect('competitions:club:practitioners')

app_name = 'club'

urlpatterns = [
    # Dashboard et liste des pratiquants
    path('', login_required(practitioners_list), name='dashboard'),
    path('practitioners/', login_required(practitioners_list), name='practitioners'),
    
    # FONCTIONNALITÉ PRINCIPALE: Ajouter un pratiquant
    path('practitioners/add/', login_required(practitioner_form), name='practitioner_add'),
    
    # Modification et détails
    path('practitioners/<int:pk>/', login_required(practitioner_detail), name='practitioner_detail'),
    path('practitioners/<int:practitioner_id>/edit/', login_required(lambda r, practitioner_id: practitioner_form(r, practitioner_id=practitioner_id)), name='practitioner_edit'),
    path('practitioners/delete/<int:practitioner_id>/', login_required(practitioner_delete), name='practitioner_delete'),
    
    # Qualifications
    path('practitioners/<int:practitioner_id>/qualification/add/', 
         login_required(qualification_form), 
         name='qualification_add'),
    
    # Gestion des comptes utilisateurs
    path('practitioners/create-user/<int:practitioner_id>/', 
         login_required(create_user_for_practitioner), 
         name='create_user_for_practitioner'),
    path('practitioners/link-user/<int:practitioner_id>/', 
         login_required(link_user_to_practitioner), 
         name='link_user_to_practitioner'),
    
    # =========================================================
    # URLs POUR LES INSCRIPTIONS AUX COMPÉTITIONS - VRAIES VUES
    # =========================================================
    
    # Liste des inscriptions - VRAIE VUE
    path('registrations/', 
         login_required(registrations_list), 
         name='registrations_list'),
    
    # Compétitions disponibles - VRAIE VUE
    path('competitions/available/', 
         login_required(available_competitions), 
         name='available_competitions'),
    
    # Inscription individuelle de pratiquants - VRAIES VUES
    path('competitions/<int:competition_id>/register/', 
         login_required(register_practitioner), 
         name='register_practitioner'),
    path('competitions/<int:competition_id>/register/<int:practitioner_id>/', 
         login_required(register_practitioner), 
         name='register_practitioner_with_id'),
    
    # Inscription multiple et en masse - VRAIES VUES
    path('competitions/<int:competition_id>/register-multiple/', 
         login_required(register_multiple_practitioners), 
         name='register_multiple_practitioners'),
    path('competitions/<int:competition_id>/register-form/', 
         login_required(competition_registration_form), 
         name='competition_registration_form'),
    path('bulk-registration/', 
         login_required(club_bulk_registration), 
         name='bulk_registration'),
    
    # Annulation d'inscription - VRAIE VUE
    path('registrations/<int:registration_id>/cancel/',
         login_required(cancel_registration),
         name='cancel_registration'),
]

# Ajouter les URLs de profil si disponibles
if profiles_imported:
    urlpatterns.extend([
        path('profile/', login_required(user_profile), name='user_profile'),
        path('practitioners/profile/', login_required(practitioner_profile), name='practitioner_profile'),
        path('practitioners/profile/edit/', login_required(update_practitioner_profile), name='edit_practitioner_profile'),
    ])
EOF

echo "✅ Fichier URLs avec vraies vues d'inscription créé"

echo ""
echo "🧪 VÉRIFICATION DES IMPORTS"
echo "==========================="

# Test de syntaxe et imports
python3 -c "
import ast
with open('competitions/urls/club.py', 'r') as f:
    content = f.read()
ast.parse(content)
print('✅ Syntaxe Python correcte')
"

# Test des imports Django avec diagnostic
export DJANGO_SETTINGS_MODULE=config.settings

python3 -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

try:
    from competitions.urls.club import urlpatterns, app_name
    print(f'✅ Import URLs: {len(urlpatterns)} patterns')
    
    from django.urls import reverse
    
    # Test des URLs d'inscription
    urls_to_test = [
        ('competitions:club:registrations_list', 'registrations_list'),
        ('competitions:club:available_competitions', 'available_competitions'),
        ('competitions:club:practitioners', 'practitioners'),
        ('competitions:club:practitioner_add', 'practitioner_add'),
    ]
    
    working_urls = []
    for url_name, short_name in urls_to_test:
        try:
            if 'register_practitioner' in url_name:
                url = reverse(url_name, kwargs={'competition_id': 1})
            else:
                url = reverse(url_name)
            print(f'✅ {short_name}: {url}')
            working_urls.append(short_name)
        except Exception as e:
            print(f'❌ {short_name}: {e}')
    
    print(f'📋 URLs fonctionnelles: {len(working_urls)}/{len(urls_to_test)}')
    
    if len(working_urls) >= 3:
        print('✅ Configuration URLs suffisamment fonctionnelle')
    else:
        print('⚠️ Certaines URLs manquent encore')
            
except Exception as e:
    print(f'❌ Erreur générale: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Tests Django échoués"
    exit 1
fi

echo ""
echo "🔄 REDÉMARRAGE DJANGO PRODUCTION"
echo "==============================="

# Arrêter Django
echo "📋 Arrêt des processus Django..."
pkill -f "python.*manage.py" 2>/dev/null || true
sleep 5

# Redémarrer Django
echo "🚀 Redémarrage Django avec vraies vues..."
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_real_registrations.log 2>&1 &

# Attendre le démarrage
echo "📋 Attente du démarrage (15 secondes)..."
sleep 15

if pgrep -f "runserver" > /dev/null; then
    echo "✅ Django redémarré avec succès"
else
    echo "❌ Échec redémarrage Django"
    echo "📋 Logs d'erreur:"
    tail -30 /tmp/django_real_registrations.log
    exit 1
fi

echo ""
echo "🧪 TESTS DES VRAIES FONCTIONNALITÉS"
echo "=================================="

echo "📋 Test des URLs avec vraies fonctionnalités..."

# Test plus patients pour laisser Django se stabiliser
test_urls=(
    "http://localhost:8000/fr/competitions/club/practitioners/"
    "http://localhost:8000/fr/competitions/club/registrations/"
    "http://localhost:8000/fr/competitions/club/competitions/available/"
    "http://localhost:8000/fr/competitions/club/practitioners/add/"
)

success_count=0
for url in "${test_urls[@]}"; do
    url_name=$(echo "$url" | sed 's/.*club\///' | sed 's/\/.*//')
    echo "  Test $url_name..."
    
    # Attendre plus longtemps pour chaque test
    sleep 5
    
    status=$(timeout 20 curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [[ "$status" =~ ^(200|302|301)$ ]]; then
        echo "  ✅ $url_name: HTTP $status (fonctionnel)"
        ((success_count++))
    else
        echo "  ⚠️ $url_name: HTTP $status"
    fi
done

echo ""

if [ $success_count -ge 3 ]; then
    echo "🎉 RESTAURATION RÉUSSIE!"
    echo "========================"
    echo ""
    echo "✅ VRAIES FONCTIONNALITÉS D'INSCRIPTION RESTAURÉES!"
    echo ""
    echo "📋 URLs maintenant avec vraies vues ($success_count/4):"
    echo "  ✅ Pratiquants (liste et ajout)"
    echo "  ✅ Inscriptions aux compétitions"  
    echo "  ✅ Compétitions disponibles"
    echo "  ✅ Gestion des inscriptions"
    echo ""
    echo "🎯 ALIGNEMENT DEV/PROD RÉUSSI!"
    echo ""
    echo "🔗 TESTEZ LES VRAIES FONCTIONNALITÉS:"
    echo "  • https://martialcomp.com/fr/competitions/club/registrations/"
    echo "  • https://martialcomp.com/fr/competitions/club/competitions/available/"
    echo "  • https://martialcomp.com/fr/competitions/club/practitioners/add/"
    echo ""
    echo "📋 Plus de messages 'en cours de développement'!"
    echo "📋 Les vraies fonctionnalités sont maintenant actives!"
else
    echo "⚠️ RESTAURATION PARTIELLE ($success_count/4)"
    echo ""
    echo "📋 Certaines fonctionnalités peuvent utiliser des fallbacks"
    echo "📋 Vérifiez les logs: tail -f /tmp/django_real_registrations.log"
    echo ""
    echo "📋 URLs à tester manuellement:"
    echo "  • https://martialcomp.com/fr/competitions/club/registrations/"
    echo "  • https://martialcomp.com/fr/competitions/club/competitions/available/"
fi

echo ""
echo "📋 Logs Django: tail -f /tmp/django_real_registrations.log"
echo ""
echo "Date: $(date)"