#!/usr/bin/env python3
"""
Script direct pour ajouter la colonne send_at manquante
"""

import os
import sys

# Ajouter le chemin du projet
project_path = '/mnt/c/martial_hub_django/martialcomp'
sys.path.insert(0, project_path)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection

def add_missing_columns():
    """Ajoute directement les colonnes manquantes"""
    print("🔧 AJOUT DIRECT DE LA COLONNE send_at")
    print("=" * 45)
    
    with connection.cursor() as cursor:
        # Commandes SQL directes
        sql_commands = [
            "ALTER TABLE competitions_eventreminder ADD COLUMN IF NOT EXISTS send_at timestamp with time zone;",
            "ALTER TABLE competitions_eventreminder ADD COLUMN IF NOT EXISTS sent_at timestamp with time zone;", 
            "ALTER TABLE competitions_eventreminder ADD COLUMN IF NOT EXISTS is_sent boolean DEFAULT false;",
            "ALTER TABLE competitions_eventreminder ADD COLUMN IF NOT EXISTS reminder_type varchar(50) DEFAULT 'EMAIL';",
        ]
        
        for i, sql in enumerate(sql_commands, 1):
            try:
                cursor.execute(sql)
                print(f"{i}. ✅ {sql}")
            except Exception as e:
                print(f"{i}. ⚠️ {sql} - Erreur: {e}")
        
        # Vérification finale
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'competitions_eventreminder'
            AND column_name IN ('send_at', 'sent_at', 'is_sent', 'reminder_type')
            ORDER BY column_name;
        """)
        
        found_columns = [row[0] for row in cursor.fetchall()]
        print(f"\n📋 Colonnes ajoutées: {found_columns}")
        
        return len(found_columns) >= 3  # Au minimum send_at, sent_at, is_sent

def test_event_deletion():
    """Test la suppression d'événement après correction"""
    print(f"\n🧪 TEST DE SUPPRESSION D'ÉVÉNEMENT")
    
    try:
        from competitions.models.event import Event
        
        # Créer un événement test
        test_event = Event.objects.create(
            name="Test Suppression Urgent",
            description="Test après ajout colonne send_at",
            event_type="TRAINING",
            status="DRAFT"
        )
        event_id = test_event.id
        print(f"✅ Événement créé: {event_id}")
        
        # Tenter la suppression (ceci causait l'erreur)
        test_event.delete()
        print("✅ Suppression réussie!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    print("🚨 CORRECTION URGENTE - ERREUR send_at")
    print("=" * 50)
    
    # Étape 1: Ajouter les colonnes
    if add_missing_columns():
        print("✅ Colonnes ajoutées avec succès")
        
        # Étape 2: Tester
        if test_event_deletion():
            print("\n🎉 PROBLÈME RÉSOLU!")
            print("✅ La colonne send_at a été ajoutée")
            print("✅ La suppression d'événements fonctionne")
        else:
            print("\n⚠️ Colonnes ajoutées mais des erreurs persistent")
    else:
        print("❌ Échec de l'ajout des colonnes")
    
    print("\nScript terminé.")