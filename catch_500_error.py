#!/usr/bin/env python
"""Capturer l'erreur 500 exacte sur practitioner_create"""

import os
import sys
import django
import logging

# Configuration Django
sys.path.insert(0, '/var/www/vhosts/martialcomp.com/httpdocs')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Activer le mode DEBUG temporairement pour voir l'erreur
from django.conf import settings
settings.DEBUG = True

django.setup()

# Configurer le logging pour capturer toutes les erreurs
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('django')

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.messages.storage.session import SessionStorage

User = get_user_model()

print("=== Capture de l'erreur 500 sur practitioner_create ===\n")

try:
    # Récupérer un utilisateur actif
    user = User.objects.get(username='bguinziemba')
    print(f"Utilisateur: {user.username} (ID: {user.id})")
    
    # Créer une requête complète avec session et messages
    factory = RequestFactory()
    request = factory.get('/fr/competitions/club/practitioners/add/')
    
    # Configurer la session
    request.session = SessionStore()
    request.session.create()
    
    # Configurer l'utilisateur
    request.user = user
    
    # Ajouter le middleware d'organisation
    from apps.core.isolation import OrganizationSecurityMiddleware
    middleware = OrganizationSecurityMiddleware(lambda r: None)
    request.user_organization = middleware.get_user_organization(user)
    print(f"Organisation: {request.user_organization}")
    
    # Ajouter le support des messages
    request._messages = SessionStorage(request)
    
    # Importer et appeler la vue
    from apps.competitions.views.club.practitioners import practitioner_create
    
    try:
        response = practitioner_create(request)
        print(f"\nRéponse: {response.status_code}")
        
        if response.status_code == 500:
            print("\nERREUR 500 DÉTECTÉE!")
            print("Contenu de l'erreur:")
            print(response.content.decode('utf-8')[:2000])
            
    except Exception as e:
        print(f"\nEXCEPTION CAPTURÉE!")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        
        import traceback
        print("\nTraceback complet:")
        traceback.print_exc()
        
        # Essayer de comprendre l'erreur
        if hasattr(e, '__context__') and e.__context__:
            print(f"\nContexte: {e.__context__}")
            
except User.DoesNotExist:
    print("Utilisateur coach1 non trouvé")
except Exception as e:
    print(f"Erreur inattendue: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Remettre DEBUG à False
    settings.DEBUG = False