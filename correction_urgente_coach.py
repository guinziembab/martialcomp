# -*- coding: utf-8 -*-
"""
Correction urgente des problemes de routage coach identifies
"""

print("CORRECTION URGENTE PROBLEMES ROUTAGE COACH")
print("=" * 45)

# 1. CORRIGER LES SETTINGS DE REDIRECTION
print("1. CORRECTION SETTINGS REDIRECTION")
print("=" * 35)

print("PROBLEME IDENTIFIE:")
print("  LOGIN_REDIRECT_URL: /competitions/onboarding/role/")
print("  ACCOUNT_LOGIN_REDIRECT_URL: /competitions/onboarding/role/")
print("")
print("SOLUTION:")
print("  Ces settings forcent TOUS les utilisateurs vers l'onboarding")
print("  Il faut les changer vers le dashboard_router")
print("")
print("MODIFICATION REQUISE dans settings.py:")
print("  LOGIN_REDIRECT_URL = '/competitions/dashboard/'")
print("  ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/dashboard/'")

# 2. ANALYSER LE MIDDLEWARE OnboardingRedirectMiddleware  
print(f"\n2. ANALYSE MIDDLEWARE ONBOARDING")
print("=" * 35)

try:
    from apps.competitions.middleware import OnboardingRedirectMiddleware
    print("Middleware OnboardingRedirectMiddleware trouve")
    
    # Verifier le code du middleware
    import inspect
    source = inspect.getsource(OnboardingRedirectMiddleware)
    
    if 'dashboard' in source:
        print("  Le middleware contient des regles pour 'dashboard'")
        print("  Il intercepte probablement les redirections dashboard")
    
    print("  SOLUTION: Modifier le middleware pour exclure les coaches")
    print("  ou desactiver temporairement ce middleware")
    
except Exception as e:
    print(f"Erreur analyse middleware: {e}")

# 3. VERIFIER LA CONFIGURATION URLS
print(f"\n3. VERIFICATION URLS DASHBOARD")
print("=" * 30)

import os

# Chercher les fichiers URLs
urls_files = [
    'apps/competitions/urls.py',
    'competitions/urls.py',
    'apps/competitions/urls/__init__.py'
]

dashboard_router_found = False

for urls_file in urls_files:
    if os.path.exists(urls_file):
        print(f"Analyse {urls_file}:")
        
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'dashboard_router' in content:
            dashboard_router_found = True
            print("  dashboard_router trouve dans le fichier")
            
            # Extraire les lignes avec dashboard_router
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'dashboard_router' in line and 'path(' in line:
                    print(f"    Ligne {i+1}: {line.strip()}")
        else:
            print("  dashboard_router NON trouve")

if not dashboard_router_found:
    print("\nPROBLEME: dashboard_router n'est pas configure dans les URLs")
    print("SOLUTION: Ajouter la route dashboard_router dans urls.py")

# 4. TESTER LA CORRECTION TEMPORAIRE
print(f"\n4. TEST CORRECTION TEMPORAIRE")
print("=" * 30)

print("Pour tester immediatement, modifiez temporairement:")
print("")
print("Dans settings.py, changez:")
print("  LOGIN_REDIRECT_URL = '/competitions/dashboard/spectator/'")
print("  ACCOUNT_LOGIN_REDIRECT_URL = '/competitions/dashboard/spectator/'")
print("")
print("Cela forcera tous les utilisateurs vers spectator,")
print("mais au moins vous verrez si le probleme vient des settings")

# 5. CREER UN BYPASS TEMPORAIRE
print(f"\n5. CREATION BYPASS TEMPORAIRE")
print("=" * 30)

# Creer une vue de test
bypass_view_content = '''
# Vue de bypass temporaire pour tester le routage coach
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

@login_required
def test_coach_bypass(request):
    """Vue de test pour bypass le middleware"""
    user = request.user
    
    # Verifier le role
    profile = getattr(user, 'profile', None)
    if profile and hasattr(profile, 'role'):
        if profile.role == 'coach':
            # Rediriger directement vers le template coach
            context = {
                'user': user,
                'page_title': 'Dashboard Coach (Bypass)',
                'bypass_active': True
            }
            return render(request, 'competitions/dashboard/coach.html', context)
    
    # Sinon, aller vers spectator
    return redirect('/competitions/dashboard/spectator/')
'''

# Ecrire la vue de bypass
try:
    with open('test_coach_bypass_view.py', 'w', encoding='utf-8') as f:
        f.write(bypass_view_content)
    print("Vue de bypass creee: test_coach_bypass_view.py")
    print("Vous pouvez ajouter cette vue temporairement pour tester")
except Exception as e:
    print(f"Erreur creation bypass: {e}")

print(f"\n" + "=" * 45)
print("RESUME DES PROBLEMES IDENTIFIES:")
print("1. SETTINGS forcent vers onboarding au lieu de dashboard")
print("2. MIDDLEWARE OnboardingRedirectMiddleware intercepte les redirections") 
print("3. URLS dashboard_router mal configurees")
print("4. Redirections linguistiques automatiques")
print("")
print("ACTIONS IMMEDIATES REQUISES:")
print("1. Modifier LOGIN_REDIRECT_URL dans settings.py")
print("2. Modifier ou desactiver temporairement OnboardingRedirectMiddleware")
print("3. Verifier la configuration des URLs dashboard")
print("=" * 45)