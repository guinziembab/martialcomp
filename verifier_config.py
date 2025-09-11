# -*- coding: utf-8 -*-
"""
Verifier la configuration URLs et middlewares
"""

print("VERIFICATION CONFIGURATION URLS")
print("=" * 35)

from django.conf import settings

# 1. Verifier les settings de redirection
print("SETTINGS REDIRECTION:")
login_settings = [
    'LOGIN_URL',
    'LOGIN_REDIRECT_URL',
    'LOGOUT_REDIRECT_URL',
    'ACCOUNT_LOGIN_REDIRECT_URL',
    'ACCOUNT_LOGOUT_REDIRECT_URL'
]

for setting in login_settings:
    value = getattr(settings, setting, 'NON DEFINI')
    print(f"  {setting}: {value}")
    
    if value and 'spectator' in str(value):
        print(f"    PROBLEME - Redirection forcee vers spectator!")

print("\n" + "=" * 35)

# 2. Verifier les middlewares
middlewares = getattr(settings, 'MIDDLEWARE', [])
print("MIDDLEWARES:")
for i, middleware in enumerate(middlewares):
    print(f"  {i+1}. {middleware}")
    
    if 'redirect' in middleware.lower() or 'onboarding' in middleware.lower():
        print(f"     ATTENTION - Middleware de redirection")

print("\n" + "=" * 35)

# 3. Tester les URLs
try:
    from django.urls import reverse, NoReverseMatch
    
    print("TEST URLS:")
    urls_to_test = [
        'competitions:dashboard_router',
        'competitions:dashboard',
        'dashboard_router',
        'dashboard'
    ]
    
    for url_name in urls_to_test:
        try:
            url = reverse(url_name)
            print(f"  {url_name} -> {url}")
        except NoReverseMatch:
            print(f"  {url_name} -> NON TROUVEE")
            
except Exception as e:
    print(f"Erreur test URLs: {e}")

print("\n" + "=" * 35)

# 4. Analyser le fichier URLs competitions
import os

urls_files = [
    'apps/competitions/urls.py',
    'competitions/urls.py'
]

for urls_file in urls_files:
    if os.path.exists(urls_file):
        print(f"ANALYSE {urls_file}:")
        
        with open(urls_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'dashboard_router' in content:
            print("  dashboard_router trouve dans le fichier")
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'dashboard_router' in line:
                    print(f"    Ligne {i+1}: {line.strip()}")
        else:
            print("  dashboard_router NON trouve dans le fichier")
            
        # Chercher patterns dashboard
        lines = content.split('\n')
        dashboard_patterns = []
        for i, line in enumerate(lines):
            if 'dashboard' in line.lower() and ('path(' in line or 'url(' in line):
                dashboard_patterns.append(f"    Ligne {i+1}: {line.strip()}")
        
        if dashboard_patterns:
            print("  Patterns dashboard:")
            for pattern in dashboard_patterns:
                print(pattern)

print("\n" + "=" * 35)
print("VERIFICATION TERMINEE")
print("Analysez les resultats ci-dessus")