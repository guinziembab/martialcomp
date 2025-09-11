#!/usr/bin/env python3
"""
Script de correction pour ajouter les colonnes manquantes à la table notifications
Exécutez ce script depuis le dossier racine du projet :
python add_notification_columns.py
"""

import os
import sys
import django

# Configuration de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def add_notification_columns():
    """Ajoute les colonnes manquantes à la table competitions_notification"""
    
    cursor = connection.cursor()
    
    # Liste des colonnes à ajouter avec leurs définitions
    columns_to_add = [
        ("notification_type", "VARCHAR(20) DEFAULT 'info'"),
        ("priority", "VARCHAR(20) DEFAULT 'standard'"),
        ("action_url", "VARCHAR(200)"),
        ("action_text", "VARCHAR(100)"),
        ("expires_at", "TIMESTAMP"),
    ]
    
    print("🔧 Correction de la table competitions_notification...")
    
    # Vérifier d'abord quelles colonnes existent déjà
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'competitions_notification' 
        AND table_schema = 'public'
    """)
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    print(f"📋 Colonnes existantes : {existing_columns}")
    
    # Ajouter les colonnes manquantes
    for column_name, column_definition in columns_to_add:
        if column_name not in existing_columns:
            try:
                sql = f"ALTER TABLE competitions_notification ADD COLUMN {column_name} {column_definition};"
                print(f"➕ Ajout de la colonne : {column_name}")
                cursor.execute(sql)
                print(f"✅ Colonne {column_name} ajoutée avec succès")
            except Exception as e:
                print(f"❌ Erreur lors de l'ajout de {column_name}: {e}")
        else:
            print(f"⏭️  Colonne {column_name} déjà présente")
    
    # Vérifier le résultat final
    cursor.execute("""
        SELECT column_name, data_type, column_default
        FROM information_schema.columns 
        WHERE table_name = 'competitions_notification' 
        AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    
    final_columns = cursor.fetchall()
    print("\n📊 Structure finale de la table :")
    for col_name, col_type, col_default in final_columns:
        default_info = f" (défaut: {col_default})" if col_default else ""
        print(f"  - {col_name}: {col_type}{default_info}")
    
    print("\n🎉 Correction terminée ! Vous pouvez maintenant redémarrer le serveur.")

if __name__ == "__main__":
    try:
        add_notification_columns()
    except Exception as e:
        print(f"💥 Erreur fatale : {e}")
        sys.exit(1)