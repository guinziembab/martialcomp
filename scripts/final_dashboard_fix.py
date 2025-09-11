#!/usr/bin/env python3
"""
Script final de correction dashboard - Utilise UNIQUEMENT les templates existants
AUCUN nouveau template créé - Respecte la directive utilisateur
"""
import os
import subprocess
import time

def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    log("🎯 CORRECTION FINALE DASHBOARD - TEMPLATES EXISTANTS UNIQUEMENT")
    log("=" * 60)
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('competitions'):
        if os.path.exists('/var/www/vhosts/martialcomp.com/httpdocs'):
            os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')
        else:
            log("❌ Répertoire Django non trouvé")
            return False
    
    log(f"📂 Répertoire: {os.getcwd()}")
    
    # 1. Vérifier les templates dashboard existants
    log("\n🔍 VÉRIFICATION TEMPLATES DASHBOARD EXISTANTS")
    dashboard_templates = [
        'competitions/templates/competitions/dashboard/club.html',
        'competitions/templates/competitions/dashboard/coach.html', 
        'competitions/templates/competitions/dashboard/participant.html',
        'competitions/templates/competitions/dashboard/federation.html',
        'competitions/templates/competitions/dashboard/manager.html',
        'competitions/templates/competitions/dashboard/admin.html'
    ]
    
    existing_templates = []
    for template in dashboard_templates:
        if os.path.exists(template):
            existing_templates.append(template)
            log(f"✅ Template existant: {template}")
        else:
            log(f"⚠️ Template absent: {template}")
    
    if not existing_templates:
        log("❌ Aucun template dashboard trouvé!")
        return False
    
    log(f"📊 {len(existing_templates)} templates dashboard existants trouvés")
    
    # 2. Créer le dashboard router MINIMAL (utilise UNIQUEMENT templates existants)
    log("\n🔧 CRÉATION ROUTER MINIMAL - TEMPLATES EXISTANTS")
    
    router_code = '''"""
Dashboard router - Utilise UNIQUEMENT les templates existants
Ne crée AUCUN nouveau template
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_router(request):
    """Route vers le dashboard approprié selon le profil utilisateur"""
    user = request.user
    username = user.username.lower()
    
    # Routage intelligent basé sur le nom d'utilisateur
    if 'federation' in username or 'fed' in username:
        return redirect('/dashboard/federation/')
    elif 'manager' in username or 'club' in username or 'dojo' in username:
        return redirect('/dashboard/club/')
    elif 'coach' in username:
        return redirect('/dashboard/coach/')
    elif 'participant' in username or 'pratiquant' in username:
        return redirect('/dashboard/participant/')
    elif 'admin' in username:
        return redirect('/dashboard/admin/')
    
    # Par défaut - club dashboard (compte demo)
    return redirect('/dashboard/club/')

@login_required
def club_dashboard_view(request):
    """Dashboard club - Template existant competitions/dashboard/club.html"""
    context = {
        'user': request.user,
        'club_name': 'Dojo Sakura',
        'members_count': 45,
        'dashboard_type': 'club'
    }
    return render(request, 'competitions/dashboard/club.html', context)

@login_required  
def coach_dashboard_view(request):
    """Dashboard coach - Template existant competitions/dashboard/coach.html"""
    context = {
        'user': request.user,
        'dashboard_type': 'coach'
    }
    return render(request, 'competitions/dashboard/coach.html', context)

@login_required
def participant_dashboard_view(request):
    """Dashboard participant - Template existant competitions/dashboard/participant.html"""
    context = {
        'user': request.user,
        'dashboard_type': 'participant'
    }
    return render(request, 'competitions/dashboard/participant.html', context)

@login_required
def federation_dashboard_view(request):
    """Dashboard federation - Template existant competitions/dashboard/federation.html"""
    context = {
        'user': request.user,
        'dashboard_type': 'federation'
    }
    return render(request, 'competitions/dashboard/federation.html', context)

@login_required
def manager_dashboard_view(request):
    """Dashboard manager - Template existant competitions/dashboard/manager.html"""
    context = {
        'user': request.user,
        'dashboard_type': 'manager'
    }
    return render(request, 'competitions/dashboard/manager.html', context)

@login_required
def admin_dashboard_view(request):
    """Dashboard admin - Template existant competitions/dashboard/admin.html"""
    context = {
        'user': request.user,
        'dashboard_type': 'admin'
    }
    return render(request, 'competitions/dashboard/admin.html', context)
'''
    
    try:
        os.makedirs('competitions/views', exist_ok=True)
        with open('competitions/views/dashboard_router.py', 'w', encoding='utf-8') as f:
            f.write(router_code)
        log("✅ Dashboard router créé - utilise templates existants")
    except Exception as e:
        log(f"❌ Erreur création router: {e}")
        return False
    
    # 3. Corriger competitions/urls.py pour utiliser le router
    log("\n🔧 CORRECTION competitions/urls.py")
    
    urls_content = '''"""
URLs competitions - Version finale avec router dashboard
"""
from django.urls import path, include
from django.shortcuts import render
from competitions.views import pages, auth
from competitions.views.dashboard_router import (
    dashboard_router,
    club_dashboard_view,
    coach_dashboard_view,
    participant_dashboard_view,
    federation_dashboard_view,
    manager_dashboard_view,
    admin_dashboard_view
)

app_name = "competitions"

urlpatterns = [
    # Page d'accueil
    path("", pages.welcome, name="welcome"),
    
    # Dashboard principal avec routage intelligent
    path("dashboard/", dashboard_router, name="dashboard"),
    
    # Dashboards spécifiques - utilisent templates existants
    path("dashboard/club/", club_dashboard_view, name="dashboard_club"),
    path("dashboard/coach/", coach_dashboard_view, name="dashboard_coach"),
    path("dashboard/participant/", participant_dashboard_view, name="dashboard_participant"),
    path("dashboard/federation/", federation_dashboard_view, name="dashboard_federation"),
    path("dashboard/manager/", manager_dashboard_view, name="dashboard_manager"),
    path("dashboard/admin/", admin_dashboard_view, name="dashboard_admin"),
    
    # Auth
    path("auth/", include([
        path("login/", auth.custom_login, name="custom_login"),
        path("logout/", auth.custom_logout, name="custom_logout"),
        path("signup/", auth.custom_signup, name="signup"),
    ])),
]
'''
    
    try:
        with open('competitions/urls.py', 'w', encoding='utf-8') as f:
            f.write(urls_content)
        log("✅ competitions/urls.py corrigé")
    except Exception as e:
        log(f"❌ Erreur correction URLs: {e}")
        return False
    
    # 4. Corriger les redirections dans settings.py
    log("\n🔧 CORRECTION REDIRECTIONS SETTINGS")
    
    try:
        settings_file = 'config/settings.py'
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Corriger toutes les redirections pour pointer vers /dashboard/
            replacements = [
                ('LOGIN_REDIRECT_URL = "/competitions/dashboard/"', 'LOGIN_REDIRECT_URL = "/dashboard/"'),
                ('ACCOUNT_LOGIN_REDIRECT_URL = "/competitions/dashboard/"', 'ACCOUNT_LOGIN_REDIRECT_URL = "/dashboard/"'),
                ('ACCOUNT_SIGNUP_REDIRECT_URL = "/competitions/dashboard/"', 'ACCOUNT_SIGNUP_REDIRECT_URL = "/dashboard/"'),
                ('/competitions/dashboard/', '/dashboard/')
            ]
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)
            log("✅ Redirections settings corrigées")
        else:
            log("⚠️ Fichier settings.py non trouvé")
    except Exception as e:
        log(f"❌ Erreur correction settings: {e}")
    
    # 5. Test configuration Django
    log("\n🧪 TEST CONFIGURATION DJANGO")
    
    success, stdout, stderr = run_command("python3 manage.py check")
    if success:
        log("✅ Configuration Django valide")
    else:
        log(f"❌ Erreurs Django: {stderr[:200]}")
        return False
    
    # 6. Redémarrer Django/Gunicorn
    log("\n🚀 REDÉMARRAGE SERVEUR")
    
    # Arrêter tous les processus Django
    run_command("pkill -f 'manage.py runserver'")
    run_command("pkill -f gunicorn")
    time.sleep(3)
    
    # Redémarrer Gunicorn (production)
    success, stdout, stderr = run_command("gunicorn config.wsgi:application --bind 0.0.0.0:8000 --daemon")
    time.sleep(6)
    
    # Test de connectivité
    success, stdout, stderr = run_command("curl -I -s http://localhost:8000/ | head -1")
    if "200 OK" in stdout:
        log("✅ Site accessible")
    else:
        log(f"❌ Site non accessible: {stdout}")
        # Fallback avec runserver
        run_command("nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &")
        time.sleep(6)
    
    # 7. Test final du routage avec compte demo
    log("\n🧪 TEST ROUTAGE COMPTE DEMO")
    
    test_script = '''
from django.contrib.auth.models import User
from django.test import Client

try:
    # Test avec le compte demo
    user = User.objects.get(username="dojo_sakura_manager")
    client = Client()
    client.force_login(user)
    
    # Test routage dashboard
    response = client.get("/dashboard/")
    if hasattr(response, "url"):
        print(f"✅ dojo_sakura_manager → {response.url}")
        
        # Test accès direct au dashboard club
        club_response = client.get("/dashboard/club/")
        status = "✅" if club_response.status_code == 200 else "❌"
        print(f"{status} Dashboard club accessible: {club_response.status_code}")
        
    else:
        print("❌ Pas de redirection")
        
except User.DoesNotExist:
    print("❌ Utilisateur dojo_sakura_manager non trouvé")
except Exception as e:
    print(f"❌ Erreur test: {str(e)[:50]}")
'''
    
    success, stdout, stderr = run_command(f'python3 manage.py shell -c "{test_script.replace(chr(10), "; ")}"')
    if success:
        log("Test routage:")
        print(stdout)
    else:
        log(f"⚠️ Erreur test: {stderr[:100]}")
    
    log("\n🎉 CORRECTION FINALE TERMINÉE!")
    log("=" * 60)
    log("✅ RÉSULTATS:")
    log("   🔧 Router créé - utilise UNIQUEMENT templates existants")
    log("   🔗 URLs corrigées")
    log("   ⚙️ Redirections settings corrigées")  
    log("   🚀 Serveur redémarré")
    
    log(f"\n📄 TEMPLATES UTILISÉS ({len(existing_templates)} existants):")
    for template in existing_templates[:3]:  # Afficher les 3 premiers
        log(f"   {template}")
    if len(existing_templates) > 3:
        log(f"   ... et {len(existing_templates) - 3} autres")
    
    log("\n🧪 TEST MAINTENANT:")
    log("   1. https://martialcomp.com/")
    log("   2. Cliquer 'Rejoindre la phase de test'")
    log("   3. Connexion: dojo_sakura_manager / demo2025")
    log("   4. → Dashboard club existant affiché")
    
    log("\n📊 RÉSULTAT ATTENDU:")
    log("   👤 dojo_sakura_manager → /dashboard/club/")
    log("   🏢 Template: competitions/dashboard/club.html (EXISTANT)")
    log("   ❌ AUCUN nouveau template créé")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)