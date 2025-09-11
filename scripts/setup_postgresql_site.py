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
from django.db import transaction

def setup_site_for_martialcomp():
    """Create or update the Site object for MartialComp in PostgreSQL."""
    
    print("🚀 Configuration du Site pour l'authentification sociale...")
    
    try:
        with transaction.atomic():
            # Try to get the existing site with ID 1
            try:
                site = Site.objects.get(id=1)
                site.domain = 'martialcomp.com'
                site.name = 'MartialComp'
                site.save()
                print(f"✅ Site mis à jour: {site.domain} - {site.name}")
            except Site.DoesNotExist:
                # Create new site with ID 1
                site = Site.objects.create(
                    id=1, 
                    domain='martialcomp.com', 
                    name='MartialComp'
                )
                print(f"✅ Site créé: {site.domain} - {site.name}")
        
        # Verify the site was created/updated
        site = Site.objects.get(id=1)
        print(f"✅ Vérification: Site ID {site.id} - {site.domain} - {site.name}")
        
        print("\n📋 Configuration complète pour django-allauth:")
        print("   - SITE_ID = 1 ✅")
        print("   - Site object créé ✅")
        print("   - Domain: martialcomp.com ✅")
        print("   - Name: MartialComp ✅")
        
        print("\n🔄 Prochaines étapes:")
        print("   1. Installer django-allauth: pip install django-allauth")
        print("   2. Décommenter les apps allauth dans INSTALLED_APPS")
        print("   3. Exécuter les migrations: python manage.py migrate")
        print("   4. Configurer les fournisseurs sociaux (Google, Facebook, Apple)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la configuration du Site: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        
        # Si c'est un problème de table manquante, suggérer les migrations
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("\n💡 Il semble que la table django_site n'existe pas.")
            print("   Exécutez: python manage.py migrate sites")

if __name__ == "__main__":
    setup_site_for_martialcomp()