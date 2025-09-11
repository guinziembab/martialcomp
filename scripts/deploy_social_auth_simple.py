#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/mnt/c/martial_hub_django/martialcomp')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.db import transaction
from django.core.management import call_command

def deploy_social_auth():
    """Déployer l'authentification sociale (fonctionne avec SQLite ou PostgreSQL)."""
    
    print("🚀 Déploiement de l'authentification sociale pour MartialComp")
    print("=" * 65)
    
    # Étape 1: Vérifier et créer les tables manquantes
    print("📊 Étape 1: Vérification des migrations...")
    try:
        # Vérifier si les tables existent
        from django.db import connection
        cursor = connection.cursor()
        
        # Essayer d'accéder aux tables allauth
        try:
            cursor.execute("SELECT COUNT(*) FROM django_site")
            site_count = cursor.fetchone()[0]
            print(f"✅ Table django_site trouvée ({site_count} sites)")
        except:
            print("⚠️  Table django_site manquante - exécution des migrations...")
            call_command('migrate', verbosity=0)
            print("✅ Migrations exécutées")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM socialaccount_socialapp")
            app_count = cursor.fetchone()[0]
            print(f"✅ Table socialaccount_socialapp trouvée ({app_count} apps)")
        except:
            print("⚠️  Tables allauth manquantes - exécution des migrations allauth...")
            call_command('migrate', 'account', verbosity=0)
            call_command('migrate', 'socialaccount', verbosity=0)
            print("✅ Migrations allauth exécutées")
            
    except Exception as e:
        print(f"❌ Erreur lors des migrations: {e}")
        return False
    
    # Étape 2: Configuration du site
    print("\n🌐 Étape 2: Configuration du site...")
    try:
        with transaction.atomic():
            site, created = Site.objects.get_or_create(
                id=1,
                defaults={'domain': 'martialcomp.com', 'name': 'MartialComp'}
            )
            if not created and site.domain != 'martialcomp.com':
                site.domain = 'martialcomp.com'
                site.name = 'MartialComp'
                site.save()
                print("✅ Site mis à jour: martialcomp.com")
            else:
                print(f"✅ Site configuré: {site.domain} ({'créé' if created else 'existant'})")
    except Exception as e:
        print(f"❌ Erreur lors de la configuration du site: {e}")
        return False
    
    # Étape 3: Configuration des fournisseurs sociaux
    print("\n📱 Étape 3: Configuration des fournisseurs sociaux...")
    try:
        with transaction.atomic():
            # Supprimer les anciennes applications
            deleted_count = SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple']).count()
            if deleted_count > 0:
                SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple']).delete()
                print(f"🔄 {deleted_count} anciennes applications supprimées")
            
            # Créer les nouvelles applications
            providers_config = [
                {
                    'provider': 'google',
                    'name': 'Google OAuth2',
                    'client_id': 'YOUR_GOOGLE_CLIENT_ID_REPLACE_ME',
                    'secret': 'YOUR_GOOGLE_CLIENT_SECRET_REPLACE_ME'
                },
                {
                    'provider': 'facebook',
                    'name': 'Facebook Login',
                    'client_id': 'YOUR_FACEBOOK_APP_ID_REPLACE_ME',
                    'secret': 'YOUR_FACEBOOK_APP_SECRET_REPLACE_ME'
                },
                {
                    'provider': 'apple',
                    'name': 'Sign in with Apple',
                    'client_id': 'YOUR_APPLE_SERVICES_ID_REPLACE_ME',
                    'secret': 'YOUR_APPLE_PRIVATE_KEY_REPLACE_ME'
                }
            ]
            
            for config in providers_config:
                app = SocialApp.objects.create(**config)
                app.sites.add(site)
                print(f"✅ {config['name']} créé (ID: {app.id})")
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration des fournisseurs: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Étape 4: Vérification finale
    print("\n🔍 Étape 4: Vérification finale...")
    try:
        apps = SocialApp.objects.all()
        print(f"📊 Total des applications sociales: {apps.count()}")
        for app in apps:
            configured = "🔐 Configuré" if not app.client_id.startswith('YOUR_') else "⚠️  À configurer"
            print(f"   {configured} {app.name} ({app.provider})")
            
        print("\n🔗 URLs de redirection pour les consoles développeur:")
        base_url = "https://martialcomp.com"
        for app in apps:
            callback_url = f"{base_url}/accounts/{app.provider}/login/callback/"
            print(f"   {app.provider.title()}: {callback_url}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False
    
    print("\n" + "=" * 65)
    print("🎉 Déploiement de l'authentification sociale terminé avec succès !")
    print("\n📋 RÉSUMÉ:")
    print("   ✅ Tables allauth créées/vérifiées")
    print("   ✅ Site configuré (martialcomp.com)")
    print("   ✅ Applications sociales créées")
    print("   ✅ URLs d'authentification prêtes")
    
    print("\n🔄 PROCHAINES ÉTAPES:")
    print("\n1. 🔐 Configurer les consoles développeur:")
    print("   📱 Google: https://console.cloud.google.com/")
    print("      - Créer identifiants OAuth 2.0")
    print("      - URL de redirection: https://martialcomp.com/accounts/google/login/callback/")
    print("\n   📘 Facebook: https://developers.facebook.com/")
    print("      - Créer une app Facebook")
    print("      - URL de redirection: https://martialcomp.com/accounts/facebook/login/callback/")
    print("\n   🍎 Apple: https://developer.apple.com/")
    print("      - Créer un Services ID")
    print("      - URL de redirection: https://martialcomp.com/accounts/apple/login/callback/")
    
    print("\n2. 🔑 Mettre à jour les clés API:")
    print("   - Aller sur https://martialcomp.com/admin/")
    print("   - Section 'Social Applications'")
    print("   - Modifier chaque application pour ajouter les vraies clés")
    
    print("\n3. 🌐 Tester l'authentification:")
    print("   - https://martialcomp.com/accounts/login/")
    print("   - https://martialcomp.com/accounts/signup/")
    
    print("\n💡 POUR BASCULER VERS POSTGRESQL EN PRODUCTION:")
    print("   1. Modifier config/settings.py:")
    print("      - Décommenter la section PostgreSQL")
    print("      - Commenter la section SQLite")
    print("   2. Installer: sudo apt install python3-psycopg2")
    print("   3. Exécuter: python3 manage.py migrate")
    print("   4. Réexécuter ce script: python3 deploy_social_auth_simple.py")
    
    return True

if __name__ == "__main__":
    success = deploy_social_auth()
    if not success:
        print("\n❌ Échec du déploiement.")
        sys.exit(1)
    else:
        print("\n✅ Déploiement réussi !")