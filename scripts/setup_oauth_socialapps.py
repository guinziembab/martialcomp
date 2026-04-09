#!/usr/bin/env python
"""
Script pour configurer les applications OAuth (Google & Facebook) dans Django
via le modèle SocialApp de django-allauth.

Usage:
    python manage.py shell < scripts/setup_oauth_socialapps.py

Ou en production:
    ssh martialcomp-production
    cd /var/www/vhosts/martialcomp.com/httpdocs
    source ../venv/bin/activate
    python manage.py shell < scripts/setup_oauth_socialapps.py
"""

import os
import sys

# Configuration OAuth
# ============================================================
# IMPORTANT: Remplacez VOTRE_GOOGLE_CLIENT_SECRET avant d'exécuter
# ============================================================

OAUTH_CONFIG = {
    'google': {
        'name': 'Google',
        'client_id': '246820300466-up5bbhd2199t9ekep3sa4jmhtto12tel.apps.googleusercontent.com',
        'secret': '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',
    },
    'facebook': {
        'name': 'Facebook',
        'client_id': '1415333696343612',
        'secret': 'fd1e66ffcd47958997274808d0c2ec64',
    }
}

def setup_oauth():
    """Configure les applications OAuth dans la base de données."""

    try:
        from allauth.socialaccount.models import SocialApp
        from django.contrib.sites.models import Site
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Assurez-vous que django-allauth est installé.")
        return False

    # Récupérer le site par défaut
    try:
        site = Site.objects.get_current()
        print(f"✅ Site actuel: {site.domain}")
    except Site.DoesNotExist:
        # Créer le site si nécessaire
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={'domain': 'martialcomp.com', 'name': 'MartialComp'}
        )
        if created:
            print(f"✅ Site créé: {site.domain}")
        else:
            print(f"✅ Site existant: {site.domain}")

    # Mettre à jour le domaine si nécessaire
    if site.domain not in ['martialcomp.com', 'www.martialcomp.com']:
        site.domain = 'martialcomp.com'
        site.name = 'MartialComp'
        site.save()
        print(f"✅ Domaine mis à jour: {site.domain}")

    print("\n" + "="*50)
    print("Configuration des applications OAuth")
    print("="*50 + "\n")

    for provider, config in OAUTH_CONFIG.items():
        print(f"\n🔧 Configuration {config['name']}...")

        # Vérifier que le secret est défini
        if config['secret'] == 'VOTRE_GOOGLE_CLIENT_SECRET':
            print(f"   ⚠️  ATTENTION: Secret {provider} non configuré!")
            print(f"   Remplacez 'VOTRE_GOOGLE_CLIENT_SECRET' par la vraie valeur.")
            continue

        # Chercher une app existante ou en créer une nouvelle
        app, created = SocialApp.objects.update_or_create(
            provider=provider,
            defaults={
                'name': config['name'],
                'client_id': config['client_id'],
                'secret': config['secret'],
            }
        )

        # Associer au site
        if site not in app.sites.all():
            app.sites.add(site)

        action = "créée" if created else "mise à jour"
        print(f"   ✅ Application {config['name']} {action}")
        print(f"      Client ID: {config['client_id'][:20]}...")
        print(f"      Secret: {'*' * 10} (masqué)")
        print(f"      Site associé: {site.domain}")

    print("\n" + "="*50)
    print("✅ Configuration OAuth terminée!")
    print("="*50)

    # Afficher les applications configurées
    print("\nApplications OAuth configurées:")
    for app in SocialApp.objects.all():
        sites = ", ".join([s.domain for s in app.sites.all()])
        print(f"  - {app.provider}: {app.name} (sites: {sites})")

    return True


if __name__ == '__main__':
    setup_oauth()
else:
    # Exécuté via manage.py shell
    setup_oauth()
