#!/usr/bin/env python3
"""
Configuration des applications sociales pour MartialComp
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

def configure_social_apps():
    """Configure Google and Facebook social authentication"""
    try:
        print("🔄 Configuration des applications sociales...")
        
        # Supprimer les applications existantes
        SocialApp.objects.all().delete()
        print("✅ Anciennes applications supprimées")
        
        # Récupérer le site actuel
        site = Site.objects.get_current()
        print(f"✅ Site actuel: {site.domain}")
        
        # Configurer Google OAuth
        google_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id='243898642746-6tjnpdflrrsetgif0fne7pgs4v66j6j5.apps.googleusercontent.com',
            secret='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'
        )
        google_app.sites.add(site)
        print("✅ Application Google configurée")
        
        # Configurer Facebook OAuth
        facebook_app = SocialApp.objects.create(
            provider='facebook',
            name='Facebook',
            client_id='1415333696343612',
            secret='fd1e66ffcd47958997274808d0c2ec64'
        )
        facebook_app.sites.add(site)
        print("✅ Application Facebook configurée")
        
        # Vérifier la configuration
        google_count = SocialApp.objects.filter(provider='google').count()
        facebook_count = SocialApp.objects.filter(provider='facebook').count()
        
        print("\n📊 État de la configuration:")
        print(f"  • Applications Google: {google_count}")
        print(f"  • Applications Facebook: {facebook_count}")
        
        if google_count == 1 and facebook_count == 1:
            print("\n🎉 Configuration sociale terminée avec succès!")
            print("\n🔗 URLs d'authentification disponibles:")
            print("  • /accounts/google/login/")
            print("  • /accounts/facebook/login/")
            print("  • /accounts/login/ (connexion classique)")
            print("  • /accounts/signup/ (inscription classique)")
            return True
        else:
            print("\n❌ Problème de configuration détecté")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la configuration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = configure_social_apps()
    exit(0 if success else 1)