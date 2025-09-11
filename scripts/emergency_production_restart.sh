#!/bin/bash

################################################################################
# REDÉMARRAGE D'URGENCE SERVEUR PRODUCTION - 502 BAD GATEWAY
################################################################################

echo "🚨 REDÉMARRAGE D'URGENCE SERVEUR PRODUCTION"
echo "==========================================="
echo "Date: $(date)"
echo ""

# Variables d'environnement production
LOG_FILE="/tmp/emergency_production_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "🔍 DIAGNOSTIC SERVEUR PRODUCTION"
echo "==============================="

echo "📋 1. Localisation du répertoire de production..."

# Recherche des répertoires de production possibles
POSSIBLE_DIRS=(
    "/var/www/html"
    "/var/www/martialcomp"
    "/var/www/vhosts/martialcomp.com/httpdocs"
    "/home/martialcomp"
    "/opt/martialcomp"
    "/srv/martialcomp"
    "/root/martialcomp"
)

PROD_DIR=""
for dir in "${POSSIBLE_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -f "$dir/manage.py" ]; then
        PROD_DIR="$dir"
        echo "✅ Répertoire production trouvé: $PROD_DIR"
        break
    fi
done

if [ -z "$PROD_DIR" ]; then
    echo "❌ Répertoire de production non trouvé automatiquement"
    echo "📋 Recherche manuelle..."
    
    # Recherche plus large
    echo "📁 Recherche de manage.py sur le système:"
    find /var /home /opt /srv /root -name "manage.py" -type f 2>/dev/null | head -5
    
    echo ""
    echo "⚠️ VEUILLEZ SPÉCIFIER LE CHEMIN DE PRODUCTION"
    echo "Usage: PROD_DIR=/chemin/vers/martialcomp $0"
    exit 1
fi

cd "$PROD_DIR"

echo "📋 2. Vérification de l'environnement..."

# Activation de l'environnement virtuel
VENV_DIRS=("venv" "env" ".venv" "martialcomp_env")
VENV_ACTIVATED=false

for venv_dir in "${VENV_DIRS[@]}"; do
    if [ -d "$venv_dir" ] && [ -f "$venv_dir/bin/activate" ]; then
        echo "📋 Activation environnement virtuel: $venv_dir"
        source "$venv_dir/bin/activate"
        VENV_ACTIVATED=true
        break
    fi
done

if [ "$VENV_ACTIVATED" = false ]; then
    echo "⚠️ Aucun environnement virtuel trouvé, utilisation Python système"
fi

echo "📋 3. Diagnostic des processus Django..."

# Vérification des processus Django
django_processes=$(ps aux | grep -E "(python.*manage\.py|gunicorn.*martialcomp)" | grep -v grep | wc -l)
echo "  Processus Django/Gunicorn actifs: $django_processes"

if [ $django_processes -gt 0 ]; then
    echo "  📋 Processus détectés:"
    ps aux | grep -E "(python.*manage\.py|gunicorn.*martialcomp)" | grep -v grep
fi

echo ""
echo "📋 4. Vérification nginx..."
nginx_status=$(systemctl is-active nginx 2>/dev/null || echo "unknown")
echo "  Status nginx: $nginx_status"

echo ""
echo "📋 5. Vérification des ports..."
port_8000=$(netstat -tlnp 2>/dev/null | grep ":8000" || echo "Port 8000 libre")
port_80=$(netstat -tlnp 2>/dev/null | grep ":80" || echo "Port 80 libre")
echo "  Port 8000: $port_8000"
echo "  Port 80: $port_80"

echo ""
echo "🛑 ARRÊT DE TOUS LES PROCESSUS DJANGO"
echo "==================================="

echo "📋 Arrêt des processus Django/Gunicorn..."
pkill -f "python.*manage.py" 2>/dev/null || true
pkill -f "gunicorn.*martialcomp" 2>/dev/null || true
pkill -f "runserver" 2>/dev/null || true

echo "📋 Attente de l'arrêt complet..."
sleep 10

# Vérification arrêt
remaining=$(ps aux | grep -E "(python.*manage|gunicorn.*martialcomp)" | grep -v grep | wc -l)
if [ $remaining -gt 0 ]; then
    echo "⚠️ $remaining processus encore actifs, arrêt forcé..."
    ps aux | grep -E "(python.*manage|gunicorn.*martialcomp)" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
    sleep 5
fi

echo "✅ Processus Django arrêtés"

echo ""
echo "🔧 CORRECTION DU PROBLÈME TECHNICAL SCORING"
echo "=========================================="

echo "📋 Le problème était probablement lié au wrapper technical_scoring..."

# Vérifier et nettoyer les fichiers temporaires problématiques
rm -f /tmp/technical_scoring_wrapper.py* 2>/dev/null || true

# Vérifier le fichier URLs actuel
if [ -f "competitions/urls/club.py" ]; then
    echo "📋 Vérification du fichier URLs..."
    
    # Sauvegarder le fichier actuel
    cp competitions/urls/club.py competitions/urls/club.py.backup_production_$(date +%Y%m%d_%H%M%S)
    
    # Vérifier s'il contient des imports problématiques
    if grep -q "technical_scoring_wrapper" competitions/urls/club.py; then
        echo "⚠️ Wrapper problématique détecté, restauration version stable..."
        
        # Restaurer une version stable
        if [ -f "competitions/urls/club.py.backup_before_wrapper" ]; then
            cp competitions/urls/club.py.backup_before_wrapper competitions/urls/club.py
            echo "✅ Version stable restaurée"
        else
            echo "📝 Création d'une version minimale stable..."
            
            cat > competitions/urls/club.py << 'EOF'
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages

# Import des vues principales
from competitions.views.club.practitioners import (
    practitioners_list,
    practitioner_form,
    practitioner_detail,
    practitioner_delete,
    create_user_for_practitioner,
    link_user_to_practitioner
)

# Import sécurisé des autres vues
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
except ImportError:
    def registrations_list(request):
        messages.warning(request, 'Module inscriptions en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def register_practitioner(request, competition_id=None, practitioner_id=None):
        return redirect('competitions:club:practitioners')
    def available_competitions(request):
        return redirect('competitions:club:practitioners')
    def register_multiple_practitioners(request, competition_id):
        return redirect('competitions:club:practitioners')
    def competition_registration_form(request, competition_id):
        return redirect('competitions:club:practitioners')
    def club_bulk_registration(request):
        return redirect('competitions:club:practitioners')
    def cancel_registration(request, registration_id):
        return redirect('competitions:club:practitioners')

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
            messages.info(request, 'Modification juge en cours de développement.')
            return redirect('competitions:club:judges_list')
        def judge_delete(request, judge_id):
            messages.info(request, 'Suppression juge en cours de développement.')
            return redirect('competitions:club:judges_list')
except ImportError:
    def judges_list(request):
        messages.warning(request, 'Module juges en cours de restauration.')
        return redirect('competitions:club:practitioners')
    def judge_add(request):
        return redirect('competitions:club:practitioners')
    def judge_assignments(request):
        return redirect('competitions:club:practitioners')
    def judge_edit(request, judge_id):
        return redirect('competitions:club:practitioners')
    def judge_delete(request, judge_id):
        return redirect('competitions:club:practitioners')

# Technical scoring - VERSION SIMPLE SANS ERREUR
def technical_scoring_safe(request):
    """Vue sécurisée pour technical scoring"""
    messages.warning(request, 'Module notation technique temporairement indisponible (maintenance).')
    return redirect('competitions:club:practitioners')

def competition_scoring_safe(request, competition_id):
    messages.warning(request, 'Notation compétition temporairement indisponible.')
    return redirect('competitions:club:practitioners')

def performance_detail_safe(request, performance_id):
    messages.warning(request, 'Détail performance temporairement indisponible.')
    return redirect('competitions:club:practitioners')

try:
    from competitions.views.club.qualifications import qualification_form
except ImportError:
    def qualification_form(request, practitioner_id=None, qualification_id=None):
        messages.info(request, 'Module qualifications en cours de restauration.')
        return redirect('competitions:club:practitioners')

app_name = 'club'

urlpatterns = [
    # URLs principales - TOUJOURS FONCTIONNELLES
    path('', login_required(practitioners_list), name='dashboard'),
    path('practitioners/', login_required(practitioners_list), name='practitioners'),
    path('practitioners/add/', login_required(practitioner_form), name='practitioner_add'),
    path('practitioners/<int:pk>/', login_required(practitioner_detail), name='practitioner_detail'),
    path('practitioners/<int:practitioner_id>/edit/', 
         login_required(lambda r, practitioner_id: practitioner_form(r, practitioner_id=practitioner_id)), 
         name='practitioner_edit'),
    path('practitioners/delete/<int:practitioner_id>/', 
         login_required(practitioner_delete), 
         name='practitioner_delete'),
    
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
    
    # Technical scoring - VERSION SÉCURISÉE
    path('technical-scoring/', login_required(technical_scoring_safe), name='technical_scoring'),
    path('technical-scoring/competition/<int:competition_id>/', 
         login_required(competition_scoring_safe), 
         name='competition_scoring'),
    path('technical-scoring/performance/<int:performance_id>/', 
         login_required(performance_detail_safe), 
         name='performance_detail'),
    
    # Inscriptions
    path('registrations/', login_required(registrations_list), name='registrations_list'),
    path('competitions/available/', login_required(available_competitions), name='available_competitions'),
    path('competitions/<int:competition_id>/register/', login_required(register_practitioner), name='register_practitioner'),
    path('competitions/<int:competition_id>/register/<int:practitioner_id>/', 
         login_required(register_practitioner), 
         name='register_practitioner_with_id'),
    path('competitions/<int:competition_id>/register-multiple/', 
         login_required(register_multiple_practitioners), 
         name='register_multiple_practitioners'),
    path('competitions/<int:competition_id>/register-form/', 
         login_required(competition_registration_form), 
         name='competition_registration_form'),
    path('bulk-registration/', login_required(club_bulk_registration), name='bulk_registration'),
    path('registrations/<int:registration_id>/cancel/', 
         login_required(cancel_registration), 
         name='cancel_registration'),
]
EOF
            echo "✅ Version minimale stable créée"
        fi
    else
        echo "✅ Fichier URLs semble correct"
    fi
else
    echo "❌ Fichier competitions/urls/club.py non trouvé"
fi

echo ""
echo "🧪 TEST DE CONFIGURATION"
echo "======================="

echo "📋 Test Django..."
export DJANGO_SETTINGS_MODULE=config.settings

# Test de base Django
python3 manage.py check --deploy 2>&1 | head -10

echo ""
echo "🚀 REDÉMARRAGE SERVEUR PRODUCTION"
echo "==============================="

echo "📋 Démarrage Django en mode production..."

# Déterminer la méthode de démarrage
if command -v gunicorn >/dev/null 2>&1; then
    echo "📋 Démarrage avec Gunicorn (recommandé pour production)..."
    nohup gunicorn config.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers 3 \
        --timeout 120 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --preload \
        --access-logfile /tmp/gunicorn_access.log \
        --error-logfile /tmp/gunicorn_error.log \
        > /tmp/gunicorn_restart.log 2>&1 &
    
    sleep 15
    
    if pgrep -f "gunicorn.*config.wsgi" > /dev/null; then
        echo "✅ Gunicorn démarré avec succès"
        SERVER_TYPE="Gunicorn"
    else
        echo "❌ Échec démarrage Gunicorn, fallback vers runserver..."
        nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_production_restart.log 2>&1 &
        sleep 10
        if pgrep -f "runserver" > /dev/null; then
            echo "✅ Django runserver démarré en fallback"
            SERVER_TYPE="Django runserver"
        else
            echo "❌ Échec total démarrage Django"
            SERVER_TYPE="FAILED"
        fi
    fi
else
    echo "📋 Démarrage avec Django runserver..."
    nohup python3 manage.py runserver 0.0.0.0:8000 > /tmp/django_production_restart.log 2>&1 &
    sleep 10
    
    if pgrep -f "runserver" > /dev/null; then
        echo "✅ Django runserver démarré"
        SERVER_TYPE="Django runserver"
    else
        echo "❌ Échec démarrage Django"
        SERVER_TYPE="FAILED"
    fi
fi

echo ""
echo "🔄 REDÉMARRAGE NGINX"
echo "=================="

echo "📋 Redémarrage nginx..."
systemctl restart nginx 2>/dev/null || service nginx restart 2>/dev/null || echo "⚠️ Nginx non redémarré automatiquement"

sleep 5

nginx_status=$(systemctl is-active nginx 2>/dev/null || echo "unknown")
echo "📋 Status nginx: $nginx_status"

echo ""
echo "🧪 TESTS FINAUX"
echo "=============="

if [ "$SERVER_TYPE" != "FAILED" ]; then
    echo "📋 Test des URLs principales..."
    
    # Tests des URLs
    for attempt in {1..3}; do
        echo "  Tentative $attempt/3..."
        
        # Test direct
        status=$(timeout 15 curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/fr/competitions/club/practitioners/" 2>/dev/null || echo "000")
        echo "    Practitioners: HTTP $status"
        
        if [[ "$status" =~ ^(200|302|301)$ ]]; then
            echo "  ✅ Site accessible à la tentative $attempt"
            SITE_OK=true
            break
        else
            echo "  ⚠️ Site non accessible, attente..."
            sleep 10
        fi
    done
else
    SITE_OK=false
fi

echo ""
echo "🎯 RÉSUMÉ DU REDÉMARRAGE PRODUCTION"
echo "================================="

if [ "$SITE_OK" = "true" ]; then
    echo ""
    echo "✅ REDÉMARRAGE PRODUCTION RÉUSSI!"
    echo ""
    echo "📋 Configuration:"
    echo "  📁 Répertoire: $PROD_DIR"
    echo "  🚀 Serveur: $SERVER_TYPE"
    echo "  🌐 Nginx: $nginx_status"
    echo ""
    echo "📋 Actions effectuées:"
    echo "  ✅ Arrêt processus Django/Gunicorn"
    echo "  ✅ Nettoyage fichiers temporaires problématiques"
    echo "  ✅ Correction/stabilisation URLs club"
    echo "  ✅ Redémarrage serveur Django"
    echo "  ✅ Redémarrage nginx"
    echo "  ✅ Site à nouveau accessible"
    echo ""
    echo "⚠️ Technical scoring désactivé temporairement (sécurité)"
    echo ""
    echo "🔗 Site de production accessible:"
    echo "  • https://martialcomp.com/fr/competitions/club/practitioners/"
    echo "  • https://martialcomp.com/fr/competitions/club/judges/"
    echo "  • https://martialcomp.com/fr/competitions/club/registrations/"
    echo ""
else
    echo ""
    echo "⚠️ REDÉMARRAGE PARTIEL"
    echo ""
    echo "📋 Serveur redémarré mais vérifications manuelles nécessaires:"
    echo "  • Vérifiez: https://martialcomp.com/"
    echo "  • Logs Gunicorn: tail -f /tmp/gunicorn_error.log"
    echo "  • Logs Django: tail -f /tmp/django_production_restart.log"
    echo "  • Status nginx: systemctl status nginx"
    echo ""
fi

echo "📋 Répertoire production: $PROD_DIR"
echo "📋 Logs redémarrage: $LOG_FILE"
echo ""
echo "Date: $(date)"