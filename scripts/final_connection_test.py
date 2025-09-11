#!/usr/bin/env python3
"""
Test final de connexion avec simulation complète
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_fixed')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import requests

def test_browser_simulation():
    """Simule exactement ce que fait le navigateur"""
    print("🌐 SIMULATION NAVIGATEUR COMPLÈTE")
    print("=" * 60)
    
    # Test avec les deux utilisateurs
    test_users = [
        ('admin', 'admin123'),
        ('guinziembab', 'zBx43V22')
    ]
    
    for username, password in test_users:
        print(f"\n👤 Test avec {username}")
        print("-" * 30)
        
        # 1. Créer une session client Django
        client = Client()
        
        # 2. D'abord GET de la page de login pour récupérer CSRF
        print("   1. GET /admin/login/")
        response = client.get('/admin/login/')
        print(f"      Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"      ❌ Page de login inaccessible")
            continue
            
        # 3. Extraire CSRF token
        csrf_token = None
        if hasattr(response, 'context') and response.context:
            csrf_token = response.context.get('csrf_token')
        
        if not csrf_token:
            # Essayer d'extraire du contenu HTML
            content = response.content.decode('utf-8')
            if 'csrfmiddlewaretoken' in content:
                import re
                match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', content)
                if match:
                    csrf_token = match.group(1)
        
        print(f"      CSRF token: {'Found' if csrf_token else 'NOT FOUND'}")
        
        # 4. POST avec les données de connexion
        print("   2. POST /admin/login/")
        login_data = {
            'username': username,
            'password': password,
            'next': '/admin/',
        }
        
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        response = client.post('/admin/login/', login_data, follow=True)
        print(f"      Status: {response.status_code}")
        print(f"      Final URL: {response.request.get('PATH_INFO', 'Unknown')}")
        
        # 5. Vérifier si connecté
        if response.status_code == 200 and '/admin/' in response.request.get('PATH_INFO', ''):
            print("      ✅ CONNEXION RÉUSSIE!")
            
            # 6. Test d'accès à Rosetta
            print("   3. Test Rosetta")
            rosetta_response = client.get('/rosetta/')
            print(f"      Rosetta status: {rosetta_response.status_code}")
            
            if rosetta_response.status_code == 200:
                print("      ✅ ROSETTA ACCESSIBLE!")
                return True
            else:
                print(f"      ⚠️ Rosetta redirect: {rosetta_response.get('Location', 'Unknown')}")
                
        else:
            print("      ❌ Connexion échouée")
            # Afficher le contenu pour debug
            content = response.content.decode('utf-8')
            if 'errorlist' in content:
                print("      ❌ Erreurs dans le formulaire détectées")
            if 'Veuillez compléter correctement' in content:
                print("      ❌ Message d'erreur: identifiants incorrects")
    
    return False

def test_with_requests():
    """Test avec requests (plus proche du navigateur)"""
    print("\n🔗 TEST AVEC REQUESTS (simulation navigateur)")
    print("=" * 60)
    
    session = requests.Session()
    
    try:
        # 1. GET page de login
        response = session.get('http://localhost:8000/admin/login/')
        print(f"GET login page: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ Serveur inaccessible avec requests")
            return False
            
        # 2. Extraire CSRF
        import re
        csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.text)
        if not csrf_match:
            print("❌ CSRF token non trouvé")
            return False
            
        csrf_token = csrf_match.group(1)
        print(f"CSRF token: {csrf_token[:20]}...")
        
        # 3. POST login
        login_data = {
            'username': 'admin',
            'password': 'admin123',
            'csrfmiddlewaretoken': csrf_token,
            'next': '/admin/'
        }
        
        response = session.post('http://localhost:8000/admin/login/', data=login_data)
        print(f"POST login: {response.status_code}")
        print(f"Final URL: {response.url}")
        
        if 'admin' in response.url and response.status_code == 200:
            print("✅ CONNEXION RÉUSSIE avec requests!")
            return True
        else:
            print("❌ Connexion échouée avec requests")
            print(f"Response text preview: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Serveur non accessible - Vérifiez que runserver est lancé")
        return False
    
    return False

def main():
    print("TEST FINAL DE CONNEXION")
    print("=" * 60)
    
    # Test 1: Simulation Django
    success1 = test_browser_simulation()
    
    # Test 2: Simulation requests
    success2 = test_with_requests()
    
    print(f"\n📊 RÉSULTATS:")
    print(f"Test Django Client: {'✅ SUCCÈS' if success1 else '❌ ÉCHEC'}")
    print(f"Test Requests: {'✅ SUCCÈS' if success2 else '❌ ÉCHEC'}")
    
    if success1 and not success2:
        print("\n🔍 DIAGNOSTIC:")
        print("Django fonctionne mais pas le serveur HTTP")
        print("SOLUTION: Vérifiez que le serveur tourne:")
        print("python manage.py runserver 8000 --settings=config.settings_fixed")
    
    elif not success1 and not success2:
        print("\n🔍 DIAGNOSTIC:")
        print("Problème avec Django lui-même")
        print("SOLUTION: Vérifiez la configuration")
    
    elif success1 and success2:
        print("\n🎉 TOUT FONCTIONNE!")
        print("Le problème vient du navigateur:")
        print("• Videz complètement le cache")
        print("• Essayez un autre navigateur")
        print("• Navigation privée")
        print("• Vérifiez les cookies")
    
    print(f"\n🔐 IDENTIFIANTS À UTILISER:")
    print(f"Username: admin")
    print(f"Password: admin123")
    print(f"URL: http://localhost:8000/admin/login/")

if __name__ == '__main__':
    main()