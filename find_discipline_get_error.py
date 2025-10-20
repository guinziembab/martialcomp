#!/usr/bin/env python
"""
Trouve l'origine exacte de l'appel Discipline.objects.get()
"""
import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

def trace_discipline_get():
    """Trace l'origine de l'erreur"""
    print("🔍 TRAÇAGE DE L'ERREUR DISCIPLINE.OBJECTS.GET()")
    print("=" * 60)
    
    # Monkey patch pour tracer les appels
    from apps.competitions.models import Discipline
    original_get = Discipline.objects.get
    
    def traced_get(*args, **kwargs):
        print("\n⚠️  APPEL DÉTECTÉ: Discipline.objects.get()")
        print(f"   Args: {args}")
        print(f"   Kwargs: {kwargs}")
        print("   Stack trace:")
        for line in traceback.format_stack()[-10:-1]:
            print(f"   {line.strip()}")
        
        # Appeler l'original pour voir l'erreur
        try:
            return original_get(*args, **kwargs)
        except Exception as e:
            print(f"   ❌ ERREUR: {e}")
            raise
    
    Discipline.objects.get = traced_get
    
    # Tenter de charger l'admin
    try:
        from django.contrib import admin
        from django.urls import reverse
        from django.test import Client
        
        print("\n📋 SIMULATION DE L'ACCÈS ADMIN")
        
        # Simuler une requête
        client = Client()
        response = client.get('/fr/admin/competitions/practitioner/', follow=False)
        print(f"Response status: {response.status_code}")
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    trace_discipline_get()