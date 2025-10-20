#!/usr/bin/env python3
"""
Script pour installer le middleware de blocage en production
"""
import os

print("📦 INSTALLATION DU MIDDLEWARE DE BLOCAGE")
print("=" * 60)

# 1. Créer le répertoire si nécessaire
print("\n1. Création du répertoire middleware...")
middleware_dir = "apps/core/middleware"
os.makedirs(middleware_dir, exist_ok=True)

# 2. Créer __init__.py
init_file = os.path.join(middleware_dir, "__init__.py")
if not os.path.exists(init_file):
    open(init_file, 'a').close()
    print(f"✅ Créé: {init_file}")

# 3. Copier le middleware
middleware_content = '''"""
Middleware d'urgence pour bloquer l'accès aux practitioners
"""
from django.http import HttpResponseRedirect
from django.contrib import messages

class BlockPractitionerMiddleware:
    """
    Middleware qui bloque complètement l'accès aux URLs practitioner
    et redirige vers le dashboard
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Vérifier si l'URL contient 'practitioner'
        if 'practitioner' in request.path.lower():
            # Logger l'accès bloqué
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Accès bloqué à practitioner: {request.path} par {request.user}")
            
            # Message à l'utilisateur
            if hasattr(request, 'user') and request.user.is_authenticated:
                messages.warning(
                    request, 
                    "La section Practitioners est temporairement désactivée pour maintenance."
                )
            
            # Rediriger vers l'admin
            return HttpResponseRedirect('/fr/admin/')
        
        response = self.get_response(request)
        return response
'''

block_file = os.path.join(middleware_dir, "block_practitioner.py")
with open(block_file, 'w') as f:
    f.write(middleware_content)
print(f"✅ Créé: {block_file}")

# 4. Instructions pour la production
print("\n⚠️  INSTALLATION EN PRODUCTION:")
print("-" * 40)
print("1. Copier les fichiers:")
print("   scp -r apps/core/middleware user@martialcomp.com:/var/www/vhosts/martialcomp.com/httpdocs/apps/core/")
print()
print("2. Modifier config/settings/production.py:")
print("   Ajouter dans MIDDLEWARE après 'django.middleware.security.SecurityMiddleware':")
print("   'apps.core.middleware.block_practitioner.BlockPractitionerMiddleware',")
print()
print("3. Redémarrer Apache:")
print("   systemctl restart apache2")
print()
print("✅ Le middleware bloquera toutes les URLs contenant 'practitioner'")