# diagnostic_grades.py
import os
import sys
import django

# Configurer l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')  # Ajustez selon le nom de votre module de paramètres
django.setup()

from django.apps import apps
from django.db import models, connection
from pprint import pprint

# Configuration initiale
print("=== Diagnostic du système de grades ===\n")
print(f"Django version: {django.get_version()}")
print(f"Python version: {sys.version}")

# Vérifier la présence du modèle GradeSystem
print("\n=== Recherche du modèle GradeSystem ===")
model_found = False

for app_config in apps.get_app_configs():
    for model in app_config.get_models():
        if model.__name__ == 'GradeSystem':
            model_found = True
            print(f"✅ Modèle GradeSystem trouvé dans l'application: {app_config.label}")
            print(f"   Chemin: {model.__module__}")
            
            # Afficher la structure du modèle
            print("\n== Structure du modèle ==")
            for field in model._meta.fields:
                print(f"   - {field.name}: {field.__class__.__name__}")
            
            # Relations
            print("\n== Relations ==")
            for rel in model._meta.related_objects:
                print(f"   - {rel.name} ({rel.__class__.__name__}) de {rel.model.__name__}")
            
            # Essayer de compter les objets
            try:
                count = model.objects.count()
                print(f"\n== Nombre d'instances: {count} ==")
                
                # Lister quelques exemples
                if count > 0:
                    print("\n== Quelques exemples ==")
                    for instance in model.objects.all()[:5]:
                        print(f"   - ID: {instance.id}, {instance}")
            except Exception as e:
                print(f"\n❌ Erreur lors du comptage des objets: {e}")

if not model_found:
    print("❌ Modèle GradeSystem non trouvé")
    
    # Explorer les tables pour trouver des tables liées aux grades
    print("\n=== Tables possiblement liées aux grades ===")
    tables = connection.introspection.table_names()
    grade_tables = [table for table in tables if 'grade' in table.lower()]
    
    if grade_tables:
        for table in grade_tables:
            print(f"Table: {table}")
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM {connection.ops.quote_name(table)} LIMIT 0")
            description = cursor.description
            if description:
                columns = [col[0] for col in description]
                print(f"   Colonnes: {', '.join(columns)}")
    else:
        print("   Aucune table avec 'grade' dans le nom n'a été trouvée")

# Vérifier les disciplines et leurs systèmes de grades associés
print("\n=== Disciplines et leurs systèmes de grades ===")
try:
    Discipline = apps.get_model('competitions', 'Discipline')
    print(f"✅ Modèle Discipline trouvé")
    disciplines = Discipline.objects.all()
    print(f"   Nombre de disciplines: {disciplines.count()}")
    
    for discipline in disciplines[:10]:  # Limiter à 10 pour la lisibilité
        print(f"\n   - {discipline.name}")
        
        # Recherche d'un système de grades lié à cette discipline
        for app_config in apps.get_app_configs():
            for model in app_config.get_models():
                if model.__name__ == 'GradeSystem' or 'grade' in model.__name__.lower():
                    try:
                        # Essayer de trouver une relation avec discipline
                        for field in model._meta.fields:
                            if isinstance(field, models.ForeignKey) and field.related_model == Discipline:
                                grades = model.objects.filter(**{field.name: discipline})
                                if grades.exists():
                                    print(f"     ✅ {grades.count()} grades trouvés dans {model.__name__}")
                                    for grade in grades[:5]:  # Limiter à 5 pour la lisibilité
                                        print(f"       - {grade}")
                    except Exception as e:
                        print(f"     ❌ Erreur: {e}")
        
except Exception as e:
    print(f"❌ Erreur lors de la vérification des disciplines: {e}")

# Vérifier s'il existe des tables liées aux grades qui n'ont pas de modèle correspondant
print("\n=== Tables dans la base de données liées aux grades ===")
tables = connection.introspection.table_names()
grade_tables = [table for table in tables if 'grade' in table.lower()]
if grade_tables:
    print(f"Tables trouvées: {len(grade_tables)}")
    for table in grade_tables:
        print(f"- {table}")
        # Obtenir la structure de la table
        cursor = connection.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table})")  # SQLite
            columns = cursor.fetchall()
            print(f"  Colonnes: {[col[1] for col in columns]}")
        except:
            try:
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")  # PostgreSQL
                columns = cursor.fetchall()
                print(f"  Colonnes: {[col[0] for col in columns]}")
            except Exception as e:
                print(f"  Impossible d'obtenir les colonnes: {e}")
else:
    print("Aucune table avec 'grade' dans le nom n'a été trouvée")

print("\n=== Fin du diagnostic ===")