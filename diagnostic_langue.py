#!/usr/bin/env python
"""
Script de diagnostic pour analyser le problème de basculement automatique de langue
MartialComp - Django i18n Debug Tool
"""

import os
import sys
import django
from pathlib import Path

# Configuration de l'environnement Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

try:
    django.setup()
except Exception as e:
    print(f"❌ Erreur d'initialisation Django: {e}")
    sys.exit(1)

from django.conf import settings
from django.utils import translation

def diagnostic_complet():
    """Effectue un diagnostic complet du système i18n"""
    print("=" * 60)
    print("🔍 DIAGNOSTIC LANGUE MARTIALCOMP")
    print("=" * 60)
    
    # 1. Configuration i18n de base
    print("\n📋 1. CONFIGURATION I18N")
    print(f"   USE_I18N: {settings.USE_I18N}")
    print(f"   USE_L10N: {settings.USE_L10N}")
    print(f"   LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
    print(f"   LANGUAGES: {len(settings.LANGUAGES)} langues configurées")
    for code, name in settings.LANGUAGES:
        print(f"      - {code}: {name}")
    
    # 2. Middleware de localisation
    print("\n🔧 2. MIDDLEWARE CONFIGURATION")
    middleware = settings.MIDDLEWARE
    locale_middleware = None
    for i, m in enumerate(middleware):
        if 'locale' in m.lower():
            locale_middleware = (i, m)
            break
    
    if locale_middleware:
        print(f"   ✅ LocaleMiddleware trouvé à la position {locale_middleware[0]}: {locale_middleware[1]}")
        # Vérifier la position correcte
        if locale_middleware[0] < 3:
            print("   ✅ Position correcte (avant CommonMiddleware)")
        else:
            print("   ⚠️  Position incorrecte (devrait être avant CommonMiddleware)")
    else:
        print("   ❌ LocaleMiddleware NON TROUVÉ!")
    
    # 3. Configuration des chemins de traduction
    print("\n📁 3. FICHIERS DE TRADUCTION")
    locale_paths = getattr(settings, 'LOCALE_PATHS', [])
    print(f"   LOCALE_PATHS: {len(locale_paths)} chemin(s)")
    
    for path in locale_paths:
        if os.path.exists(path):
            print(f"   ✅ {path} existe")
            try:
                langs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
                print(f"      Langues trouvées: {langs}")
                
                # Vérifier les fichiers .mo
                for lang in langs:
                    mo_path = os.path.join(path, lang, 'LC_MESSAGES', 'django.mo')
                    if os.path.exists(mo_path):
                        mtime = os.path.getmtime(mo_path)
                        import datetime
                        date = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"      ✅ {lang}/django.mo (modifié: {date})")
                    else:
                        print(f"      ❌ {lang}/django.mo manquant")
            except Exception as e:
                print(f"      ❌ Erreur lecture: {e}")
        else:
            print(f"   ❌ {path} n'existe pas")
    
    # 4. Test de traduction
    print("\n🌍 4. TEST DE TRADUCTION")
    test_strings = ["Hello", "Welcome", "Login", "Dashboard"]
    
    for lang_code, lang_name in [('fr', 'Français'), ('en', 'English'), ('es', 'Español')]:
        print(f"\n   📍 Test {lang_name} ({lang_code}):")
        try:
            translation.activate(lang_code)
            from django.utils.translation import gettext as _
            
            for test_str in test_strings:
                translated = _(test_str)
                if translated != test_str:
                    print(f"      ✅ '{test_str}' → '{translated}'")
                else:
                    print(f"      ⚠️  '{test_str}' → '{translated}' (non traduit)")
        except Exception as e:
            print(f"      ❌ Erreur: {e}")
    
    # 5. Configuration URL
    print("\n🔗 5. CONFIGURATION URLS")
    print(f"   ROOT_URLCONF: {settings.ROOT_URLCONF}")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # Chercher i18n_patterns
        urlconf = __import__(settings.ROOT_URLCONF, fromlist=[''])
        if hasattr(urlconf, 'urlpatterns'):
            has_i18n = any('i18n_patterns' in str(pattern) for pattern in urlconf.urlpatterns)
            if has_i18n:
                print("   ✅ i18n_patterns détecté dans les URLs")
            else:
                print("   ⚠️  i18n_patterns non détecté")
        
    except Exception as e:
        print(f"   ❌ Erreur analyse URLs: {e}")
    
    # 6. Variables d'environnement
    print("\n🔧 6. ENVIRONNEMENT")
    django_env = os.environ.get('DJANGO_SETTINGS_MODULE', 'Non défini')
    print(f"   DJANGO_SETTINGS_MODULE: {django_env}")
    
    debug_mode = getattr(settings, 'DEBUG', False)
    print(f"   DEBUG: {debug_mode}")
    
    # 7. Diagnostic de la langue courante
    print("\n🎯 7. LANGUE COURANTE")
    current_lang = translation.get_language()
    print(f"   Langue active: {current_lang}")
    
    # Restaurer la langue par défaut
    translation.deactivate()
    
    # 8. Recommandations
    print("\n💡 8. RECOMMANDATIONS")
    
    if not locale_middleware:
        print("   🔴 CRITIQUE: Ajouter 'django.middleware.locale.LocaleMiddleware' dans MIDDLEWARE")
        print("      Position recommandée: après SessionMiddleware, avant CommonMiddleware")
    
    if not locale_paths or not any(os.path.exists(p) for p in locale_paths):
        print("   🔴 CRITIQUE: Configurer LOCALE_PATHS et créer les répertoires de traduction")
    
    if debug_mode:
        print("   🟡 INFO: Mode DEBUG activé - parfait pour les tests")
    else:
        print("   🟢 PROD: Mode production détecté")
        print("      Assurez-vous que les fichiers .mo sont compilés et déployés")
    
    print("\n" + "=" * 60)
    print("🏁 DIAGNOSTIC TERMINÉ")
    print("=" * 60)

def test_language_detection():
    """Test la détection de langue"""
    print("\n🧪 TEST DE DÉTECTION DE LANGUE")
    print("-" * 40)
    
    from django.test import RequestFactory
    from django.utils import translation
    
    factory = RequestFactory()
    
    # Test 1: Accept-Language header
    print("Test 1: Header Accept-Language")
    request = factory.get('/', HTTP_ACCEPT_LANGUAGE='fr,en;q=0.9')
    print(f"   Header: {request.META.get('HTTP_ACCEPT_LANGUAGE')}")
    
    # Test 2: Cookie
    print("Test 2: Cookie django_language")
    request = factory.get('/')
    request.COOKIES = {'django_language': 'de'}
    print(f"   Cookie: {request.COOKIES.get('django_language')}")
    
    # Test 3: Session
    print("Test 3: Session")
    request = factory.get('/')
    # Simuler une session
    print("   Session django_language: es (simulé)")

if __name__ == "__main__":
    diagnostic_complet()
    test_language_detection()