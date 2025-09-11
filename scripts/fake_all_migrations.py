"""
Script pour marquer toutes les migrations comme appliquées sans les exécuter.
"""
import os
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def fake_all_migrations():
    """Marque toutes les migrations comme appliquées sans les exécuter."""
    with connection.cursor() as cursor:
        # Liste des applications à traiter
        apps = [
            'multitenant',
        ]
        
        for app in apps:
            # Obtenir les migrations existantes dans les fichiers
            migrations_dir = os.path.join(os.getcwd(), app, 'migrations')
            if not os.path.exists(migrations_dir):
                print(f"Le répertoire {migrations_dir} n'existe pas.")
                continue
            
            migration_files = [f.replace('.py', '') for f in os.listdir(migrations_dir) 
                              if f.endswith('.py') and f != '__init__.py']
            
            # Obtenir les migrations déjà appliquées
            cursor.execute("""
                SELECT name FROM django_migrations
                WHERE app = %s
            """, [app])
            applied_migrations = [row[0] for row in cursor.fetchall()]
            
            # Marquer les migrations manquantes comme appliquées
            for migration in migration_files:
                if migration not in applied_migrations:
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied)
                        VALUES (%s, %s, NOW());
                    """, [app, migration])
                    print(f"Migration {app}.{migration} marquée comme appliquée.")
        
        print("\nToutes les migrations ont été marquées comme appliquées.")

if __name__ == "__main__":
    fake_all_migrations()
    print("\nMaintenant, exécutez:")
    print("python manage.py makemigrations")
    print("python manage.py migrate --fake")