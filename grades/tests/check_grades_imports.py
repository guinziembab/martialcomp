"""
Script pour vérifier les imports dans l'application grades
Exécuter avec: python manage.py shell < check_grades_imports.py
"""

import os
import re
import sys
from collections import defaultdict
from django.conf import settings

# Configuration
GRADES_APP_PATH = os.path.join(settings.BASE_DIR, 'grades')
COMPETITIONS_APP_PATH = os.path.join(settings.BASE_DIR, 'competitions')

# Couleurs pour le terminal
class TextColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(msg):
    print(f"{TextColors.OKGREEN}✓ {msg}{TextColors.ENDC}")

def print_warning(msg):
    print(f"{TextColors.WARNING}⚠ {msg}{TextColors.ENDC}")

def print_error(msg):
    print(f"{TextColors.FAIL}✗ {msg}{TextColors.ENDC}")

def print_header(msg):
    print(f"\n{TextColors.HEADER}{TextColors.BOLD}{msg}{TextColors.ENDC}")

def scan_imports(file_path):
    """Scan un fichier Python pour trouver les imports."""
    if not os.path.exists(file_path) or not file_path.endswith('.py'):
        return []
    
    imports = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Pattern pour les imports standard: import xxx
        import_pattern = r'^\s*import\s+([\w\.]+)'
        for match in re.finditer(import_pattern, content, re.MULTILINE):
            imports.append(match.group(1))
        
        # Pattern pour les imports from: from xxx import yyy
        from_pattern = r'^\s*from\s+([\w\.]+)\s+import\s+'
        for match in re.finditer(from_pattern, content, re.MULTILINE):
            imports.append(match.group(1))
    
    return imports

def check_circular_imports():
    """Vérifie les imports circulaires entre les applications grades et competitions."""
    print_header("Vérification des imports circulaires")
    
    # Scan de tous les fichiers Python dans les deux applications
    all_files = []
    
    # Fichiers de l'application grades
    if os.path.exists(GRADES_APP_PATH):
        for root, dirs, files in os.walk(GRADES_APP_PATH):
            for file in files:
                if file.endswith('.py'):
                    all_files.append(os.path.join(root, file))
    else:
        print_error(f"Le chemin de l'application grades n'existe pas: {GRADES_APP_PATH}")
    
    # Fichiers de l'application competitions
    if os.path.exists(COMPETITIONS_APP_PATH):
        for root, dirs, files in os.walk(COMPETITIONS_APP_PATH):
            for file in files:
                if file.endswith('.py'):
                    all_files.append(os.path.join(root, file))
    else:
        print_error(f"Le chemin de l'application competitions n'existe pas: {COMPETITIONS_APP_PATH}")
    
    # Dictionnaire pour stocker les imports par fichier
    file_imports = {}
    
    # Scan des imports dans chaque fichier
    for file_path in all_files:
        imports = scan_imports(file_path)
        relative_path = os.path.relpath(file_path, settings.BASE_DIR)
        file_imports[relative_path] = imports
    
    # Vérifier les imports circulaires
    grades_to_competitions = defaultdict(list)
    competitions_to_grades = defaultdict(list)
    
    for file_path, imports in file_imports.items():
        if 'grades/' in file_path:
            for imp in imports:
                if imp.startswith('competitions'):
                    grades_to_competitions[file_path].append(imp)
        elif 'competitions/' in file_path:
            for imp in imports:
                if imp.startswith('grades'):
                    competitions_to_grades[file_path].append(imp)
    
    # Afficher les résultats
    if grades_to_competitions:
        print_header("Imports de competitions dans grades")
        for file, imports in grades_to_competitions.items():
            for imp in imports:
                print(f"{file} → {imp}")
    else:
        print_success("Aucun import de competitions dans grades")
    
    if competitions_to_grades:
        print_header("Imports de grades dans competitions")
        for file, imports in competitions_to_grades.items():
            for imp in imports:
                print(f"{file} → {imp}")
    else:
        print_success("Aucun import de grades dans competitions")
    
    # Détecter les imports circulaires potentiels
    circular_imports = []
    for grades_file, comp_imports in grades_to_competitions.items():
        for comp_file, grades_imports in competitions_to_grades.items():
            # Obtenir le module de base pour chaque fichier
            grades_module = os.path.splitext(os.path.basename(grades_file))[0]
            comp_module = os.path.splitext(os.path.basename(comp_file))[0]
            
            # Vérifier si les imports pointent les uns vers les autres
            for comp_import in comp_imports:
                if comp_module in comp_import:
                    for grades_import in grades_imports:
                        if grades_module in grades_import:
                            circular_imports.append((grades_file, comp_file))
                            break
    
    if circular_imports:
        print_header("Imports circulaires détectés")
        for grades_file, comp_file in circular_imports:
            print_error(f"{grades_file} ↔ {comp_file}")
            print("   Suggestion: Utilisez des imports à l'intérieur des fonctions/méthodes au lieu de imports au niveau du module")
    else:
        print_success("Aucun import circulaire détecté")

def check_import_usage():
    """Vérifie comment les imports sont utilisés dans les fichiers de l'application grades."""
    print_header("Analyse des imports dans l'application grades")
    
    if not os.path.exists(GRADES_APP_PATH):
        print_error(f"Le chemin de l'application grades n'existe pas: {GRADES_APP_PATH}")
        return
    
    # Scan de tous les fichiers Python dans l'application grades
    all_files = []
    for root, dirs, files in os.walk(GRADES_APP_PATH):
        for file in files:
            if file.endswith('.py'):
                all_files.append(os.path.join(root, file))
    
    for file_path in all_files:
        relative_path = os.path.relpath(file_path, settings.BASE_DIR)
        print(f"\nFichier: {relative_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Vérifier les imports de competitions
            comp_imports = re.findall(r'from competitions\.(.*?) import', content)
            if comp_imports:
                print(f"  Imports de competitions:")
                for imp in comp_imports:
                    print(f"    - competitions.{imp}")
            
            # Vérifier les imports circulaires potentiels
            function_imports = re.findall(r'def [^:]+:\s+.*?from (competitions|grades)', content, re.DOTALL)
            if function_imports:
                print_success("  Imports à l'intérieur des fonctions (bonne pratique pour éviter les imports circulaires)")
            
            # Vérifier si les imports de competitions sont dans des fonctions
            comp_imports_in_function = re.findall(r'def [^:]+:\s+.*?from competitions', content, re.DOTALL)
            if comp_imports and not comp_imports_in_function:
                print_warning("  Les imports de competitions sont au niveau du module, ce qui peut causer des imports circulaires")
                print("    Suggestion: Déplacez ces imports à l'intérieur des fonctions où ils sont utilisés")

def check_model_dependencies():
    """Vérifie les dépendances entre les modèles des deux applications."""
    print_header("Analyse des dépendances entre modèles")
    
    grades_models_path = os.path.join(GRADES_APP_PATH, 'models.py')
    competitions_models_path = os.path.join(COMPETITIONS_APP_PATH, 'models.py')
    competitions_models_dir = os.path.join(COMPETITIONS_APP_PATH, 'models')
    
    grades_models_dependencies = []
    competitions_models_dependencies = []
    
    # Vérifier le fichier models.py de grades
    if os.path.exists(grades_models_path):
        with open(grades_models_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Rechercher les références à competitions.models
            for match in re.finditer(r'(competitions\.models\.[A-Za-z]+)', content):
                grades_models_dependencies.append(match.group(1))
    else:
        print_warning(f"Le fichier models.py n'existe pas dans l'application grades: {grades_models_path}")
    
    # Vérifier le fichier models.py de competitions
    if os.path.exists(competitions_models_path):
        with open(competitions_models_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Rechercher les références à grades.models
            for match in re.finditer(r'(grades\.models\.[A-Za-z]+)', content):
                competitions_models_dependencies.append(match.group(1))
    
    # Vérifier le dossier models de competitions
    if os.path.exists(competitions_models_dir):
        for file in os.listdir(competitions_models_dir):
            if file.endswith('.py'):
                with open(os.path.join(competitions_models_dir, file), 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Rechercher les références à grades.models
                    for match in re.finditer(r'(grades\.models\.[A-Za-z]+)', content):
                        competitions_models_dependencies.append(match.group(1))
    
    # Afficher les résultats
    if grades_models_dependencies:
        print("Dépendances des modèles grades vers competitions:")
        for dep in grades_models_dependencies:
            print(f"  - {dep}")
    else:
        print_success("Aucune dépendance des modèles grades vers competitions")
    
    if competitions_models_dependencies:
        print("\nDépendances des modèles competitions vers grades:")
        for dep in competitions_models_dependencies:
            print(f"  - {dep}")
    else:
        print_success("Aucune dépendance des modèles competitions vers grades")
    
    # Recommandations
    if grades_models_dependencies and competitions_models_dependencies:
        print_warning("\nDépendances circulaires détectées entre les modèles des deux applications")
        print("Recommandations:")
        print("1. Utilisez des références de chaîne pour les ForeignKey/ManyToMany (ex: 'competitions.Discipline')")
        print("2. Placez des fonctions d'adaptation ou des proxys dans une application tierce")
        print("3. Utilisez le pattern médiateur pour éviter les dépendances directes")
    elif grades_models_dependencies:
        print_success("\nLa structure de dépendance est unidirectionnelle (grades dépend de competitions), ce qui est bon")
    elif competitions_models_dependencies:
        print_warning("\nLa structure de dépendance est inversée (competitions dépend de grades)")
        print("C'est généralement préférable que l'application principale (competitions) ne dépende pas de l'application secondaire (grades)")

def check_apps_config():
    """Vérifie la configuration des applications dans settings.py et apps.py."""
    print_header("Vérification de la configuration des applications")
    
    # Vérifier que grades est bien dans INSTALLED_APPS
    if 'grades' in settings.INSTALLED_APPS or 'grades.apps.GradesConfig' in settings.INSTALLED_APPS:
        print_success("L'application 'grades' est correctement présente dans INSTALLED_APPS")
    else:
        print_error("L'application 'grades' n'est PAS dans INSTALLED_APPS")
        print("Ajoutez 'grades' ou 'grades.apps.GradesConfig' à la liste INSTALLED_APPS dans settings.py")
    
    # Vérifier le fichier apps.py
    apps_path = os.path.join(GRADES_APP_PATH, 'apps.py')
    if os.path.exists(apps_path):
        with open(apps_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'class GradesConfig' in content and 'name = ' in content:
                print_success("Le fichier apps.py est correctement configuré")
            else:
                print_warning("Le fichier apps.py pourrait ne pas être correctement configuré")
                print("Assurez-vous qu'il contient une classe GradesConfig avec un attribut name")
    else:
        print_warning(f"Le fichier apps.py n'existe pas dans l'application grades: {apps_path}")

def check_urls_config():
    """Vérifie la configuration des URLs pour l'application grades."""
    print_header("Vérification de la configuration des URLs")
    
    # Vérifier le fichier urls.py de l'application grades
    grades_urls_path = os.path.join(GRADES_APP_PATH, 'urls.py')
    if os.path.exists(grades_urls_path):
        with open(grades_urls_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if 'app_name = ' in content:
                print_success("Le fichier urls.py a un app_name défini")
            else:
                print_warning("Le fichier urls.py n'a pas d'app_name défini")
                print("Ajoutez 'app_name = \"grades\"' pour éviter les conflits de noms d'URL")
            
            url_patterns = re.findall(r'path\([\'"]([^\'"]+)[\'"]', content)
            print(f"Trouvé {len(url_patterns)} patterns d'URL dans grades/urls.py")
    else:
        print_error(f"Le fichier urls.py n'existe pas dans l'application grades: {grades_urls_path}")
        print("Créez un fichier urls.py avec les routes pour votre application grades")
    
    # Vérifier l'inclusion dans les URLs principales
    main_urls_path = os.path.join(settings.BASE_DIR, 'martialcomp', 'urls.py')
    if os.path.exists(main_urls_path):
        with open(main_urls_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            if re.search(r'include\([\'"]grades\.urls[\'"]', content):
                print_success("Les URLs de grades sont incluses dans les URLs principales")
            else:
                print_error("Les URLs de grades ne sont PAS incluses dans les URLs principales")
                print("Ajoutez: path('grades/', include('grades.urls', namespace='grades')), dans votre fichier urls.py principal")
    else:
        print_warning(f"Le fichier d'URLs principal n'a pas été trouvé: {main_urls_path}")

def main():
    """Fonction principale"""
    print(f"{TextColors.BOLD}VÉRIFICATION DE L'APPLICATION GRADES{TextColors.ENDC}")
    print(f"Base dir: {settings.BASE_DIR}")
    print(f"Grades app path: {GRADES_APP_PATH}")
    print(f"Competitions app path: {COMPETITIONS_APP_PATH}")
    
    # Réaliser toutes les vérifications
    check_circular_imports()
    check_import_usage()
    check_model_dependencies()
    check_apps_config()
    check_urls_config()
    
    print(f"\n{TextColors.BOLD}RECOMMANDATIONS FINALES{TextColors.ENDC}")
    print("""
1. Évitez les imports circulaires en:
   - Utilisant des imports à l'intérieur des fonctions/méthodes
   - Préférant les références par chaîne dans les ForeignKey ('app.Model')
   - Plaçant le code de liaison dans une application tierce si nécessaire

2. Structure d'applications:
   - L'application principale (competitions) ne devrait pas dépendre de l'application secondaire (grades)
   - L'application secondaire (grades) peut dépendre de l'application principale

3. Configuration:
   - Assurez-vous que 'grades' est dans INSTALLED_APPS
   - Vérifiez que les URLs sont correctement configurées
   - Définissez app_name dans urls.py

4. Migrations:
   - Appliquez les migrations dans le bon ordre: d'abord competitions, puis grades
   - En cas de problème, utilisez --fake-initial pour les migrations qui échouent
    """)

if __name__ == "__main__":
    main()