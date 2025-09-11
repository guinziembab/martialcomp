#!/usr/bin/env python3

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/mnt/c/martial_hub_django/martialcomp')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.db import transaction

def update_social_keys():
    """Mettre à jour les clés API des fournisseurs sociaux."""
    
    print("🔐 Mise à jour des clés API des fournisseurs sociaux")
    print("=" * 60)
    
    # Clés à configurer (à remplacer par les vraies valeurs)
    keys_config = {
        'google': {
            'client_id': 'YOUR_ACTUAL_GOOGLE_CLIENT_ID',
            'secret': 'YOUR_ACTUAL_GOOGLE_CLIENT_SECRET'
        },
        'facebook': {
            'client_id': 'YOUR_ACTUAL_FACEBOOK_APP_ID', 
            'secret': 'YOUR_ACTUAL_FACEBOOK_APP_SECRET'
        },
        'apple': {
            'client_id': 'YOUR_ACTUAL_APPLE_SERVICES_ID',
            'secret': 'YOUR_ACTUAL_APPLE_PRIVATE_KEY'
        }
    }
    
    try:
        with transaction.atomic():
            for provider, keys in keys_config.items():
                try:
                    app = SocialApp.objects.get(provider=provider)
                    
                    # Vérifier si les clés ont été modifiées
                    if 'YOUR_ACTUAL_' in keys['client_id']:
                        print(f"⚠️  {provider.title()}: Clés non configurées (placeholders détectés)")
                        continue
                    
                    app.client_id = keys['client_id']
                    app.secret = keys['secret']
                    app.save()
                    
                    print(f"✅ {provider.title()}: Clés mises à jour")
                    print(f"   Client ID: {keys['client_id'][:10]}...")
                    
                except SocialApp.DoesNotExist:
                    print(f"❌ {provider.title()}: Application non trouvée")
            
            print("\n📋 Statut final des applications:")
            for app in SocialApp.objects.all():
                status = "🔐 Configuré" if not app.client_id.startswith('YOUR_') else "⚠️  Non configuré"
                print(f"   {app.provider.title()}: {status}")
                
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

def show_configuration_guide():
    """Afficher le guide de configuration des consoles développeur."""
    
    print("\n" + "=" * 60)
    print("📚 GUIDE DE CONFIGURATION DES CONSOLES DÉVELOPPEUR")
    print("=" * 60)
    
    print("\n📱 GOOGLE OAUTH2:")
    print("   1. Aller sur https://console.cloud.google.com/")
    print("   2. Créer un projet ou sélectionner un projet existant")
    print("   3. Activer l'API Google+ et Google Sign-In")
    print("   4. Créer des identifiants OAuth 2.0:")
    print("      - Type: Application Web")
    print("      - Origines JavaScript: https://martialcomp.com")
    print("      - URI de redirection: https://martialcomp.com/accounts/google/login/callback/")
    
    print("\n📘 FACEBOOK LOGIN:")
    print("   1. Aller sur https://developers.facebook.com/")
    print("   2. Créer une nouvelle application")
    print("   3. Ajouter le produit 'Facebook Login'")
    print("   4. Configurer:")
    print("      - URI de redirection OAuth: https://martialcomp.com/accounts/facebook/login/callback/")
    print("      - Domaines d'application: martialcomp.com")
    
    print("\n🍎 APPLE SIGN IN:")
    print("   1. Aller sur https://developer.apple.com/")
    print("   2. Créer un App ID avec 'Sign In with Apple'")
    print("   3. Créer un Services ID pour le web")
    print("   4. Configurer les domaines et URLs:")
    print("      - Domain: martialcomp.com")
    print("      - Return URL: https://martialcomp.com/accounts/apple/login/callback/")
    print("   5. Générer une clé privée")
    
    print("\n🔐 MISE À JOUR DES CLÉS:")
    print("   1. Éditer le fichier update_social_keys_production.py")
    print("   2. Remplacer 'YOUR_ACTUAL_*' par les vraies valeurs")
    print("   3. Exécuter: python3 update_social_keys_production.py")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--guide':
        show_configuration_guide()
    else:
        success = update_social_keys()
        if success:
            print("\n✅ Mise à jour terminée !")
            print("\n💡 Pour voir le guide de configuration:")
            print("   python3 update_social_keys_production.py --guide")
        else:
            print("\n❌ Échec de la mise à jour.")
            sys.exit(1)