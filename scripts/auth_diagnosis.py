#!/usr/bin/env python3
"""
Script de diagnostic d'authentification pour MartialComp
Usage: python scripts/auth_diagnosis.py
"""

import django
import os
import sys

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.sites.models import Site
from django.conf import settings

try:
    from allauth.socialaccount.models import SocialApp
    ALLAUTH_AVAILABLE = True
except ImportError:
    ALLAUTH_AVAILABLE = False
    print("⚠️  django-allauth n'est pas disponible")

User = get_user_model()

def print_separator():
    print("=" * 60)

def print_subsection(title):
    print(f"\n--- {title} ---")

def run_diagnostics():
    print_separator()
    print("🔍 DIAGNOSTIC DE L'AUTHENTIFICATION MARTIALCOMP")
    print_separator()
    
    # 1. Informations générales
    print_subsection("Informations générales")
    print(f"Django version: {django.get_version()}")
    print(f"Settings module: {settings.SETTINGS_MODULE}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Secret key: {'✓ Définie' if settings.SECRET_KEY else '✗ Non définie'}")
    
    # 2. Configuration de la base de données
    print_subsection("Configuration de la base de données")
    db_config = settings.DATABASES['default']
    print(f"Engine: {db_config['ENGINE']}")
    print(f"Name: {db_config['NAME']}")
    print(f"Host: {db_config.get('HOST', 'localhost')}")
    print(f"Port: {db_config.get('PORT', 'default')}")
    
    # 3. Vérifier le nombre d'utilisateurs
    print_subsection("Statistiques des utilisateurs")
    users_count = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    
    print(f"Total utilisateurs: {users_count}")
    print(f"Utilisateurs actifs: {active_users}")
    print(f"Superutilisateurs: {superusers}")
    print(f"Staff: {staff_users}")
    
    # 4. Vérifier la configuration des sites
    print_subsection("Configuration des sites")
    sites = Site.objects.all()
    print(f"Sites configurés: {sites.count()}")
    for site in sites:
        print(f"  - {site.domain} ({site.name}) [ID: {site.id}]")
    
    # 5. Vérifier les applications sociales (si allauth est disponible)
    if ALLAUTH_AVAILABLE:
        print_subsection("Applications sociales (Allauth)")
        social_apps = SocialApp.objects.all()
        print(f"Applications sociales: {social_apps.count()}")
        for app in social_apps:
            print(f"  - {app.provider} ({app.name})")
            print(f"    Client ID: {'✓ Défini' if app.client_id else '✗ Non défini'}")
            print(f"    Secret: {'✓ Défini' if app.secret else '✗ Non défini'}")
            print(f"    Sites associés: {app.sites.count()}")
            for site in app.sites.all():
                print(f"      - {site.domain}")
    
    # 6. Paramètres d'authentification
    print_subsection("Paramètres d'authentification")
    print(f"Backends d'authentification:")
    for backend in settings.AUTHENTICATION_BACKENDS:
        print(f"  - {backend}")
    
    if ALLAUTH_AVAILABLE:
        print(f"ACCOUNT_AUTHENTICATION_METHOD: {getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'Non défini')}")
        print(f"ACCOUNT_EMAIL_REQUIRED: {getattr(settings, 'ACCOUNT_EMAIL_REQUIRED', 'Non défini')}")
        print(f"ACCOUNT_EMAIL_VERIFICATION: {getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'Non défini')}")
        print(f"ACCOUNT_USERNAME_REQUIRED: {getattr(settings, 'ACCOUNT_USERNAME_REQUIRED', 'Non défini')}")
    
    # 7. Paramètres de session
    print_subsection("Paramètres de session")
    print(f"SESSION_ENGINE: {settings.SESSION_ENGINE}")
    print(f"SESSION_COOKIE_AGE: {settings.SESSION_COOKIE_AGE} secondes")
    print(f"SESSION_EXPIRE_AT_BROWSER_CLOSE: {settings.SESSION_EXPIRE_AT_BROWSER_CLOSE}")
    print(f"SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
    print(f"SESSION_COOKIE_HTTPONLY: {settings.SESSION_COOKIE_HTTPONLY}")
    
    # 8. Paramètres CSRF
    print_subsection("Paramètres CSRF")
    print(f"CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
    print(f"CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}")
    print(f"CSRF_COOKIE_SAMESITE: {getattr(settings, 'CSRF_COOKIE_SAMESITE', 'Non défini')}")
    print(f"CSRF_USE_SESSIONS: {getattr(settings, 'CSRF_USE_SESSIONS', 'Non défini')}")
    
    if hasattr(settings, 'CSRF_TRUSTED_ORIGINS'):
        print(f"CSRF_TRUSTED_ORIGINS:")
        for origin in settings.CSRF_TRUSTED_ORIGINS:
            print(f"  - {origin}")
    
    # 9. Configuration des URLs
    print_subsection("Configuration des URLs")
    print(f"LOGIN_REDIRECT_URL: {getattr(settings, 'LOGIN_REDIRECT_URL', 'Non défini')}")
    print(f"LOGOUT_REDIRECT_URL: {getattr(settings, 'LOGOUT_REDIRECT_URL', 'Non défini')}")
    print(f"BASE_URL: {getattr(settings, 'BASE_URL', 'Non défini')}")
    
    # 10. Test d'authentification pour un utilisateur
    print_subsection("Test d'authentification utilisateur")
    if users_count > 0:
        print("Utilisateurs disponibles pour le test:")
        test_users = User.objects.all()[:5]  # Afficher les 5 premiers
        for i, user in enumerate(test_users, 1):
            print(f"  {i}. {user.username} ({user.email}) - Actif: {user.is_active}")
        
        try:
            choice = input("\nEntrez le numéro de l'utilisateur à tester (ou 'skip' pour ignorer): ")
            if choice.lower() != 'skip' and choice.isdigit():
                user_index = int(choice) - 1
                if 0 <= user_index < len(test_users):
                    test_user = test_users[user_index]
                    test_password = input(f"Entrez le mot de passe pour {test_user.username}: ")
                    
                    print(f"\n🔍 Test pour l'utilisateur: {test_user.username}")
                    print(f"Email: {test_user.email}")
                    print(f"Est actif: {test_user.is_active}")
                    print(f"Est staff: {test_user.is_staff}")
                    print(f"Est superuser: {test_user.is_superuser}")
                    print(f"Dernière connexion: {test_user.last_login}")
                    print(f"Date de création: {test_user.date_joined}")
                    
                    if check_password(test_password, test_user.password):
                        print("✅ Mot de passe correct")
                    else:
                        print("❌ Mot de passe incorrect")
                    
                    # Vérifier les paramètres du profil si disponible
                    if hasattr(test_user, 'profile'):
                        profile = test_user.profile
                        print(f"\n📋 Informations du profil:")
                        print(f"Onboarding complété: {getattr(profile, 'onboarding_completed', 'Non défini')}")
                        print(f"Étape d'onboarding: {getattr(profile, 'onboarding_step', 'Non défini')}")
                        print(f"Rôle: {getattr(profile, 'role', 'Non défini')}")
                    else:
                        print("❌ Profil utilisateur non trouvé")
                        
        except KeyboardInterrupt:
            print("\nTest interrompu par l'utilisateur.")
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
    else:
        print("Aucun utilisateur disponible pour le test.")
    
    # 11. Vérifications de sécurité
    print_subsection("Vérifications de sécurité")
    security_checks = []
    
    if settings.DEBUG:
        security_checks.append("⚠️  DEBUG est activé (ne pas utiliser en production)")
    else:
        security_checks.append("✅ DEBUG est désactivé")
    
    if settings.SECRET_KEY == 'django-insecure-martialcomp-secret-key-change-in-production-2025-auth-system':
        security_checks.append("❌ SECRET_KEY par défaut détectée (CHANGEZ-LA !)")
    else:
        security_checks.append("✅ SECRET_KEY personnalisée")
    
    if '*' in settings.ALLOWED_HOSTS:
        security_checks.append("⚠️  ALLOWED_HOSTS contient '*' (ne pas utiliser en production)")
    else:
        security_checks.append("✅ ALLOWED_HOSTS configuré correctement")
    
    for check in security_checks:
        print(check)
    
    print_separator()
    print("🎉 DIAGNOSTIC TERMINÉ")
    print_separator()

if __name__ == "__main__":
    try:
        run_diagnostics()
    except Exception as e:
        print(f"❌ Erreur lors du diagnostic: {e}")
        sys.exit(1)