#!/usr/bin/env python
"""
Script pour reproduire l'erreur SQL en utilisant les mêmes conditions que le navigateur.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.db import connection
from django.conf import settings

def reproduce_browser_request():
    """Reproduire exactement la requête du navigateur."""
    print("🌐 REPRODUCTION DE LA REQUÊTE NAVIGATEUR")
    print("=" * 60)
    
    try:
        # Activer le debug SQL
        settings.DEBUG = True
        connection.force_debug_cursor = True
        
        # Client de test avec tous les middlewares
        client = Client()
        
        # Récupérer un utilisateur
        user = User.objects.get(username='parent_demo_628317')
        print(f"✅ Utilisateur trouvé: {user.username}")
        
        # Se connecter
        login_success = client.login(username='parent_demo_628317', password='demo123')
        print(f"✅ Connexion: {'Réussie' if login_success else 'Échouée'}")
        
        if not login_success:
            # Force login en cas d'échec
            client.force_login(user)
            print("✅ Force login réussi")
        
        # Vider les requêtes précédentes
        connection.queries.clear()
        
        print("\n🔍 Requête GET /families/ avec tous les middlewares...")
        
        # Faire la requête exacte du navigateur
        response = client.get(
            '/families/',
            HTTP_HOST='127.0.0.1:8001',
            HTTP_USER_AGENT='Mozilla/5.0 Test',
            follow=True
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Requête réussie!")
            print(f"📝 Contenu: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ ERREUR: Status {response.status_code}")
            print(f"📝 Contenu: {response.content[:300]}...")
            
            # Afficher les dernières requêtes SQL
            print("\n📋 Dernières requêtes SQL:")
            for i, query in enumerate(connection.queries[-10:], 1):
                print(f"  {i:2d}. {query['sql'][:100]}...")
                if 'SET' in query['sql']:
                    print(f"      ⚠️  REQUÊTE SUSPECTE: {query['sql']}")
            
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        print(f"Type: {type(e).__name__}")
        
        # Afficher les requêtes SQL en cas d'erreur
        print("\n📋 Requêtes SQL avant l'erreur:")
        for i, query in enumerate(connection.queries[-10:], 1):
            print(f"  {i:2d}. {query['sql'][:100]}...")
            if 'SET' in query['sql']:
                print(f"      🔥 REQUÊTE PROBLÉMATIQUE: {query['sql']}")
        
        import traceback
        traceback.print_exc()
        return False

def test_direct_view_call():
    """Test direct de la vue sans middlewares."""
    print("\n🎯 TEST DIRECT DE LA VUE (SANS MIDDLEWARES)")
    print("=" * 60)
    
    try:
        from django.test import RequestFactory
        from family_management.views import family_dashboard
        
        # Créer une requête factice
        factory = RequestFactory()
        request = factory.get('/families/')
        
        # Ajouter l'utilisateur
        user = User.objects.get(username='parent_demo_628317')
        request.user = user
        
        # Vider les requêtes
        connection.queries.clear()
        
        print("🔍 Appel direct family_dashboard(request)...")
        response = family_dashboard(request)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Vue directe réussie!")
            return True
        else:
            print(f"❌ ERREUR: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION dans vue directe: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_middlewares_imports():
    """Vérifier si les middlewares s'importent correctement."""
    print("\n🔧 VÉRIFICATION DES IMPORTS MIDDLEWARES")
    print("=" * 60)
    
    middlewares_to_test = [
        'security.middleware.SecurityMiddleware',
        'security.rate_limiting.RateLimitingMiddleware',
        'competitions.utils.security.OrganizationIsolationMiddleware',
        'multitenant.middleware.TenantMiddleware',
        'multitenant.cache.TenantCacheMiddleware',
        'multitenant.resource_limits.ResourceTrackerMiddleware',
        'multitenant.middleware.FeatureAccessMiddleware',
    ]
    
    problematic_middlewares = []
    
    for middleware in middlewares_to_test:
        try:
            module_path = '.'.join(middleware.split('.')[:-1])
            class_name = middleware.split('.')[-1]
            
            module = __import__(module_path, fromlist=[class_name])
            middleware_class = getattr(module, class_name)
            print(f"✅ {middleware}")
            
        except Exception as e:
            print(f"❌ {middleware}: {e}")
            problematic_middlewares.append((middleware, str(e)))
    
    return problematic_middlewares

if __name__ == "__main__":
    print("🔧 REPRODUCTION DE L'ERREUR SQL 'near SET'")
    print("=" * 60)
    
    # Vérifier les imports de middlewares
    problematic = check_middlewares_imports()
    
    # Test direct de la vue
    direct_success = test_direct_view_call()
    
    # Test avec tous les middlewares (comme le navigateur)
    browser_success = reproduce_browser_request()
    
    print("\n" + "=" * 60)
    print("📊 RÉSULTATS FINAUX:")
    print("=" * 60)
    print(f"Vue directe (sans middlewares): {'✅ RÉUSSI' if direct_success else '❌ ÉCHEC'}")
    print(f"Vue avec middlewares (navigateur): {'✅ RÉUSSI' if browser_success else '❌ ÉCHEC'}")
    
    if problematic:
        print(f"\nMiddlewares problématiques ({len(problematic)}):")
        for middleware, error in problematic:
            print(f"  ❌ {middleware}: {error}")
    
    if direct_success and not browser_success:
        print("\n🎯 CONCLUSION: L'erreur SQL vient d'un middleware")
        print("   Vérifiez les middlewares problématiques listés ci-dessus")
    elif not direct_success:
        print("\n🎯 CONCLUSION: L'erreur SQL vient de la vue elle-même")
    else:
        print("\n🎯 CONCLUSION: Aucune erreur détectée dans cet environnement")
    
    print("=" * 60)