#!/usr/bin/env python3
"""
Vérifier la configuration des URLs pour comprendre le routage
À exécuter avec: python manage.py shell
"""

def verifier_urls_routage():
    """Vérifier toute la configuration de routage"""
    
    print("🔗 VÉRIFICATION COMPLÈTE ROUTAGE URLS")
    print("=" * 40)
    
    # 1. VÉRIFIER LA CONFIGURATION PRINCIPALE DES URLS
    print("📋 CONFIGURATION URLS PRINCIPALE")
    print("=" * 30)
    
    from django.conf import settings
    from django.urls import get_resolver
    
    try:
        resolver = get_resolver()
        print(f"✅ URL Resolver: {resolver}")
        print(f"   URL Conf: {settings.ROOT_URLCONF}")
        
        # Chercher les patterns liés au dashboard
        def find_dashboard_patterns(patterns, prefix=""):
            dashboard_patterns = []
            for pattern in patterns:
                try:
                    if hasattr(pattern, 'pattern'):
                        pattern_str = str(pattern.pattern)
                        if 'dashboard' in pattern_str.lower():
                            dashboard_patterns.append(f"{prefix}{pattern_str}")
                    
                    # Si c'est un include, explorer récursivement
                    if hasattr(pattern, 'url_patterns'):
                        sub_patterns = find_dashboard_patterns(
                            pattern.url_patterns, 
                            prefix + str(pattern.pattern)
                        )
                        dashboard_patterns.extend(sub_patterns)
                        
                except Exception as e:
                    continue
                    
            return dashboard_patterns
        
        dashboard_urls = find_dashboard_patterns(resolver.url_patterns)
        
        print(f"\n🔍 URLs Dashboard trouvées:")
        for url in dashboard_urls:
            print(f"   • {url}")
            
    except Exception as e:
        print(f"❌ Erreur analyse URLs: {e}")
    
    # 2. VÉRIFIER SPÉCIFIQUEMENT LES URLS COMPETITIONS
    print(f"\n🏆 URLS COMPETITIONS")
    print("=" * 20)
    
    try:
        from django.urls import reverse, NoReverseMatch
        
        # Tester les URLs de dashboard
        dashboard_urls_to_test = [
            'competitions:dashboard_router',
            'competitions:dashboard',
            'dashboard_router',
            'dashboard',
            'competitions:coach_dashboard',
            'competitions:coach',
        ]
        
        for url_name in dashboard_urls_to_test:
            try:
                url = reverse(url_name)
                print(f"   ✅ {url_name} → {url}")
            except NoReverseMatch:
                print(f"   ❌ {url_name} → Non trouvée")
                
    except Exception as e:
        print(f"❌ Erreur test reverse URLs: {e}")
    
    # 3. ANALYSER LE FICHIER URLS COMPETITIONS
    print(f"\n📄 ANALYSE FICHIER URLS COMPETITIONS")
    print("=" * 35)
    
    import os
    urls_files = [
        'apps/competitions/urls.py',
        'competitions/urls.py',
        'apps/competitions/urls/__init__.py'
    ]
    
    for urls_file in urls_files:
        if os.path.exists(urls_file):
            print(f"\n✅ Fichier trouvé: {urls_file}")
            
            with open(urls_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Chercher les références au dashboard_router
            if 'dashboard_router' in content:
                print(f"   ✅ 'dashboard_router' trouvé dans le fichier")
                
                # Extraire les lignes contenant dashboard_router
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'dashboard_router' in line:
                        print(f"   Ligne {i+1}: {line.strip()}")
            else:
                print(f"   ❌ 'dashboard_router' NON trouvé dans le fichier")
            
            # Chercher les patterns de dashboard
            dashboard_lines = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'dashboard' in line.lower() and ('path(' in line or 'url(' in line):
                    dashboard_lines.append(f"   Ligne {i+1}: {line.strip()}")
            
            if dashboard_lines:
                print(f"   📋 Patterns dashboard:")
                for line in dashboard_lines:
                    print(line)
    
    # 4. VÉRIFIER LES MIDDLEWARES QUI POURRAIENT INTERFÉRER
    print(f"\n⚙️ VÉRIFICATION MIDDLEWARES")
    print("=" * 25)
    
    middlewares = getattr(settings, 'MIDDLEWARE', [])
    print(f"Middlewares configurés:")
    for i, middleware in enumerate(middlewares):
        print(f"   {i+1}. {middleware}")
        
        # Vérifier si c'est un middleware personnalisé qui pourrait rediriger
        if 'competitions' in middleware or 'redirect' in middleware.lower():
            print(f"      ⚠️ Middleware potentiellement problématique")
    
    # 5. TESTER LE ROUTAGE DIRECT
    print(f"\n🧪 TEST ROUTAGE DIRECT")
    print("=" * 20)
    
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        client = Client()
        
        # Tester avec COACH1 ou COACH2
        coaches = []
        for username in ['COACH1', 'COACH2']:
            try:
                coach = User.objects.get(username=username)
                coaches.append(coach)
            except User.DoesNotExist:
                continue
        
        for coach in coaches:
            print(f"\n🔍 Test avec {coach.username}:")
            
            # Se connecter
            client.force_login(coach)
            
            # Tester différentes URLs
            test_urls = [
                '/competitions/dashboard/',
                '/dashboard/',
                '/competitions/dashboard/coach/',
            ]
            
            for test_url in test_urls:
                try:
                    response = client.get(test_url, follow=False)
                    
                    if response.status_code == 302:
                        redirect_url = response.url
                        print(f"   {test_url} → REDIRECT: {redirect_url}")
                    elif response.status_code == 200:
                        print(f"   {test_url} → OK (200)")
                    else:
                        print(f"   {test_url} → {response.status_code}")
                        
                except Exception as e:
                    print(f"   {test_url} → ERREUR: {e}")
    
    except Exception as e:
        print(f"❌ Erreur test client: {e}")
    
    # 6. VÉRIFIER LES SETTINGS LOGIN
    print(f"\n🔐 SETTINGS LOGIN/REDIRECT")
    print("=" * 25)
    
    login_settings = [
        'LOGIN_URL',
        'LOGIN_REDIRECT_URL', 
        'LOGOUT_URL',
        'LOGOUT_REDIRECT_URL',
    ]
    
    # Vérifier aussi django-allauth si installé
    allauth_settings = [
        'ACCOUNT_LOGIN_REDIRECT_URL',
        'ACCOUNT_LOGOUT_REDIRECT_URL',
        'ACCOUNT_SIGNUP_REDIRECT_URL',
    ]
    
    all_settings = login_settings + allauth_settings
    
    for setting in all_settings:
        value = getattr(settings, setting, 'NON DÉFINI')
        print(f"   • {setting}: {value}")
        
        if value and isinstance(value, str) and 'spectator' in value:
            print(f"     ⚠️ PROBLÈME POTENTIEL: Redirection vers spectator!")

if __name__ == "__main__":
    verifier_urls_routage()
    
    print(f"\n" + "=" * 40)
    print("🎯 VÉRIFICATION URLS TERMINÉE")
    print("Analysez les résultats pour identifier le problème de routage.")
    print("=" * 40)

# Exécuter automatiquement
verifier_urls_routage()