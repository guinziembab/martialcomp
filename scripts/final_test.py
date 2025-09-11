#!/usr/bin/env python3
"""
Test final pour vérifier que tout fonctionne
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_final():
    print("🧪 TEST FINAL DU TEMPLATE TENANT")
    print("="*50)
    
    # Test 1: Domaine principal (localhost)
    print("1️⃣ Test domaine principal...")
    client = Client()
    response = client.get('/', HTTP_HOST='localhost:8000')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'MartialComp - La Plateforme Complète' in content:
            print("   ✅ Template welcome générique affiché")
        else:
            print("   ❓ Template non identifié")
    
    # Test 2: Sous-domaine tenant
    print("\n2️⃣ Test sous-domaine tenant...")
    response = client.get('/', HTTP_HOST='fed-federation-test-fix.localhost:8000')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Fédération d\'Arts Martiaux' in content:
            print("   ✅ Template fédération affiché!")
            print("   🎉 SUCCÈS! Le template personnalisé fonctionne!")
        elif 'federation-header' in content:
            print("   ✅ Éléments CSS fédération détectés!")
        elif 'MartialComp - La Plateforme Complète' in content:
            print("   ❌ Template welcome générique (problème non résolu)")
        else:
            print("   ❓ Template non identifié")
            # Afficher un extrait pour debug
            print(f"   Extrait: {content[:200]}...")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    test_final()