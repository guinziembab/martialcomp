# 1. Lancez le shell Django
python manage.py shell

# 2. Vérifier si la classe GradeSystem existe
from django.apps import apps
try:
    GradeSystem = apps.get_model('competitions', 'GradeSystem')
    print(f"Le modèle GradeSystem existe dans l'application competitions")
except LookupError:
    print("Le modèle GradeSystem n'existe pas dans l'application competitions")
    # Essayez de trouver le modèle dans d'autres applications
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            if model.__name__ == 'GradeSystem':
                print(f"Trouvé GradeSystem dans l'application {app_config.label}")

# 3. Si vous savez dans quelle application se trouve le modèle, importez-le directement
# Par exemple, si le modèle est dans une application 'grades':
try:
    from grades.models import GradeSystem
    print("Le modèle GradeSystem a été importé avec succès depuis grades.models")
except ImportError:
    print("Impossible d'importer GradeSystem depuis grades.models")

# 4. Lister tous les systèmes de grades
try:
    systems = GradeSystem.objects.all()
    print(f"Nombre de systèmes de grades: {systems.count()}")
    for system in systems:
        print(f"ID: {system.id}, Discipline: {system.discipline}, Nom: {system.name}")
except NameError:
    print("Erreur: GradeSystem n'est pas défini")

# 5. Vérifier les grades pour une discipline spécifique
try:
    from competitions.models import Discipline
    discipline = Discipline.objects.get(name="Qwan Ki Do")  # Remplacez par le nom d'une discipline que vous avez
    
    # Essayez de trouver les systèmes de grades liés à cette discipline
    if 'GradeSystem' in globals():
        grades = GradeSystem.objects.filter(discipline=discipline)
        print(f"Grades pour {discipline.name}: {grades.count()}")
        for grade in grades:
            print(f"- {grade.name}")
except Exception as e:
    print(f"Erreur: {e}")

# 6. Explorer la structure des tables dans la base de données
from django.db import connection
tables = connection.introspection.table_names()
print("Tables dans la base de données:")
for table in tables:
    if 'grade' in table.lower():
        print(f"- {table}")
        cursor = connection.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")