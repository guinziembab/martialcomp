"""
Script pour nettoyer les migrations problématiques de multitenant.
"""
import os
import shutil
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def clean_migrations():
    """Nettoie les migrations problématiques de multitenant."""
    # Chemin du répertoire des migrations
    migrations_dir = os.path.join(os.getcwd(), 'multitenant', 'migrations')
    
    # Migrations à conserver
    keep_migrations = [
        '__init__.py',
        '0001_initial.py',
        '0002_add_customization_fields.py',
        '0003_paymentmethod_tenantpayment_tenantsubscription_and_more.py',
        '0004_remove_tenant_logo_remove_tenant_primary_color_and_more.py',
        '0005_pricing_models.py',
        '0006_alter_featureusage_id_alter_payperusefeature_id_and_more.py',
    ]
    
    # Lister tous les fichiers de migration
    try:
        migration_files = os.listdir(migrations_dir)
    except FileNotFoundError:
        print(f"Le répertoire {migrations_dir} n'existe pas.")
        return
    
    # Sauvegarder puis supprimer les migrations problématiques
    backup_dir = os.path.join(os.getcwd(), 'multitenant_migrations_backup')
    os.makedirs(backup_dir, exist_ok=True)
    
    for filename in migration_files:
        if filename not in keep_migrations and filename.endswith('.py'):
            # Sauvegarder le fichier
            src_path = os.path.join(migrations_dir, filename)
            dst_path = os.path.join(backup_dir, filename)
            try:
                shutil.copy2(src_path, dst_path)
                print(f"Fichier sauvegardé: {filename}")
                
                # Supprimer le fichier original
                os.remove(src_path)
                print(f"Fichier supprimé: {filename}")
            except Exception as e:
                print(f"Erreur lors du traitement de {filename}: {e}")

if __name__ == "__main__":
    clean_migrations()
    print("\nNettoyage terminé. Maintenant, exécutez:")
    print("1. python manage.py migrate multitenant 0006")
    print("2. python manage.py makemigrations multitenant")
    print("3. python manage.py migrate")