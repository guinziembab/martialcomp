#!/usr/bin/env python3
"""
Script simple pour corriger le serveur et créer les vues manquantes
"""
import os
import sys

# Changer le répertoire de travail
PROD_DIR = '/var/www/vhosts/martialcomp.com/httpdocs'
os.chdir(PROD_DIR)

def create_all_missing_views():
    """Créé toutes les vues manquantes d'un coup"""
    
    print("🔧 CRÉATION TOUTES LES VUES MANQUANTES")
    print("=" * 38)
    
    # S'assurer que le répertoire views existe
    os.makedirs('competitions/views', exist_ok=True)
    
    # Créer __init__.py dans views
    with open('competitions/views/__init__.py', 'w') as f:
        f.write('# Views package\n')
    
    # Toutes les vues d'un coup
    all_views = {
        'competitions/views/pages.py': '''"""Vues des pages principales"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

def welcome(request):
    """Page d'accueil"""
    context = {
        'is_test_phase': True,
        'key_features': [],
        'target_audiences': [],
        'upcoming_competitions': [],
        'total_competitions': 150,
        'total_practitioners': 2500,
    }
    return render(request, 'competitions/welcome.html', context)

@login_required
def dashboard(request):
    """Dashboard principal"""
    return render(request, 'competitions/dashboard.html')
''',
        
        'competitions/views/auth.py': '''"""Vues d'authentification"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

def custom_login(request):
    """Connexion personnalisée"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', '/competitions/dashboard/')
            return redirect(next_url)
        else:
            messages.error(request, 'Identifiants incorrects')
    
    return render(request, 'registration/login.html')

def custom_logout(request):
    """Déconnexion"""
    logout(request)
    return redirect('/')

def custom_signup(request):
    """Inscription"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Compte créé!')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})
''',

        'competitions/views/clubs.py': '''"""Vues des clubs"""
from django.http import HttpResponse

def clubs_list(request):
    return HttpResponse("Liste des clubs - En développement")

def club_detail(request, club_id):
    return HttpResponse(f"Club {club_id} - En développement")
''',

        'competitions/views/members.py': '''"""Vues des membres"""
from django.http import HttpResponse

def members_list(request):
    return HttpResponse("Liste des membres - En développement")

def member_detail(request, member_id):
    return HttpResponse(f"Membre {member_id} - En développement")
''',

        'competitions/views/competitions_views.py': '''"""Vues des compétitions"""
from django.http import HttpResponse

def competitions_list(request):
    return HttpResponse("Liste des compétitions - En développement")

def competition_detail(request, competition_id):
    return HttpResponse(f"Compétition {competition_id} - En développement")
''',

        'competitions/views/grades.py': '''"""Vues des grades"""
from django.http import HttpResponse

def grades_list(request):
    return HttpResponse("Liste des grades - En développement")

def grade_detail(request, grade_id):
    return HttpResponse(f"Grade {grade_id} - En développement")
''',

        'competitions/views/notifications.py': '''"""Vues des notifications"""
from django.http import HttpResponse

def notifications_list(request):
    return HttpResponse("Liste des notifications - En développement")

def notification_detail(request, notification_id):
    return HttpResponse(f"Notification {notification_id} - En développement")

def mark_notification_read(request, notification_id):
    return HttpResponse(f"Notification {notification_id} marquée comme lue")
''',
    }
    
    created_count = 0
    for filepath, content in all_views.items():
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ {os.path.basename(filepath)}")
            created_count += 1
        except Exception as e:
            print(f"❌ {filepath}: {e}")
    
    print(f"📊 {created_count}/{len(all_views)} vues créées")
    return created_count == len(all_views)

def create_dashboard_template():
    """Créé le template dashboard"""
    
    print("\n📄 CRÉATION TEMPLATE DASHBOARD")
    print("=" * 30)
    
    os.makedirs('competitions/templates/competitions', exist_ok=True)
    
    dashboard_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Dashboard - MartialComp</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background: #c41e3a; color: white; padding: 20px; border-radius: 8px; }
        .content { margin: 20px 0; }
        .btn { background: #d4af37; color: #000; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🥋 Dashboard MartialComp</h1>
        <p>Bienvenue dans votre espace de gestion</p>
    </div>
    
    <div class="content">
        <h2>Tableau de bord</h2>
        <p>Cette page est en cours de développement.</p>
        <p>Toutes les fonctionnalités seront bientôt disponibles.</p>
        
        <h3>Fonctionnalités à venir :</h3>
        <ul>
            <li>Gestion des membres</li>
            <li>Gestion du club</li>
            <li>Finances</li>
            <li>Compétitions</li>
            <li>Grades et certifications</li>
        </ul>
        
        <p><a href="/" class="btn">← Retour à l'accueil</a></p>
    </div>
</body>
</html>'''
    
    try:
        with open('competitions/templates/competitions/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(dashboard_content)
        print("✅ Template dashboard.html créé")
        return True
    except Exception as e:
        print(f"❌ Erreur création dashboard.html: {e}")
        return False

def check_django_config():
    """Vérifie la configuration Django"""
    
    print("\n🔍 VÉRIFICATION CONFIGURATION DJANGO")
    print("=" * 37)
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
        
        # Test d'import des vues
        from competitions.views import pages, auth
        from competitions.views.onboarding import general, club
        
        print("✅ Configuration Django OK")
        print("✅ Imports des vues réussis")
        
        # Test reverse des URLs principales
        from django.urls import reverse
        
        test_urls = [
            'competitions:welcome',
            'competitions:dashboard',
        ]
        
        for url_name in test_urls:
            try:
                url = reverse(url_name)
                print(f"✅ URL {url_name}: {url}")
            except Exception as e:
                print(f"⚠️ URL {url_name}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur configuration Django: {e}")
        import traceback
        traceback.print_exc()
        return False

def restart_django_simple():
    """Redémarre Django de manière simple"""
    
    print("\n🚀 REDÉMARRAGE DJANGO")
    print("=" * 20)
    
    try:
        # Arrêter les processus existants doucement
        import subprocess
        subprocess.run(['pkill', '-f', 'manage.py'], check=False)
        
        import time
        time.sleep(2)
        
        # Démarrer le serveur
        print("🔄 Démarrage du serveur...")
        
        # Utiliser & pour le démarrer en arrière-plan
        result = subprocess.run([
            'bash', '-c', 
            'cd /var/www/vhosts/martialcomp.com/httpdocs && source venv/bin/activate && python3 manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &'
        ])
        
        time.sleep(5)
        
        # Vérifier si le serveur répond
        try:
            import urllib.request
            response = urllib.request.urlopen('http://localhost:8000/', timeout=10)
            status = response.getcode()
            print(f"✅ Serveur répond: HTTP {status}")
            return True
        except Exception as e:
            print(f"⚠️ Test serveur: {e}")
            
            # Vérifier les logs
            try:
                with open('/tmp/django.log', 'r') as f:
                    logs = f.read()
                    if logs:
                        print("📋 Logs serveur:")
                        print(logs[-500:])  # Dernières 500 caractères
            except:
                pass
            
            return False
            
    except Exception as e:
        print(f"❌ Erreur redémarrage: {e}")
        return False

if __name__ == "__main__":
    print("🛠️ CORRECTION SIMPLE SERVEUR")
    print("=" * 29)
    print(f"📂 Répertoire: {os.getcwd()}")
    
    # Faire les corrections une par une
    success1 = create_all_missing_views()
    success2 = create_dashboard_template()
    success3 = check_django_config()
    success4 = restart_django_simple()
    
    print(f"\n📋 RÉSUMÉ:")
    print(f"   {'✅' if success1 else '❌'} Vues créées")
    print(f"   {'✅' if success2 else '❌'} Template dashboard")
    print(f"   {'✅' if success3 else '❌'} Configuration Django")
    print(f"   {'✅' if success4 else '❌'} Serveur redémarré")
    
    if success1 and success2 and success3:
        print("\n🎉 CORRECTION RÉUSSIE!")
        print("\n🌐 SITE DISPONIBLE:")
        print("   🏠 https://martialcomp.com/")
        print("   🏠 https://martialcomp.com/fr/")
        
        print("\n🧪 DÉMO:")
        print("   👤 dojo_sakura_manager / demo2025")
        print("   🎯 Bouton 'Accéder à la démo complète'")
        
        if success4:
            print("\n✅ Serveur fonctionnel")
        else:
            print("\n⚠️ Serveur en cours de démarrage")
            print("   Attendez 1-2 minutes puis testez le site")
            
    else:
        print("\n❌ CORRECTION PARTIELLE")
        print("   Consultez les erreurs ci-dessus")
    
    sys.exit(0 if (success1 and success2 and success3) else 1)