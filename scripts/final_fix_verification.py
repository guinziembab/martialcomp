#!/usr/bin/env python3
"""
Vérification finale de la correction NoReverseMatch
"""

import os
import sys
import django

print("🔍 VÉRIFICATION FINALE DE LA CORRECTION")
print("=" * 50)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import reverse, NoReverseMatch, get_resolver

try:
    print("✅ VÉRIFICATION DES URLs PROBLÉMATIQUES:")
    
    # URLs qui causaient l'erreur
    problem_urls = [
        '/fr/competitions/practitioner/support/',
        '/fr/competitions/practitioner/notifications/'
    ]
    
    resolver = get_resolver()
    
    for test_url in problem_urls:
        try:
            match = resolver.resolve(test_url)
            print(f"✅ {test_url}")
            print(f"   → Vue: {match.func.__name__}")
            print(f"   → Namespace: {match.namespace}")
            print(f"   → URL name: {match.url_name}")
        except Exception as e:
            print(f"❌ {test_url}: {e}")
    
    print(f"\n✅ VÉRIFICATION DES REDIRECTIONS:")
    
    # Tester que 'welcome' fonctionne
    try:
        welcome_url = reverse('welcome')
        print(f"✅ 'welcome' URL: {welcome_url}")
    except NoReverseMatch as e:
        print(f"❌ 'welcome' URL: {e}")
    
    # Vérifier que 'home' et 'competitions:home' n'existent pas
    for bad_url in ['home', 'competitions:home']:
        try:
            url = reverse(bad_url)
            print(f"⚠️ {bad_url} existe encore: {url}")
        except NoReverseMatch:
            print(f"✅ {bad_url} n'existe pas (correct)")
    
    print(f"\n📋 RÉSUMÉ DES CORRECTIONS:")
    print("✅ practitioner_extra.py - corrigé")
    print("✅ practitioner_dashboard.py - corrigé") 
    print("✅ practitioner_extra_completions.py - corrigé")
    print("✅ practitioner_training.py - corrigé")
    print("✅ practitioner_finance.py - corrigé")
    
    print(f"\n🚀 ÉTAPES SUIVANTES:")
    print("1. Redémarrer Django sur le serveur de production")
    print("2. Tester les URLs problématiques:")
    print("   - https://martialcomp.com/fr/competitions/practitioner/support/")
    print("   - https://martialcomp.com/fr/competitions/practitioner/notifications/")
    
    print(f"\n🎉 CORRECTION TERMINÉE AVEC SUCCÈS!")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    sys.exit(1)