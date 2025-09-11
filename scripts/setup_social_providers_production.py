#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/mnt/c/martial_hub_django/martialcomp')

# Set up Django with PostgreSQL settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Override database settings for production PostgreSQL
from django.conf import settings
if not settings.configured:
    django.setup()

# Import after Django setup
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction, connection

def setup_social_providers_production():
    """Créer les applications sociales pour PostgreSQL en production."""
    
    print("🚀 Configuration des fournisseurs sociaux pour MartialComp (PostgreSQL Production)")
    print("=" * 80)
    
    # Vérifier la connexion à la base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            print(f"📊 Base de données: {db_info[0]}")
            print(f"👤 Utilisateur: {db_info[1]}")
    except Exception as e:
        print(f"❌ Erreur de connexion à PostgreSQL: {e}")
        return False
    
    try:
        with transaction.atomic():
            # Get or create the site object
            try:
                site = Site.objects.get(id=1)
                print(f"✅ Site trouvé: {site.domain} - {site.name}")
            except Site.DoesNotExist:
                site = Site.objects.create(
                    id=1,
                    domain='martialcomp.com',
                    name='MartialComp'
                )
                print(f"✅ Site créé: {site.domain} - {site.name}")
            
            # Vérifier que les tables allauth existent
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE '%socialaccount%';
                """)
                tables = cursor.fetchall()
                print(f"📊 Tables socialaccount trouvées: {len(tables)}")
                for table in tables:
                    print(f"   - {table[0]}")
            
            # Supprimer les applications existantes si elles existent
            existing_apps = SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple'])
            if existing_apps.exists():
                print(f"🔄 Suppression de {existing_apps.count()} applications existantes...")
                existing_apps.delete()
            
            # Configuration Google OAuth2
            print("\n📱 Configuration Google OAuth2...")
            google_app = SocialApp.objects.create(
                provider='google',
                name='Google OAuth2',
                client_id='YOUR_GOOGLE_CLIENT_ID_HERE',  # À remplacer
                secret='YOUR_GOOGLE_CLIENT_SECRET_HERE'   # À remplacer
            )
            google_app.sites.add(site)
            print(f"✅ Application Google créée (ID: {google_app.id})")
            
            # Configuration Facebook Login
            print("\n📘 Configuration Facebook Login...")
            facebook_app = SocialApp.objects.create(
                provider='facebook',
                name='Facebook Login',
                client_id='YOUR_FACEBOOK_APP_ID_HERE',    # À remplacer
                secret='YOUR_FACEBOOK_APP_SECRET_HERE'   # À remplacer
            )
            facebook_app.sites.add(site)
            print(f"✅ Application Facebook créée (ID: {facebook_app.id})")
            
            # Configuration Apple Sign In
            print("\n🍎 Configuration Apple Sign In...")
            apple_app = SocialApp.objects.create(
                provider='apple',
                name='Sign in with Apple',
                client_id='YOUR_APPLE_SERVICES_ID_HERE',  # À remplacer
                secret='YOUR_APPLE_PRIVATE_KEY_HERE'      # À remplacer
            )
            apple_app.sites.add(site)
            print(f"✅ Application Apple créée (ID: {apple_app.id})")
            
            print("\n" + "=" * 80)
            print("🎉 Configuration des fournisseurs sociaux terminée !")
            print("\n📋 Résumé des applications créées:")
            
            # Afficher un résumé
            for app in SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple']):
                print(f"   ✅ {app.name} ({app.provider}) - ID: {app.id}")
                print(f"      Client ID: {app.client_id}")
                print(f"      Sites associés: {[s.domain for s in app.sites.all()]}")
                print()
            
            print("🔗 URLs de redirection à configurer dans les consoles développeur:")
            print("   📱 Google: https://martialcomp.com/accounts/google/login/callback/")
            print("   📘 Facebook: https://martialcomp.com/accounts/facebook/login/callback/")
            print("   🍎 Apple: https://martialcomp.com/accounts/apple/login/callback/")
            print()
            
            print("🔄 Prochaines étapes:")
            print("   1. Configurer les consoles développeur avec ces URLs")
            print("   2. Récupérer les vraies clés API")
            print("   3. Mettre à jour les applications avec update_social_keys_production.py")
            print("   4. Tester sur https://martialcomp.com/accounts/login/")
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = setup_social_providers_production()
    if success:
        print("\n✅ Configuration terminée avec succès !")
    else:
        print("\n❌ Échec de la configuration.")
        sys.exit(1)