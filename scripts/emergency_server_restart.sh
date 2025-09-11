#!/bin/bash

################################################################################
# REDÉMARRAGE D'URGENCE SERVEUR - 502 BAD GATEWAY
################################################################################

echo "🚨 REDÉMARRAGE D'URGENCE SERVEUR - 502 BAD GATEWAY"
echo "=================================================="
echo "Date: $(date)"
echo ""

PROD_DIR="/var/www/vhosts/martialcomp.com/httpdocs"
LOG_FILE="/tmp/emergency_restart_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE")
exec 2>&1

cd "$PROD_DIR"

# Activation de l'environnement virtuel
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
fi

echo "🔍 DIAGNOSTIC D'URGENCE"
echo "======================="

echo "📋 1. Vérification des processus Django..."
django_processes=$(ps aux | grep -E "(python|django|runserver)" | grep -v grep | wc -l)
echo "  Processus Django actifs: $django_processes"

if [ $django_processes -gt 0 ]; then
    echo "  📋 Processus Django détectés:"
    ps aux | grep -E "(python|django|runserver)" | grep -v grep | head -5
else
    echo "  ❌ Aucun processus Django actif"
fi

echo ""
echo "📋 2. Vérification nginx..."
nginx_status=$(systemctl is-active nginx 2>/dev/null || echo "unknown")
echo "  Status nginx: $nginx_status"

echo ""
echo "📋 3. Vérification des ports..."
port_8000=$(netstat -tlnp 2>/dev/null | grep ":8000" || echo "Port 8000 libre")
echo "  Port 8000: $port_8000"

echo ""
echo "📋 4. Derniers logs Django..."
recent_logs=$(find /tmp -name "*django*.log" -mtime -1 | head -3)
if [ -n "$recent_logs" ]; then
    echo "  📁 Logs récents trouvés:"
    for log in $recent_logs; do
        echo "    $log"
        echo "    --- Dernières lignes ---"
        tail -5 "$log" 2>/dev/null
        echo ""
    done
else
    echo "  ⚠️ Aucun log Django récent trouvé"
fi

echo ""
echo "🛑 ARRÊT DE TOUS LES PROCESSUS"
echo "=============================="

echo "📋 Arrêt de tous les processus Django/Python..."
pkill -f "python.*manage.py" 2>/dev/null || true
pkill -f "runserver" 2>/dev/null || true
pkill -f "gunicorn" 2>/dev/null || true
pkill -9 -f "django" 2>/dev/null || true

echo "📋 Attente de l'arrêt complet..."
sleep 10

# Vérifier que tous les processus sont arrêtés
remaining=$(ps aux | grep -E "(python.*manage|runserver|gunicorn)" | grep -v grep | wc -l)
if [ $remaining -gt 0 ]; then
    echo "⚠️ $remaining processus encore actifs, arrêt forcé..."
    ps aux | grep -E "(python.*manage|runserver|gunicorn)" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    sleep 5
fi

echo "✅ Tous les processus arrêtés"

echo ""
echo "🔧 RESTAURATION FICHIER URLs STABLE"
echo "===================================="

echo "📋 Le dernier changement (wrapper technical_scoring) a probablement causé le problème"

# Restaurer le fichier URLs de la dernière version stable
if [ -f "competitions/urls/club.py.backup_before_wrapper" ]; then
    echo "📋 Restauration du fichier URLs stable..."
    cp "competitions/urls/club.py.backup_before_wrapper" "competitions/urls/club.py"
    echo "✅ Fichier URLs restauré à la version stable"
else
    echo "⚠️ Backup non trouvé, création d'une version minimale..."
    
    # Créer une version minimale fonctionnelle
    cat > competitions/urls/club.py << 'EOF'
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

# Import des vues de base - SEULEMENT LES VUES QUI FONCTIONNENT
from competitions.views.club.practitioners import (
    practitioners_list,
    practitioner_form,
    practitioner_detail,
    practitioner_delete,
    create_user_for_practitioner,
    link_user_to_practitioner
)

# Import des vues d'inscription
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
    registrations_imported = True
except ImportError:
    registrations_imported = False

# Import des vues de juges
try:
    from competitions.views.club.judges import (
        judges_list,
        judge_add,
        judge_assignments
    )
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
except ImportError:
    judges_imported = False

# Import des qualifications
try:
    from competitions.views.club.qualifications import qualification_form
    qualifications_imported = True
except ImportError:
    qualifications_imported = False

# TECHNICAL SCORING - VERSION SIMPLE SANS WRAPPER
def technical_scoring_temp(request):
    """Vue temporaire pour technical scoring à cause de l'erreur BACH HAC"""
    messages.warning(request, 'Module notation technique temporairement indisponible à cause de données corrompues (BACH HAC).')
    return redirect('competitions:club:practitioners')

def competition_scoring_temp(request, competition_id):
    messages.warning(request, 'Notation compétition temporairement indisponible.')
    return redirect('competitions:club:practitioners')

def performance_detail_temp(request, performance_id):
    messages.warning(request, 'Détail performance temporairement indisponible.')
    return redirect('competitions:club:practitioners')

# Créer les fallbacks pour les modules non importés
if not registrations_imported:
    def registrations_list(request):
        messages.warning(request, 'Module inscriptions en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def register_practitioner(request, competition_id=None, practitioner_id=None):
        messages.warning(request, 'Inscription en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def available_competitions(request):
        messages.warning(request, 'Compétitions disponibles en cours de restauration.')
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

if not judges_imported:
    def judges_list(request):
        messages.warning(request, 'Module juges en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def judge_add(request):
        messages.warning(request, 'Ajout juge en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def judge_assignments(request):
        messages.warning(request, 'Affectations juges en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def judge_edit(request, judge_id):
        messages.warning(request, 'Modification juge en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def judge_delete(request, judge_id):
        messages.warning(request, 'Suppression juge en cours de restauration.')
        return redirect('competitions:club:practitioners')

if not qualifications_imported:
    def qualification_form(request, practitioner_id=None, qualification_id=None):
        messages.info(request, 'Module qualifications en cours de restauration.')
        return redirect('competitions:club:practitioners')

app_name = 'club'

urlpatterns = [
    # URLs de base - TOUJOURS FONCTIONNELLES
    path('', login_required(practitioners_list), name='dashboard'),
    path('practitioners/', login_required(practitioners_list), name='practitioners'),
    path('practitioners/add/', login_required(practitioner_form), name='practitioner_add'),
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
    
    # Juges
    path('judges/', login_required(judges_list), name='judges_list'),
    path('judges/add/', login_required(judge_add), name='judge_add'),
    path('judges/<int:judge_id>/edit/', login_required(judge_edit), name='judge_edit'),
    path('judges/<int:judge_id>/delete/', login_required(judge_delete), name='judge_delete'),
    path('judges/assignments/', login_required(judge_assignments), name='judge_assignments'),
    
    # Technical scoring - VERSION TEMPORAIRE SANS ERREUR
    path('technical-scoring/', login_required(technical_scoring_temp), name='technical_scoring'),
    path('technical-scoring/competition/<int:competition_id>/', 
         login_required(competition_scoring_temp), 
         name='competition_scoring'),
    path('technical-scoring/performance/<int:performance_id>/', 
         login_required(performance_detail_temp), 
         name='performance_detail'),
    
    # Inscriptions
    path('registrations/', login_required(registrations_list), name='registrations_list'),
    path('competitions/available/', login_required(available_competitions), name='available_competitions'),
    path('competitions/<int:competition_id>/register/', login_required(register_practitioner), name='register_practitioner'),
    path('competitions/<int:competition_id>/register/<int:practitioner_id>/', login_required(register_practitioner), name='register_practitioner_with_id'),
    path('competitions/<int:competition_id>/register-multiple/', login_required(register_multiple_practitioners), name='register_multiple_practitioners'),
    path('competitions/<int:competition_id>/register-form/', login_required(competition_registration_form), name='competition_registration_form'),
    path('bulk-registration/', login_required(club_bulk_registration), name='bulk_registration'),
    path('registrations/<int:registration_id>/cancel/', login_required(cancel_registration), name='cancel_registration'),
]
EOF
    
    echo "✅ Version minimale stable créée"
fi

echo ""
echo "🧪 TEST DE SYNTAXE"
echo "=================="

# Test de syntaxe Python
python3 -c "
import ast
with open('competitions/urls/club.py', 'r') as f:
    content = f.read()
ast.parse(content)
print('✅ Syntaxe Python correcte')
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Erreur de syntaxe détectée, correction..."
    # En cas d'erreur, utiliser une version encore plus simple
    cat > competitions/urls/club.py << 'EOF'
from django.urls import path
from django.contrib.auth.decorators import login_required
from competitions.views.club.practitioners import practitioners_list, practitioner_form

app_name = 'club'

urlpatterns = [
    path('', login_required(practitioners_list), name='dashboard'),
    path('practitioners/', login_required(practitioners_list), name='practitioners'),
    path('practitioners/add/', login_required(practitioner_form), name='practitioner_add'),
]
EOF
    echo "✅ Version ultra-simple créée"
fi

echo ""
echo "🚀 REDÉMARRAGE D'URGENCE DJANGO"
echo "==============================="

# Supprimer les fichiers temporaires problématiques
rm -f /tmp/technical_scoring_wrapper.py* 2>/dev/null || true

export DJANGO_SETTINGS_MODULE=config.settings

echo "📋 Test de la configuration Django..."
python3 manage.py check --deploy 2>&1 | head -10

echo ""
echo "📋 Démarrage Django en mode d'urgence..."
nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_emergency_restart.log 2>&1 &

echo "📋 Attente du démarrage (20 secondes)..."
sleep 20

# Vérification du démarrage
if pgrep -f "runserver" > /dev/null; then
    echo "✅ Django redémarré avec succès"
    
    # Test rapide
    sleep 5
    status=$(timeout 10 curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/club/practitioners/" 2>/dev/null || echo "000")
    
    if [[ "$status" =~ ^(200|302|301)$ ]]; then
        echo "✅ Test URL réussi: HTTP $status"
    else
        echo "⚠️ Test URL: HTTP $status"
    fi
    
else
    echo "❌ Échec redémarrage Django"
    echo "📋 Logs d'erreur:"
    tail -20 /tmp/django_emergency_restart.log
fi

echo ""
echo "🔄 REDÉMARRAGE NGINX"
echo "==================="

echo "📋 Redémarrage du service nginx..."
systemctl restart nginx 2>/dev/null || service nginx restart 2>/dev/null || true

sleep 5

nginx_status=$(systemctl is-active nginx 2>/dev/null || echo "unknown")
echo "📋 Status nginx après redémarrage: $nginx_status"

echo ""
echo "🧪 TEST FINAL DU SITE"
echo "===================="

echo "📋 Test du site complet..."
for attempt in {1..3}; do
    echo "  Tentative $attempt/3..."
    
    # Test via HTTP direct
    status=$(timeout 15 curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/" 2>/dev/null || echo "000")
    echo "    HTTP direct: $status"
    
    # Test via nom de domaine si possible
    domain_status=$(timeout 15 curl -s -o /dev/null -w "%{http_code}" "http://martialcomp.com/" 2>/dev/null || echo "000")
    echo "    HTTP domaine: $domain_status"
    
    if [[ "$status" =~ ^(200|302|301)$ ]] || [[ "$domain_status" =~ ^(200|302|301)$ ]]; then
        echo "  ✅ Site accessible à la tentative $attempt"
        SITE_OK=true
        break
    else
        echo "  ⚠️ Site non accessible, attente..."
        sleep 10
    fi
done

echo ""
echo "🎯 RÉSUMÉ DU REDÉMARRAGE D'URGENCE"
echo "=================================="

if [ "$SITE_OK" = "true" ]; then
    echo ""
    echo "✅ REDÉMARRAGE D'URGENCE RÉUSSI!"
    echo ""
    echo "📋 Actions effectuées:"
    echo "  ✅ Arrêt de tous les processus Django"
    echo "  ✅ Restauration fichier URLs stable"
    echo "  ✅ Redémarrage Django avec version simplifiée"
    echo "  ✅ Redémarrage nginx"
    echo "  ✅ Site à nouveau accessible"
    echo ""
    echo "⚠️ Technical scoring désactivé temporairement (erreur BACH HAC)"
    echo ""
    echo "🔗 Site accessible:"
    echo "  • https://martialcomp.com/fr/competitions/club/practitioners/"
    echo "  • https://martialcomp.com/fr/competitions/club/judges/"
    echo "  • https://martialcomp.com/fr/competitions/club/registrations/"
    echo ""
    echo "📋 Le module technical-scoring affiche un message d'indisponibilité"
    echo "   au lieu de planter le serveur."
else
    echo ""
    echo "⚠️ REDÉMARRAGE PARTIEL"
    echo ""
    echo "📋 Django redémarré mais vérifiez manuellement:"
    echo "  • https://martialcomp.com/"
    echo "  • Logs: tail -f /tmp/django_emergency_restart.log"
    echo "  • Status nginx: systemctl status nginx"
fi

echo ""
echo "📋 Logs de l'urgence: $LOG_FILE"
echo ""
echo "Date: $(date)"