"""
Script de résolution complète des problèmes de migration
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.db import connection, transaction
from django.db.migrations.recorder import MigrationRecorder

print("=== RÉSOLUTION COMPLÈTE DES MIGRATIONS ===")

def clean_migration_records():
    """Nettoie les enregistrements de migrations fantômes"""
    print("\n1. Nettoyage des migrations fantômes...")
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Supprimer les références aux migrations qui n'existent plus
                cursor.execute("""
                    DELETE FROM django_migrations 
                    WHERE app = 'competitions' 
                    AND (name = '0011_add_team_config_fields' 
                         OR name = '0012_merge_20251107_2026')
                """)
                deleted = cursor.rowcount
                
                if deleted > 0:
                    print(f"  ✓ {deleted} migration(s) fantôme(s) supprimée(s)")
                else:
                    print("  ✓ Aucune migration fantôme trouvée")
                    
    except Exception as e:
        print(f"  ✗ Erreur lors du nettoyage: {e}")
        return False
    return True

def check_migration_status():
    """Vérifie le statut de la migration 0011"""
    print("\n2. Vérification du statut de migration 0011...")
    try:
        recorder = MigrationRecorder(connection)
        applied = recorder.applied_migrations()
        
        if ('competitions', '0011_combat_configuration_enhanced') in applied:
            print("  ✓ Migration 0011_combat_configuration_enhanced déjà appliquée")
            return True
        else:
            print("  → Migration 0011_combat_configuration_enhanced à appliquer")
            return False
            
    except Exception as e:
        print(f"  ✗ Erreur: {e}")
        return None

def check_columns_exist():
    """Vérifie si les colonnes existent déjà dans la base"""
    print("\n3. Vérification des colonnes dans la base...")
    try:
        with connection.cursor() as cursor:
            # Vérifier une colonne clé de la migration
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = 'competitions_combatconfiguration'
                AND column_name = 'labels_points'
            """)
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                print("  ✓ Les colonnes de la migration semblent déjà présentes")
                return True
            else:
                print("  → Les colonnes de la migration ne sont pas encore créées")
                return False
                
    except Exception:
        print("  → Impossible de vérifier les colonnes")
        return None

def main():
    # Étape 1: Nettoyer
    if not clean_migration_records():
        print("\n❌ Échec du nettoyage. Arrêt.")
        return
    
    # Étape 2: Vérifier le statut
    migration_applied = check_migration_status()
    columns_exist = check_columns_exist()
    
    # Étape 3: Décider de l'action
    print("\n=== RECOMMANDATION ===")
    
    if migration_applied and columns_exist:
        print("✅ Tout semble en ordre! Les migrations sont appliquées et les colonnes existent.")
        print("\nVous pouvez maintenant exécuter:")
        print("  python test_combat_configs_simple.py")
        
    elif not migration_applied and not columns_exist:
        print("📝 La migration doit être appliquée.")
        print("\nExécutez:")
        print("  python manage.py migrate competitions")
        
    elif migration_applied and not columns_exist:
        print("⚠️  Incohérence détectée: migration marquée comme appliquée mais colonnes manquantes.")
        print("\nOptions:")
        print("  1. Forcer la ré-application: python manage.py migrate competitions --fake-initial")
        print("  2. Ou marquer comme non appliquée et réappliquer")
        
    elif not migration_applied and columns_exist:
        print("⚠️  Les colonnes existent mais la migration n'est pas marquée comme appliquée.")
        print("\nMarquer la migration comme appliquée:")
        print("  python manage.py migrate competitions 0011_combat_configuration_enhanced --fake")
    
    print("\n✅ Analyse terminée!")

if __name__ == "__main__":
    main()