#!/usr/bin/env python3
"""
Script simple de debug pour l'import
"""

import os
import sys
import django

def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

def debug_import():
    print('DEBUG IMPORT LicenseNumberGenerator')
    print('=' * 40)
    
    setup_django()
    
    # Test 1: Import du module
    print('1. Test import module...')
    try:
        import apps.competitions.services as services_module
        print(f'   Module: {services_module}')
        print(f'   Contient LicenseNumberGenerator: {hasattr(services_module, "LicenseNumberGenerator")}')
        if hasattr(services_module, 'LicenseNumberGenerator'):
            print(f'   LicenseNumberGenerator: {services_module.LicenseNumberGenerator}')
    except Exception as e:
        print(f'   Erreur: {e}')
    
    print()
    
    # Test 2: Import direct
    print('2. Test import direct...')
    try:
        from apps.competitions.services import LicenseNumberGenerator
        print(f'   LicenseNumberGenerator: {LicenseNumberGenerator}')
        print(f'   Type: {type(LicenseNumberGenerator)}')
        print(f'   Has generate: {hasattr(LicenseNumberGenerator, "generate")}')
    except Exception as e:
        print(f'   Erreur: {e}')
    
    print()
    
    # Test 3: Contenu du module
    print('3. Contenu du module...')
    try:
        import apps.competitions.services as services_module
        print(f'   Attributs: {dir(services_module)}')
    except Exception as e:
        print(f'   Erreur: {e}')

if __name__ == "__main__":
    debug_import()