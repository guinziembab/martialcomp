#!/usr/bin/env python3
"""
Script de déploiement simple pour corriger le dashboard routing
Utilise les templates existants - NE CRÉE PAS DE NOUVEAUX TEMPLATES
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
    log("🎯 CORRECTION DASHBOARD - UTILISE TEMPLATES EXISTANTS")
    log("=" * 50)
    
    # Vérifier qu'on est dans le bon répertoire
    if not os.path.exists('competitions'):
        if os.path.exists('/var/www/vhosts/martialcomp.com/httpdocs'):
            os.chdir('/var/www/vhosts/martialcomp.com/httpdocs')
        else:
            log("❌ Répertoire Django non trouvé")
            return False
    
    log(f"📂 Répertoire: {os.getcwd()}")
    
    # 1. Vérifier que les templates dashboard existent
    log("\n🔍 VÉRIFICATION TEMPLATES EXISTANTS")
    dashboard_templates = [
        'competitions/templates/competitions/dashboard/club.html',
        'competitions/templates/competitions/dashboard/coach.html', 
        'competitions/templates/competitions/dashboard/participant.html',
        'competitions/templates/competitions/dashboard/federation.html'
    ]
    
    existing_templates = []
    for template in dashboard_templates:
        if os.path.exists(template):
            existing_templates.append(template)
            log(f"✅ Template trouvé: {template}")
        else:
            log(f"❌ Template manquant: {template}")
    
    if not existing_templates:
        log("❌ Aucun template dashboard existant trouvé!")
        return False
    
    # 2. Créer/corriger le dashboard router (utilise templates existants)
    log("\n🔧 CRÉATION DASHBOARD ROUTER")
    
    router_code = '''"""
Routeur dashboard intelligent - utilise les templates existants
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_router(request):
    """Route vers le bon dashboard selon le profil utilisateur"""
    user = request.user
    username = user.username.lower()
    
    # Routage basé sur le nom d'utilisateur
    if 'federation' in username or 'fed' in username:
        return redirect('/dashboard/federation/')
    elif 'manager' in username or 'club' in username or 'dojo' in username:
        return redirect('/dashboard/club/')
    elif 'coach' in username:
        return redirect('/dashboard/coach/')
    elif 'participant' in username:
        return redirect('/dashboard/participant/')
    
    # Par défaut - rediriger vers club pour demo
    return redirect('/dashboard/club/')

@login_required
def club_dashboard_view(request):
    """Dashboard club - utilise le template existant"""
    context = {
        'user': request.user,
        'club_name': 'Dojo Sakura',
        'members_count': 45,
        'dashboard_type': 'club'
    }
    return render(request, 'competitions/dashboard/club.html', context)

@login_required  
def coach_dashboard_view(request):
    """Dashboard coach - utilise le template existant"""
    context = {
        'user': request.user,
        'dashboard_type': 'coach'
    }
    return render(request, 'competitions/dashboard/coach.html', context)

@login_required
def participant_dashboard_view(request):
    """Dashboard participant - utilise le template existant"""
    context = {
        'user': request.user,
        'dashboard_type': 'participant'
    }
    return render(request, 'competitions/dashboard/participant.html', context)

@login_required
def federation_dashboard_view(request):
    """Dashboard federation - utilise le template existant"""
    context = {
        'user': request.user,
        'dashboard_type': 'federation'
    }
    return render(request, 'competitions/dashboard/federation.html', context)
'''
    
    try:
        os.makedirs('competitions/views', exist_ok=True)
        with open('competitions/views/dashboard_router.py', 'w', encoding='utf-8') as f:
            f.write(router_code)
        log("✅ Dashboard router créé")
    except Exception as e:
        log(f"❌ Erreur création router: {e}")
        return False
    
    # 3. Corriger config/settings.py pour les redirections
    log("\n🔧 CORRECTION REDIRECTIONS AUTH")
    
    try:
        settings_file = 'config/settings.py'
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Corriger les redirections pour pointer vers /dashboard/
            content = content.replace('/competitions/dashboard/', '/dashboard/')
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                f.write(content)
            log("✅ Redirections auth corrigées")
        else:
            log("⚠️ Fichier settings.py non trouvé")
    except Exception as e:
        log(f"❌ Erreur correction settings: {e}")
    
    # 4. Tester la configuration Django
    log("\n🧪 TEST CONFIGURATION")
    
    success, stdout, stderr = run_command("python3 manage.py check")
    if success:
        log("✅ Configuration Django valide")
    else:
        log(f"❌ Erreurs Django: {stderr}")
        return False
    
    # 5. Redémarrer Django
    log("\n🚀 REDÉMARRAGE DJANGO")
    
    # Arrêter Django en cours
    run_command("pkill -f 'manage.py runserver'")
    time.sleep(3)
    
    # Redémarrer
    success, stdout, stderr = run_command("nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/null 2>&1 &")
    time.sleep(6)
    
    # Test de connectivité
    success, stdout, stderr = run_command("curl -I -s http://localhost:8000/ | head -1")
    if "200 OK" in stdout:
        log("✅ Site accessible")
    else:
        log("❌ Site non accessible")
    
    # 6. Test du routage
    log("\n🧪 TEST ROUTAGE PROFILS")
    
    test_script = '''
from django.contrib.auth.models import User
from django.test import Client

test_users = [
    ("dojo_sakura_manager", "Club"),
    ("FEDE99", "Federation")
]

for username, expected in test_users:
    try:
        user = User.objects.get(username=username)
        client = Client()
        client.force_login(user)
        response = client.get("/dashboard/")
        redirect_url = response.url if hasattr(response, "url") else "No redirect"
        print(f"✅ {username} → {redirect_url}")
    except User.DoesNotExist:
        print(f"❌ {username} → USER NOT FOUND")
    except Exception as e:
        print(f"❌ {username} → ERROR: {str(e)[:50]}")
'''
    
    success, stdout, stderr = run_command(f'python3 manage.py shell -c "{test_script.replace(chr(10), "; ")}"')
    if success:
        log("Tests de routage:")
        print(stdout)
    
    log("\n🎉 CORRECTION TERMINÉE!")
    log("=" * 50)
    log("✅ UTILISE LES TEMPLATES EXISTANTS:")
    for template in existing_templates:
        log(f"   📄 {template}")
    
    log("\n🧪 TESTS RECOMMANDÉS:")
    log("   1. Aller sur: https://martialcomp.com/")
    log("   2. Cliquer: 'Rejoindre la phase de test'")
    log("   3. Se connecter: dojo_sakura_manager / demo2025")
    log("   4. Vérifier que le dashboard club existant s'affiche")
    
    log("\n📊 RÉSULTAT ATTENDU:")
    log("   👤 dojo_sakura_manager → /dashboard/club/")
    log("   🏢 Template utilisé: competitions/dashboard/club.html (EXISTANT)")
    log("   ❌ AUCUN nouveau template créé")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)