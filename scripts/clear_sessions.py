#!/usr/bin/env python3
"""
Script pour vider les sessions Django
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_minimal_translation')
django.setup()

from django.contrib.sessions.models import Session

def clear_sessions():
    print("🧹 NETTOYAGE DES SESSIONS")
    print("=" * 40)
    
    # Compter les sessions existantes
    session_count = Session.objects.count()
    print(f"Sessions existantes: {session_count}")
    
    # Supprimer toutes les sessions
    Session.objects.all().delete()
    
    print("✅ Toutes les sessions supprimées")
    print("\n💡 Essayez maintenant de vous connecter!")

if __name__ == '__main__':
    clear_sessions()