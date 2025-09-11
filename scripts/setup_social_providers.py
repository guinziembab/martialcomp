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

def setup_social_providers():
    """Créer les applications sociales pour Google, Facebook et Apple."""
    
    print("🚀 Configuration des fournisseurs sociaux pour MartialComp...")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Get the site object
            site = Site.objects.get(id=1)
            print(f"✅ Site trouvé: {site.domain} - {site.name}")
            
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
                client_id='GOOGLE_CLIENT_ID_PLACEHOLDER',  # À remplacer par la vraie clé
                secret='GOOGLE_CLIENT_SECRET_PLACEHOLDER'   # À remplacer par le vrai secret
            )
            google_app.sites.add(site)
            print(f"✅ Application Google créée (ID: {google_app.id})")
            
            # Configuration Facebook Login
            print("\n📘 Configuration Facebook Login...")
            facebook_app = SocialApp.objects.create(
                provider='facebook',
                name='Facebook Login',
                client_id='FACEBOOK_APP_ID_PLACEHOLDER',    # À remplacer par la vraie clé
                secret='FACEBOOK_APP_SECRET_PLACEHOLDER'   # À remplacer par le vrai secret
            )
            facebook_app.sites.add(site)
            print(f"✅ Application Facebook créée (ID: {facebook_app.id})")
            
            # Configuration Apple Sign In
            print("\n🍎 Configuration Apple Sign In...")
            apple_app = SocialApp.objects.create(
                provider='apple',
                name='Sign in with Apple',
                client_id='APPLE_SERVICES_ID_PLACEHOLDER',  # À remplacer par la vraie clé
                secret='APPLE_PRIVATE_KEY_PLACEHOLDER',     # À remplacer par la vraie clé privée
                # Pour Apple, on peut aussi ajouter des settings supplémentaires
                settings={
                    'certificate_id': 'APPLE_CERTIFICATE_ID_PLACEHOLDER',
                    'app_id': 'APPLE_APP_ID_PLACEHOLDER'
                }
            )
            apple_app.sites.add(site)
            print(f"✅ Application Apple créée (ID: {apple_app.id})")
            
            print("\n" + "=" * 60)
            print("🎉 Configuration des fournisseurs sociaux terminée !")
            print("\n📋 Résumé des applications créées:")
            
            # Afficher un résumé
            for app in SocialApp.objects.filter(provider__in=['google', 'facebook', 'apple']):
                print(f"   ✅ {app.name} ({app.provider}) - ID: {app.id}")
                print(f"      Client ID: {app.client_id}")
                print(f"      Sites associés: {[s.domain for s in app.sites.all()]}")
                print()
            
            print("🔄 Prochaines étapes:")
            print("   1. Configurer les consoles développeur:")
            print("      - Google: https://console.cloud.google.com/")
            print("      - Facebook: https://developers.facebook.com/")
            print("      - Apple: https://developer.apple.com/")
            print()
            print("   2. Mettre à jour les clés API:")
            print("      - Modifier les applications dans Django Admin")
            print("      - Ou utiliser le script update_social_keys.py")
            print()
            print("   3. Configurer les URLs de redirection:")
            print("      - Google: https://martialcomp.com/accounts/google/login/callback/")
            print("      - Facebook: https://martialcomp.com/accounts/facebook/login/callback/")
            print("      - Apple: https://martialcomp.com/accounts/apple/login/callback/")
            print()
            print("   4. Tester l'authentification sur:")
            print("      - https://martialcomp.com/accounts/login/")
            
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        return False
    
    return True

if __name__ == "__main__":
    success = setup_social_providers()
    if success:
        print("\n✅ Configuration terminée avec succès !")
    else:
        print("\n❌ Échec de la configuration.")
        sys.exit(1)