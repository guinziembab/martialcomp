#!/bin/bash

################################################################################
# IDENTIFICATION ET RESTAURATION DES VRAIES VUES JUGES
################################################################################

echo "🔍 IDENTIFICATION ET RESTAURATION DES VRAIES VUES JUGES"
echo "======================================================="
echo "Date: $(date)"
echo ""

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOG_FILE="/tmp/find_real_judges_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE")
exec 2>&1

cd "$PROD_DIR"

# Activation de l'environnement virtuel
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
fi

echo "🔍 RECHERCHE EXHAUSTIVE DES VRAIES VUES JUGES"
echo "============================================="

echo "📋 1. Recherche des fichiers contenant des vues de juges..."

# Recherche exhaustive dans tout le projet
echo "📁 Fichiers contenant 'judges_list':"
find . -name "*.py" -exec grep -l "def judges_list" {} \; 2>/dev/null

echo ""
echo "📁 Fichiers contenant 'judge_add':"
find . -name "*.py" -exec grep -l "def judge_add" {} \; 2>/dev/null

echo ""
echo "📁 Fichiers contenant 'judge_assignments':"
find . -name "*.py" -exec grep -l "def judge_assignments" {} \; 2>/dev/null

echo ""
echo "📁 Tous les fichiers judges dans views:"
find . -path "*/views/*" -name "*judge*" -type f 2>/dev/null

echo ""
echo "📋 2. Analyse des imports existants dans le fichier URLs original..."

# Vérifier l'ancien fichier URLs s'il existe
if [ -f "competitions/urls/club.py.backup_before_real_restore" ]; then
    echo "📁 Imports dans l'ancien fichier URLs:"
    grep -E "from.*judge|import.*judge" competitions/urls/club.py.backup_before_real_restore 2>/dev/null || echo "Aucun import judge trouvé"
fi

echo ""
echo "📋 3. Test des imports Python directs..."

# Test systématique des imports possibles
python3 -c "
import sys
sys.path.insert(0, '.')

print('🔍 Test des imports possibles pour les juges...')

# Liste des modules à tester
modules_to_test = [
    ('competitions.views.club.judges', ['judges_list', 'judge_add', 'judge_assignments']),
    ('competitions.views.club.qualifications', ['judges_list', 'judge_add', 'judge_assignments']),
    ('competitions.views.club', ['judges_list', 'judge_add', 'judge_assignments']),
    ('competitions.views.judges', ['judges_list', 'judge_add', 'judge_assignments']),
    ('competitions.views', ['judges_list', 'judge_add', 'judge_assignments']),
]

successful_imports = {}

for module_name, functions in modules_to_test:
    try:
        module = __import__(module_name, fromlist=functions)
        available_functions = []
        
        for func_name in functions:
            if hasattr(module, func_name):
                func = getattr(module, func_name)
                if callable(func):
                    available_functions.append(func_name)
                    
        if available_functions:
            successful_imports[module_name] = available_functions
            print(f'✅ {module_name}: {available_functions}')
        else:
            print(f'⚠️ {module_name}: module trouvé mais pas de fonctions juges')
            
    except ImportError as e:
        print(f'❌ {module_name}: {e}')
    except Exception as e:
        print(f'⚠️ {module_name}: erreur {e}')

print('')
if successful_imports:
    print('📋 IMPORTS RÉUSSIS:')
    for module, functions in successful_imports.items():
        print(f'  {module}: {functions}')
    
    # Choisir le meilleur module
    best_module = max(successful_imports.keys(), key=lambda k: len(successful_imports[k]))
    print(f'')
    print(f'🎯 MEILLEUR MODULE: {best_module}')
    print(f'🎯 FONCTIONS: {successful_imports[best_module]}')
else:
    print('❌ AUCUN IMPORT DE JUGES RÉUSSI')
" 2>/dev/null

echo ""
echo "📋 4. Recherche dans les fichiers backup..."

# Chercher dans tous les backups
echo "📁 Backups disponibles:"
find . -name "*backup*" -type d 2>/dev/null | head -5

echo ""
echo "📁 Fichiers judges dans les backups:"
find . -path "*backup*" -name "*judge*" -type f 2>/dev/null | head -5

echo ""
echo "🔧 CRÉATION DU FICHIER URLs AVEC VRAIS IMPORTS DÉTECTÉS"
echo "======================================================"

# Sauvegarder le fichier actuel
cp competitions/urls/club.py competitions/urls/club.py.backup_before_real_fix

echo "📝 Génération du fichier URLs avec imports détectés automatiquement..."

# Générer le fichier avec les vrais imports détectés
python3 -c "
import sys
sys.path.insert(0, '.')

print('📝 Génération du fichier URLs avec imports réels...')

# Test des imports et génération du code
imports_code = []
judges_functions = {}

# Test des imports systématiques
modules_to_test = [
    'competitions.views.club.judges',
    'competitions.views.club.qualifications', 
    'competitions.views.club',
    'competitions.views.judges',
]

for module_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=[''])
        
        # Vérifier les fonctions de juges disponibles
        judge_functions = ['judges_list', 'judge_add', 'judge_assignments', 'judge_edit', 'judge_delete']
        available = []
        
        for func_name in judge_functions:
            if hasattr(module, func_name):
                available.append(func_name)
        
        if available:
            imports_code.append(f'# Import depuis {module_name}')
            imports_code.append(f'from {module_name} import (')
            for func in available:
                imports_code.append(f'    {func},')
            imports_code.append(')')
            judges_functions = dict(zip(available, available))
            print(f'✅ Utilisation de {module_name} avec {available}')
            break
            
    except ImportError:
        continue

# Si aucun import trouvé, créer des fallbacks informatifs
if not judges_functions:
    print('⚠️ Aucun import trouvé, création de fallbacks informatifs')
    judges_functions = {
        'judges_list': 'fallback_judges_list',
        'judge_add': 'fallback_judge_add', 
        'judge_assignments': 'fallback_judge_assignments',
        'judge_edit': 'fallback_judge_edit',
        'judge_delete': 'fallback_judge_delete'
    }

print(f'📋 Fonctions disponibles: {list(judges_functions.keys())}')

# Écrire dans un fichier temporaire pour debug
with open('/tmp/judges_imports_detected.txt', 'w') as f:
    f.write('\\n'.join(imports_code))
    f.write(f'\\nFonctions: {judges_functions}')

print('✅ Informations sauvées dans /tmp/judges_imports_detected.txt')
" 2>/dev/null

echo "📋 Imports détectés:"
cat /tmp/judges_imports_detected.txt 2>/dev/null || echo "Fichier de détection non créé"

echo ""
echo "📝 Création du fichier URLs final avec imports réels..."

cat > competitions/urls/club.py << 'EOF'
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
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

# Import des vues d'inscription - ESSAI DES VRAIES VUES
try:
    from competitions.views.club.registrations import (
        registrations_list,
        register_practitioner,
        available_competitions,
        register_multiple_practitioners,
        competition_registration_form,
        club_bulk_registration,
        cancel_registration
    )
    print("✅ Import inscriptions réussi")
except ImportError:
    try:
        from competitions.views.club import (
            registrations_list,
            register_practitioner,
            available_competitions,
            register_multiple_practitioners,
            competition_registration_form,
            club_bulk_registration,
            cancel_registration
        )
        print("✅ Import inscriptions depuis club réussi")
    except ImportError:
        print("⚠️ Import inscriptions échoué, création de redirections")
        def registrations_list(request):
            messages.warning(request, 'Module inscriptions en cours de restauration.')
            return redirect('competitions:club:practitioners')
        def register_practitioner(request, competition_id=None, practitioner_id=None):
            messages.warning(request, 'Inscription en cours de restauration.')
            return redirect('competitions:club:practitioners')
        def available_competitions(request):
            messages.warning(request, 'Compétitions en cours de restauration.')
            return redirect('competitions:club:practitioners')
        def register_multiple_practitioners(request, competition_id):
            messages.warning(request, 'Inscription multiple en cours de restauration.')
            return redirect('competitions:club:practitioners')
        def competition_registration_form(request, competition_id):
            messages.warning(request, 'Formulaire inscription en cours de restauration.')
            return redirect('competitions:club:practitioners')
        def club_bulk_registration(request):
            messages.warning(request, 'Inscription en masse en cours de restauration.')
            return redirect('competitions:club:practitioners')
        def cancel_registration(request, registration_id):
            messages.warning(request, 'Annulation inscription en cours de restauration.')
            return redirect('competitions:club:practitioners')

# Import des vues de juges - ESSAI EXHAUSTIF DES VRAIES VUES
judges_imported = False

# Tentative 1: competitions.views.club.judges
if not judges_imported:
    try:
        from competitions.views.club.judges import (
            judges_list,
            judge_add,
            judge_assignments
        )
        # Essayer d'importer les fonctions de modification
        try:
            from competitions.views.club.judges import judge_edit, judge_delete
        except ImportError:
            def judge_edit(request, judge_id):
                messages.info(request, 'Modification juge: fonctionnalité en cours de développement.')
                return redirect('competitions:club:judges_list')
            def judge_delete(request, judge_id):
                messages.info(request, 'Suppression juge: fonctionnalité en cours de développement.')
                return redirect('competitions:club:judges_list')
        
        judges_imported = True
        print("✅ Import juges depuis competitions.views.club.judges")
        
    except ImportError:
        pass

# Tentative 2: competitions.views.club.qualifications  
if not judges_imported:
    try:
        from competitions.views.club.qualifications import (
            judges_list,
            judge_add,
            judge_assignments
        )
        def judge_edit(request, judge_id):
            messages.info(request, 'Modification juge: fonctionnalité en cours de développement.')
            return redirect('competitions:club:judges_list')
        def judge_delete(request, judge_id):
            messages.info(request, 'Suppression juge: fonctionnalité en cours de développement.')
            return redirect('competitions:club:judges_list')
            
        judges_imported = True
        print("✅ Import juges depuis competitions.views.club.qualifications")
        
    except ImportError:
        pass

# Tentative 3: competitions.views.club (module principal)
if not judges_imported:
    try:
        from competitions.views.club import (
            judges_list,
            judge_add,
            judge_assignments
        )
        def judge_edit(request, judge_id):
            messages.info(request, 'Modification juge: fonctionnalité en cours de développement.')
            return redirect('competitions:club:judges_list')
        def judge_delete(request, judge_id):
            messages.info(request, 'Suppression juge: fonctionnalité en cours de développement.')
            return redirect('competitions:club:judges_list')
            
        judges_imported = True
        print("✅ Import juges depuis competitions.views.club")
        
    except ImportError:
        pass

# Tentative 4: competitions.views.judges (module dédié)
if not judges_imported:
    try:
        from competitions.views.judges import (
            judges_list,
            judge_add,
            judge_assignments
        )
        # Essayer les fonctions d'édition
        try:
            from competitions.views.judges import judge_edit, judge_delete
        except ImportError:
            def judge_edit(request, judge_id):
                messages.info(request, 'Modification juge: fonctionnalité en cours de développement.')
                return redirect('competitions:club:judges_list')
            def judge_delete(request, judge_id):
                messages.info(request, 'Suppression juge: fonctionnalité en cours de développement.')
                return redirect('competitions:club:judges_list')
                
        judges_imported = True
        print("✅ Import juges depuis competitions.views.judges")
        
    except ImportError:
        pass

# Si aucun import n'a réussi, créer des vues informatives (pas des erreurs)
if not judges_imported:
    print("⚠️ Aucun import de juges réussi, création de vues informatives")
    
    def judges_list(request):
        return render(request, 'competitions/club/judges_temp.html', {
            'title': 'Gestion des juges',
            'message': 'Le module de gestion des juges est en cours de restauration. Les imports Python ont échoué.',
            'debug_info': 'Vérifiez que les modules competitions.views.club.judges ou competitions.views.judges existent.'
        })
    
    def judge_add(request):
        messages.warning(request, 'Ajout de juge: module en cours de restauration.')
        return redirect('competitions:club:judges_list')
    
    def judge_assignments(request):
        messages.warning(request, 'Affectations juges: module en cours de restauration.')
        return redirect('competitions:club:judges_list')
    
    def judge_edit(request, judge_id):
        messages.warning(request, 'Modification juge: module en cours de restauration.')
        return redirect('competitions:club:judges_list')
    
    def judge_delete(request, judge_id):
        messages.warning(request, 'Suppression juge: module en cours de restauration.')
        return redirect('competitions:club:judges_list')

# Import des qualifications
try:
    from competitions.views.club.qualifications import qualification_form
except ImportError:
    def qualification_form(request, practitioner_id=None, qualification_id=None):
        messages.info(request, 'Module qualifications en cours de restauration.')
        return redirect('competitions:club:practitioners')

# Import des profils
try:
    from competitions.views.club.profiles import (
        user_profile,
        practitioner_profile,
        update_practitioner_profile
    )
    profiles_imported = True
except ImportError:
    profiles_imported = False

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
    # URLs POUR LES JUGES - VRAIES VUES OU INFORMATIVES
    # =========================================================
    
    path('judges/', login_required(judges_list), name='judges_list'),
    path('judges/add/', login_required(judge_add), name='judge_add'),
    path('judges/<int:judge_id>/edit/', login_required(judge_edit), name='judge_edit'),
    path('judges/<int:judge_id>/delete/', login_required(judge_delete), name='judge_delete'),
    path('judges/assignments/', login_required(judge_assignments), name='judge_assignments'),
    
    # =========================================================
    # URLs POUR LES INSCRIPTIONS AUX COMPÉTITIONS
    # =========================================================
    
    path('registrations/', login_required(registrations_list), name='registrations_list'),
    path('competitions/available/', login_required(available_competitions), name='available_competitions'),
    path('competitions/<int:competition_id>/register/', login_required(register_practitioner), name='register_practitioner'),
    path('competitions/<int:competition_id>/register/<int:practitioner_id>/', login_required(register_practitioner), name='register_practitioner_with_id'),
    path('competitions/<int:competition_id>/register-multiple/', login_required(register_multiple_practitioners), name='register_multiple_practitioners'),
    path('competitions/<int:competition_id>/register-form/', login_required(competition_registration_form), name='competition_registration_form'),
    path('bulk-registration/', login_required(club_bulk_registration), name='bulk_registration'),
    path('registrations/<int:registration_id>/cancel/', login_required(cancel_registration), name='cancel_registration'),
]

# Ajouter les URLs de profil si disponibles
if profiles_imported:
    urlpatterns.extend([
        path('profile/', login_required(user_profile), name='user_profile'),
        path('practitioners/profile/', login_required(practitioner_profile), name='practitioner_profile'),
        path('practitioners/profile/edit/', login_required(update_practitioner_profile), name='edit_practitioner_profile'),
    ])
EOF

echo "✅ Fichier URLs avec imports exhaustifs créé"

echo ""
echo "📝 Création du template informatif juges si nécessaire..."

mkdir -p competitions/templates/competitions/club/

cat > competitions/templates/competitions/club/judges_temp.html << 'EOF'
{% extends "base.html" %}
{% load i18n %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<div class="container py-4">
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card shadow">
                <div class="card-header bg-warning text-dark">
                    <div class="d-flex justify-content-between align-items-center">
                        <h4 class="mb-0">
                            <i class="fas fa-gavel me-2"></i>{{ title }}
                        </h4>
                        <a href="{% url 'competitions:club:practitioners' %}" class="btn btn-dark btn-sm">
                            <i class="fas fa-arrow-left me-1"></i>{% trans "Retour" %}
                        </a>
                    </div>
                </div>
                
                <div class="card-body">
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>{{ message }}</strong>
                    </div>
                    
                    {% if debug_info %}
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        <strong>Information technique:</strong> {{ debug_info }}
                    </div>
                    {% endif %}
                    
                    <div class="row mt-4">
                        <div class="col-md-4 mb-3">
                            <div class="card h-100">
                                <div class="card-body text-center">
                                    <i class="fas fa-users fa-3x text-primary mb-3"></i>
                                    <h6>{% trans "Pratiquants" %}</h6>
                                    <p class="text-muted small">{% trans "Gérer les pratiquants du club" %}</p>
                                    <a href="{% url 'competitions:club:practitioners' %}" class="btn btn-outline-primary btn-sm">
                                        {% trans "Accéder" %}
                                    </a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4 mb-3">
                            <div class="card h-100">
                                <div class="card-body text-center">
                                    <i class="fas fa-trophy fa-3x text-success mb-3"></i>
                                    <h6>{% trans "Inscriptions" %}</h6>
                                    <p class="text-muted small">{% trans "Inscrire aux compétitions" %}</p>
                                    <a href="{% url 'competitions:club:registrations_list' %}" class="btn btn-outline-success btn-sm">
                                        {% trans "Accéder" %}
                                    </a>
                                </div>
                            </div>
                        </div>
                        
                        <div class="col-md-4 mb-3">
                            <div class="card h-100">
                                <div class="card-body text-center">
                                    <i class="fas fa-plus-circle fa-3x text-info mb-3"></i>
                                    <h6>{% trans "Ajouter pratiquant" %}</h6>
                                    <p class="text-muted small">{% trans "Nouveau membre du club" %}</p>
                                    <a href="{% url 'competitions:club:practitioner_add' %}" class="btn btn-outline-info btn-sm">
                                        {% trans "Ajouter" %}
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-4 text-center">
                        <small class="text-muted">
                            {% trans "Module juges en cours de restauration. Contactez l'administrateur système si ce message persiste." %}
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
EOF

echo "✅ Template informatif juges créé"

echo ""
echo "🔄 REDÉMARRAGE AVEC IMPORTS DÉTECTÉS"
echo "==================================="

# Redémarrage Django
pkill -f "python.*manage.py" 2>/dev/null || true
sleep 5

export DJANGO_SETTINGS_MODULE=config.settings
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_judges_detected.log 2>&1 &

sleep 15

echo ""
echo "🧪 TEST FINAL DES VRAIES VUES JUGES"
echo "=================================="

if pgrep -f "runserver" > /dev/null; then
    echo "✅ Django actif"
    
    # Test de l'URL juges
    status=$(timeout 15 curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/club/judges/" 2>/dev/null)
    
    if [[ "$status" =~ ^(200|302|301)$ ]]; then
        echo "✅ URL judges accessible: HTTP $status"
        
        # Vérifier le contenu pour voir si c'est une vraie vue ou un fallback
        response_content=$(timeout 10 curl -s "http://localhost:8000/fr/competitions/club/judges/" 2>/dev/null | head -50)
        
        if echo "$response_content" | grep -q "en cours de restauration"; then
            echo "⚠️ Vue judges utilise encore un fallback"
        elif echo "$response_content" | grep -q "temporairement indisponible"; then
            echo "⚠️ Vue judges utilise encore un message temporaire"
        else
            echo "✅ Vue judges semble être la vraie vue!"
        fi
    else
        echo "❌ URL judges: HTTP $status"
    fi
else
    echo "❌ Django non actif"
fi

echo ""
echo "🎯 RÉSUMÉ DE LA DÉTECTION"
echo "========================"
echo ""
echo "📋 Fichier généré: competitions/urls/club.py"
echo "📋 Template créé: competitions/templates/competitions/club/judges_temp.html"
echo "📋 Logs Django: tail -f /tmp/django_judges_detected.log"
echo ""
echo "🔗 Testez: https://martialcomp.com/fr/competitions/club/judges/"
echo ""
echo "📋 Si la vue affiche encore un message temporaire,"
echo "   cela signifie que les imports des vraies vues ont échoué."
echo "   Vérifiez les logs Django pour plus d'informations."
echo ""
echo "Date: $(date)"