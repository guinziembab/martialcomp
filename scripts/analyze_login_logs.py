#!/usr/bin/env python3
"""
Analyseur de logs pour diagnostiquer le problème de connexion
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import logging

# Configuration du logging pour capturer les détails
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def setup_detailed_logging():
    """Configure un logging détaillé pour Django"""
    
    # Configurer les loggers Django
    loggers = [
        'django.request',
        'django.contrib.auth',
        'allauth',
        'allauth.account',
        'django.db.backends',
        'django.contrib.sessions'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        
        # Créer un handler pour afficher les logs
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'[{logger_name}] %(levelname)s %(asctime)s: %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

def test_login_with_logs():
    print("🔍 TEST CONNEXION AVEC LOGS DÉTAILLÉS")
    print("="*70)
    
    setup_detailed_logging()
    
    # Préparer l'utilisateur
    user, created = User.objects.get_or_create(
        username='ClaudiuG',
        defaults={'email': 'claudiug@martialcomp.com', 'first_name': 'Claudiu'}
    )
    user.set_password('AQW123ok')
    user.save()
    print(f"✅ Utilisateur préparé: {user.username}")
    
    client = Client()
    
    print("\n📋 ÉTAPE 1: Accès page de login")
    print("-" * 50)
    
    response = client.get('/accounts/login/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Page de login accessible")
        
        # Extraire le token CSRF
        csrf_token = client.cookies.get('csrftoken', {}).value if 'csrftoken' in client.cookies else ''
        print(f"CSRF token: {csrf_token[:20]}..." if csrf_token else "❌ Pas de CSRF token")
        
        print(f"\n📋 ÉTAPE 2: Soumission formulaire")
        print("-" * 50)
        
        login_data = {
            'login': 'ClaudiuG',
            'password': 'AQW123ok',
            'csrfmiddlewaretoken': csrf_token
        }
        
        print(f"Données envoyées: {login_data}")
        
        # Soumettre le formulaire avec logging activé
        response = client.post('/accounts/login/', data=login_data)
        
        print(f"Status réponse: {response.status_code}")
        
        if response.status_code == 302:
            redirect_url = response.get('Location', '')
            print(f"Redirection vers: {redirect_url}")
            
            print(f"\n📋 ÉTAPE 3: Suivi redirection")
            print("-" * 50)
            
            response = client.get(redirect_url)
            print(f"Status final: {response.status_code}")
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Analyser le contenu pour voir l'état de connexion
                auth_checks = [
                    ('user-info', 'Section utilisateur connecté'),
                    ('welcome-text', 'Message de bienvenue'),
                    ('Se déconnecter', 'Lien de déconnexion'),
                    ('Se connecter', 'Bouton de connexion (ne devrait pas être là)'),
                    ('ClaudiuG', 'Nom d\'utilisateur'),
                    ('openModal(\'loginModal\')', 'Modal de login (ne devrait pas être là)')
                ]
                
                print("\n🔍 ANALYSE DU CONTENU FINAL:")
                for check, description in auth_checks:
                    status = "✅" if check in content else "❌"
                    print(f"   {status} {description}")
                
                # Extraire et afficher la section d'authentification
                print(f"\n📄 SECTION D'AUTHENTIFICATION:")
                auth_start = content.find('<div class="auth-section">')
                if auth_start != -1:
                    auth_end = content.find('</div>', auth_start + 500)
                    if auth_end != -1:
                        auth_section = content[auth_start:auth_end + 6]
                        # Nettoyer le HTML pour l'affichage
                        import re
                        clean_html = re.sub(r'\s+', ' ', auth_section)
                        print(f"   {clean_html[:300]}...")
                else:
                    print("   ❌ Section auth-section non trouvée")
        
        elif response.status_code == 200:
            print("❌ Pas de redirection - formulaire réaffiché")
            content = response.content.decode('utf-8')
            
            # Chercher des messages d'erreur
            if 'error' in content.lower():
                print("⚠️  Des erreurs sont présentes dans le formulaire")
            
            # Chercher des éléments d'erreur allauth
            error_indicators = [
                'errorlist',
                'form-error',
                'alert-danger',
                'is-invalid',
                'field-error'
            ]
            
            for indicator in error_indicators:
                if indicator in content:
                    print(f"⚠️  Indicateur d'erreur trouvé: {indicator}")
    
    print(f"\n📋 ÉTAPE 4: Test de vérification")
    print("-" * 50)
    
    # Test final pour vérifier l'état de la session
    verification_response = client.get('/fr/')
    if verification_response.status_code == 200:
        content = verification_response.content.decode('utf-8')
        
        if 'ClaudiuG' in content and 'Se déconnecter' in content:
            print("🎉 SUCCÈS FINAL! Utilisateur connecté et affiché correctement")
            return True
        else:
            print("❌ ÉCHEC FINAL! Utilisateur non connecté ou mal affiché")
    
    return False

def check_allauth_configuration():
    print(f"\n📋 VÉRIFICATION CONFIGURATION ALLAUTH")
    print("-" * 50)
    
    from django.conf import settings
    
    configs = [
        ('SITE_ID', getattr(settings, 'SITE_ID', 'Non défini')),
        ('LOGIN_REDIRECT_URL', getattr(settings, 'LOGIN_REDIRECT_URL', 'Non défini')),
        ('ACCOUNT_AUTHENTICATION_METHOD', getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'Non défini')),
        ('ACCOUNT_EMAIL_VERIFICATION', getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'Non défini')),
        ('ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION', getattr(settings, 'ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION', 'Non défini')),
    ]
    
    for key, value in configs:
        print(f"   {key}: {value}")
    
    # Vérifier les backends d'authentification
    print(f"\n   AUTHENTICATION_BACKENDS:")
    backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
    for backend in backends:
        print(f"      - {backend}")

def check_site_configuration():
    print(f"\n📋 VÉRIFICATION CONFIGURATION SITE")
    print("-" * 50)
    
    try:
        from django.contrib.sites.models import Site
        
        sites = Site.objects.all()
        print(f"   Sites configurés: {sites.count()}")
        
        for site in sites:
            print(f"      ID {site.id}: {site.domain} - {site.name}")
        
        # Vérifier le site par défaut
        from django.conf import settings
        site_id = getattr(settings, 'SITE_ID', 1)
        
        try:
            current_site = Site.objects.get(id=site_id)
            print(f"   Site actuel (ID {site_id}): {current_site.domain}")
        except Site.DoesNotExist:
            print(f"   ❌ Site ID {site_id} non trouvé!")
            
    except Exception as e:
        print(f"   ❌ Erreur vérification sites: {e}")

if __name__ == "__main__":
    try:
        check_allauth_configuration()
        check_site_configuration()
        
        success = test_login_with_logs()
        
        print(f"\n{'='*70}")
        if success:
            print("✅ CONNEXION RÉUSSIE AVEC LOGS")
        else:
            print("❌ CONNEXION ÉCHOUÉE - VOIR LOGS CI-DESSUS")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()