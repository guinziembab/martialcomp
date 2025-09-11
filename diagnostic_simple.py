# -*- coding: utf-8 -*-
"""
Diagnostic simple pour le routage coach - sans caracteres speciaux
"""

def diagnostic_simple():
    print("DIAGNOSTIC COMPLET SYSTEME ROUTAGE COACH")
    print("=" * 50)
    
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    # 1. VERIFIER LES UTILISATEURS COACH1 ET COACH2
    print("VERIFICATION UTILISATEURS")
    print("=" * 30)
    
    coaches = []
    for username in ['COACH1', 'COACH2']:
        try:
            coach = User.objects.get(username=username)
            coaches.append(coach)
            
            print(f"\n{username} trouve:")
            print(f"   Email: {coach.email}")
            print(f"   Active: {coach.is_active}")
            print(f"   Type: {type(coach).__name__}")
            
            # Verifier user.role
            if hasattr(coach, 'role'):
                print(f"   User.role: {coach.role}")
            else:
                print("   User.role: AUCUN ATTRIBUT")
            
            # Verifier le profil
            profile = getattr(coach, 'profile', None)
            if profile:
                print(f"   Profile: {profile}")
                if hasattr(profile, 'role'):
                    print(f"   Profile.role: {profile.role}")
                else:
                    print("   Profile.role: AUCUN ATTRIBUT")
            else:
                print("   Profile: AUCUN PROFIL")
                
        except User.DoesNotExist:
            print(f"{username} non trouve")
    
    # 2. CORRIGER LES ROLES
    print(f"\nCORRECTION ROLES COACH")
    print("=" * 25)
    
    for coach in coaches:
        username = coach.username
        print(f"\nCorrection {username}:")
        
        # Forcer user.role
        try:
            coach.role = 'coach'
            coach.save()
            print(f"   user.role = 'coach' - OK")
        except Exception as e:
            print(f"   user.role echec: {e}")
        
        # Forcer profile.role
        profile = getattr(coach, 'profile', None)
        if profile:
            try:
                profile.role = 'coach'
                profile.save()
                print(f"   profile.role = 'coach' - OK")
            except Exception as e:
                print(f"   profile.role echec: {e}")
        else:
            print("   Pas de profil a corriger")
    
    # 3. TESTER LE DASHBOARD ROUTER
    print(f"\nTEST DASHBOARD ROUTER")
    print("=" * 25)
    
    try:
        from competitions.views.dashboard_router import dashboard_router
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        for coach in coaches:
            print(f"\nTest routage {coach.username}:")
            
            request = factory.get('/competitions/dashboard/')
            request.user = coach
            
            # CECI DEVRAIT AFFICHER LES MESSAGES DE DEBUG
            response = dashboard_router(request)
            
            if hasattr(response, 'url'):
                url = response.url
                print(f"   Redirection: {url}")
                
                if '/coach/' in url:
                    print("   SUCCESS - Dirige vers coach")
                elif '/spectator/' in url:
                    print("   PROBLEME - Dirige vers spectator")
                else:
                    print(f"   Dirige vers: {url}")
            else:
                print(f"   Pas de redirection: {type(response)}")
                
    except ImportError as e:
        print(f"Impossible d'importer dashboard_router: {e}")
    except Exception as e:
        print(f"Erreur test router: {e}")
    
    # 4. TESTER AVEC CLIENT HTTP
    print(f"\nTEST CLIENT HTTP")
    print("=" * 20)
    
    try:
        from django.test import Client
        
        client = Client()
        
        for coach in coaches:
            print(f"\nTest HTTP {coach.username}:")
            
            client.force_login(coach)
            
            # Test dashboard general
            response = client.get('/competitions/dashboard/', follow=False)
            
            if response.status_code == 302:
                redirect_url = response.url
                print(f"   /competitions/dashboard/ -> REDIRECT: {redirect_url}")
                
                if '/coach/' in redirect_url:
                    print("   SUCCESS - Redirige vers coach")
                elif '/spectator/' in redirect_url:
                    print("   PROBLEME - Redirige vers spectator")
            else:
                print(f"   /competitions/dashboard/ -> {response.status_code}")
            
            # Test URL coach directe  
            response = client.get('/competitions/dashboard/coach/', follow=False)
            print(f"   /competitions/dashboard/coach/ -> {response.status_code}")
    
    except Exception as e:
        print(f"Erreur test client: {e}")
    
    # 5. VERIFIER SETTINGS
    print(f"\nSETTINGS LOGIN")
    print("=" * 15)
    
    from django.conf import settings
    
    login_settings = [
        'LOGIN_REDIRECT_URL',
        'ACCOUNT_LOGIN_REDIRECT_URL',
        'LOGOUT_REDIRECT_URL'
    ]
    
    for setting in login_settings:
        value = getattr(settings, setting, 'NON DEFINI')
        print(f"   {setting}: {value}")
        
        if value and 'spectator' in str(value):
            print(f"     PROBLEME POTENTIEL - Redirection vers spectator!")

if __name__ == "__main__":
    diagnostic_simple()

# Executer automatiquement
diagnostic_simple()