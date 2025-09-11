#!/usr/bin/env python3
"""
Script de validation post-déploiement pour la production
Vérifie que les corrections sont bien appliquées
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.db import transaction

def check_database_schema():
    """Vérifie que les champs de la base de données sont correctement configurés"""
    print("🔍 VÉRIFICATION DU SCHÉMA DE BASE DE DONNÉES")
    print("=" * 45)
    
    try:
        with connection.cursor() as cursor:
            # Vérifier la structure de la table practitioners
            cursor.execute("""
                SELECT column_name, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'competitions_practitioner' 
                AND column_name IN ('family_role', 'family_emergency_contact')
                ORDER BY column_name;
            """)
            
            results = cursor.fetchall()
            
            if results:
                print("✅ Champs famille trouvés dans la base de données:")
                for column_name, is_nullable, column_default in results:
                    nullable_status = "✅ NULL autorisé" if is_nullable == 'YES' else "❌ NULL non autorisé"
                    print(f"   {column_name}: {nullable_status}")
                    if column_default:
                        print(f"      Défaut: {column_default}")
                
                # Vérifier que les deux champs acceptent NULL
                null_fields = [row for row in results if row[1] == 'YES']
                if len(null_fields) == 2:
                    print("\n🎉 SCHÉMA CORRECT: Les deux champs acceptent NULL")
                    return True
                else:
                    print(f"\n⚠️  PROBLÈME: Seulement {len(null_fields)}/2 champs acceptent NULL")
                    return False
            else:
                print("❌ Aucun champ famille trouvé dans la base de données")
                return False
                
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du schéma: {e}")
        return False

def test_practitioner_creation():
    """Teste la création d'un pratiquant avec des champs famille vides"""
    print("\n🧪 TEST DE CRÉATION DE PRATIQUANT")
    print("=" * 35)
    
    try:
        from competitions.models.practitioners import Practitioner
        from organizations.models import Organization
        from datetime import date
        
        # Récupérer une organisation
        org = Organization.objects.first()
        if not org:
            print("❌ Aucune organisation trouvée pour le test")
            return False
        
        print(f"📋 Organisation utilisée: {org.name}")
        
        # Test avec des champs famille vides
        with transaction.atomic():
            practitioner = Practitioner.objects.create(
                first_name="Test",
                last_name="Production",
                birth_date=date(1990, 1, 1),
                gender="male",
                organization=org,
                family_role="",  # Chaîne vide
                family_emergency_contact=""  # Chaîne vide
            )
            
            print(f"✅ Pratiquant créé avec succès: {practitioner.full_name}")
            print(f"   ID: {practitioner.id}")
            
            # Vérifier les valeurs dans la base
            practitioner.refresh_from_db()
            
            family_role_ok = practitioner.family_role in [None, '']
            family_contact_ok = practitioner.family_emergency_contact in [None, '']
            
            if family_role_ok and family_contact_ok:
                print("✅ Champs famille correctement gérés")
                
                # Nettoyer le test
                practitioner.delete()
                print("🧹 Pratiquant de test supprimé")
                return True
            else:
                print(f"⚠️  Valeurs inattendues:")
                print(f"   family_role: '{practitioner.family_role}'")
                print(f"   family_emergency_contact: '{practitioner.family_emergency_contact}'")
                
                practitioner.delete()
                return False
                
    except Exception as e:
        print(f"❌ ERREUR lors du test: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        
        # Vérifier si c'est l'ancienne erreur PostgreSQL
        if "invalid input syntax for type boolean" in str(e):
            print("💥 L'ANCIENNE ERREUR PERSISTE - La correction n'a pas été appliquée correctement")
        
        return False

def check_migrations():
    """Vérifie que les migrations ont été appliquées"""
    print("\n📋 VÉRIFICATION DES MIGRATIONS")
    print("=" * 30)
    
    try:
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connections
        
        executor = MigrationExecutor(connections['default'])
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print("⚠️  Migrations en attente:")
            for migration, backwards in plan:
                print(f"   - {migration}")
            return False
        else:
            print("✅ Toutes les migrations sont appliquées")
            
            # Vérifier spécifiquement notre migration
            applied_migrations = executor.loader.applied_migrations
            our_migration = ('competitions', '0008_fix_family_fields_null')
            
            if our_migration in applied_migrations:
                print("✅ Migration 0008_fix_family_fields_null appliquée")
                return True
            else:
                print("❌ Migration 0008_fix_family_fields_null NON appliquée")
                return False
                
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des migrations: {e}")
        return False

def main():
    print("🚀 VALIDATION POST-DÉPLOIEMENT PRODUCTION")
    print("=" * 45)
    print("🎯 Objectif: Vérifier que les corrections sont appliquées")
    print("📋 Tests: Schéma BD + Migrations + Création pratiquant")
    print()
    
    # Tests de validation
    schema_ok = check_database_schema()
    migrations_ok = check_migrations()
    creation_ok = test_practitioner_creation()
    
    print("\n" + "=" * 45)
    print("📊 RÉSUMÉ DE LA VALIDATION")
    print("=" * 25)
    
    results = [
        ("Schéma base de données", schema_ok),
        ("Migrations appliquées", migrations_ok),
        ("Création pratiquant", creation_ok)
    ]
    
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{status} - {test_name}")
    
    all_success = all(result[1] for result in results)
    
    print("\n" + "=" * 45)
    
    if all_success:
        print("🎉 VALIDATION COMPLÈTE RÉUSSIE!")
        print("✅ Toutes les corrections sont correctement appliquées")
        print("✅ L'erreur PostgreSQL 'invalid input syntax for type boolean' est résolue")
        print()
        print("📋 ÉTAPES SUIVANTES:")
        print("1. 🧪 Tester l'ajout d'un pratiquant via l'interface web")
        print("2. 📊 Surveiller les logs d'application")
        print("3. ✅ Valider le fonctionnement complet")
        
    else:
        print("⚠️  VALIDATION PARTIELLE OU ÉCHOUÉE")
        print("❌ Certaines corrections ne sont pas correctement appliquées")
        print()
        print("🔧 ACTIONS RECOMMANDÉES:")
        print("1. Vérifier les logs de migration")
        print("2. Contrôler que tous les fichiers ont été copiés")
        print("3. Réappliquer les migrations si nécessaire")
        print("4. Contacter le support technique si le problème persiste")
    
    print(f"\n📁 Logs détaillés disponibles dans les journaux système")
    print("🔍 Commande de surveillance: sudo journalctl -u martialcomp -f")

if __name__ == "__main__":
    main()