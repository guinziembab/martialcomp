"""
Script de débogage pour l'application grades dans MartialComp
Exécuter avec: python manage.py shell < debug_grades_app.py
"""

import sys
import os
import importlib
import django
from django.apps import apps
from django.db import connection
from django.core.management.color import color_style
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.template.loader import get_template
from django.template.exceptions import TemplateDoesNotExist

style = color_style()
print(style.SUCCESS("\n=== Débogage de l'application grades ===\n"))

# 1. Vérifier si l'application est installée
print("1. Vérification de l'installation:")
try:
    if 'grades' in settings.INSTALLED_APPS:
        print(style.SUCCESS("✓ L'application 'grades' est dans INSTALLED_APPS"))
    else:
        print(style.ERROR("✗ L'application 'grades' n'est PAS dans INSTALLED_APPS"))
        print("   Ajoutez 'grades' à la liste INSTALLED_APPS dans settings.py")
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des applications installées: {e}"))

# 2. Vérifier si les modèles sont enregistrés
print("\n2. Vérification des modèles:")
try:
    from grades.models import Grade, GradeCategory, PractitionerGrade, GradeRequirement, GradeExam, GradeExamRegistration
    
    models_to_check = [
        ('Grade', Grade),
        ('GradeCategory', GradeCategory),
        ('PractitionerGrade', PractitionerGrade),
        ('GradeRequirement', GradeRequirement),
        ('GradeExam', GradeExam),
        ('GradeExamRegistration', GradeExamRegistration)
    ]
    
    for model_name, model_class in models_to_check:
        if model_class._meta.app_label == 'grades':
            print(style.SUCCESS(f"✓ Modèle {model_name} correctement enregistré"))
        else:
            print(style.ERROR(f"✗ Modèle {model_name} n'est pas enregistré dans l'application 'grades'"))
            
    # Vérifier les tables dans la base de données
    with connection.cursor() as cursor:
        for model_name, model_class in models_to_check:
            table_name = model_class._meta.db_table
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(style.SUCCESS(f"✓ Table {table_name} existe dans la base de données ({count} enregistrements)"))
            except Exception as e:
                print(style.ERROR(f"✗ Table {table_name} n'existe pas dans la base de données: {e}"))
                print("   Avez-vous exécuté les migrations?")

except ImportError as e:
    print(style.ERROR(f"✗ Erreur d'importation des modèles: {e}"))
    print("   Vérifiez la structure de vos modèles et les imports")
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des modèles: {e}"))

# 3. Vérifier les relations avec l'application competitions
print("\n3. Vérification des relations avec l'application competitions:")
try:
    from competitions.models import Discipline, Practitioner, Club
    
    # Vérifier si les modèles de competitions existent
    models_to_check = [
        ('Discipline', Discipline),
        ('Practitioner', Practitioner),
        ('Club', Club)
    ]
    
    for model_name, model_class in models_to_check:
        if model_class._meta.app_label == 'competitions':
            print(style.SUCCESS(f"✓ Modèle {model_name} correctement importé depuis competitions"))
        else:
            print(style.ERROR(f"✗ Problème avec le modèle {model_name}"))
            
    # Vérifier les relations
    print("\nVérification des relations entre modèles:")
    try:
        grade = Grade._meta.get_field('discipline').remote_field.model
        print(style.SUCCESS(f"✓ Relation Grade -> Discipline configurée correctement"))
    except Exception as e:
        print(style.ERROR(f"✗ Problème avec la relation Grade -> Discipline: {e}"))
    
    try:
        pg = PractitionerGrade._meta.get_field('practitioner').remote_field.model
        print(style.SUCCESS(f"✓ Relation PractitionerGrade -> Practitioner configurée correctement"))
    except Exception as e:
        print(style.ERROR(f"✗ Problème avec la relation PractitionerGrade -> Practitioner: {e}"))
        
except ImportError as e:
    print(style.ERROR(f"✗ Erreur d'importation des modèles competitions: {e}"))
    print("   Vérifiez que l'application competitions est bien installée")
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des relations: {e}"))

# 4. Vérifier les vues et formulaires
print("\n4. Vérification des vues et formulaires:")
try:
    from grades.views import (
        GradeListView, GradeDetailView, GradeCreateView, GradeUpdateView, GradeDeleteView,
        practitioner_grades, add_practitioner_grade, edit_practitioner_grade, bulk_grade_assignment
    )
    from grades.forms import (
        GradeForm, PractitionerGradeForm, GradeCategoryForm, BulkGradeAssignmentForm
    )
    
    print(style.SUCCESS("✓ Vues principales correctement importées"))
    print(style.SUCCESS("✓ Formulaires principaux correctement importés"))
    
except ImportError as e:
    print(style.ERROR(f"✗ Erreur d'importation des vues ou formulaires: {e}"))
    print("   Vérifiez la structure de vos vues et formulaires")
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des vues et formulaires: {e}"))

# 5. Vérifier les URLs
print("\n5. Vérification des URLs:")
try:
    if 'grades.urls' in str(settings.ROOT_URLCONF):
        print(style.SUCCESS("✓ URLs de l'application grades incluses dans les URLs principales"))
    else:
        try:
            from martialcomp.urls import urlpatterns
            grades_found = False
            for pattern in urlpatterns:
                if hasattr(pattern, 'app_name') and pattern.app_name == 'grades':
                    grades_found = True
                    break
                elif hasattr(pattern, 'namespace') and pattern.namespace == 'grades':
                    grades_found = True
                    break
                elif 'grades' in str(pattern):
                    grades_found = True
                    break
            
            if grades_found:
                print(style.SUCCESS("✓ URLs de l'application grades incluses dans les URLs principales"))
            else:
                print(style.ERROR("✗ URLs de l'application grades NON incluses dans les URLs principales"))
                print("   Ajoutez: path('grades/', include('grades.urls', namespace='grades')), dans votre fichier urls.py principal")
        except ImportError:
            print(style.ERROR("✗ Impossible d'importer les URLs principales"))
        
    # Vérifier les patterns d'URL spécifiques
    try:
        from grades.urls import urlpatterns as grades_urlpatterns
        print(style.SUCCESS(f"✓ {len(grades_urlpatterns)} patterns d'URL trouvés dans grades.urls"))
        
        # Tester quelques URLs
        test_urls = [
            'grade_list',
            'grade_detail',
            'grade_create',
            'practitioner_grades',
            'bulk_assignment'
        ]
        
        for url_name in test_urls:
            try:
                full_url_name = f'grades:{url_name}'
                if url_name == 'grade_detail' or url_name == 'practitioner_grades':
                    # Ces URLs nécessitent un argument pk
                    url = reverse(full_url_name, kwargs={'pk': 1})
                else:
                    url = reverse(full_url_name)
                print(style.SUCCESS(f"✓ URL {full_url_name} correctement configurée: {url}"))
            except NoReverseMatch:
                print(style.ERROR(f"✗ URL {full_url_name} non trouvée"))
            except Exception as e:
                print(style.ERROR(f"✗ Erreur avec l'URL {full_url_name}: {e}"))
    
    except ImportError:
        print(style.ERROR("✗ Impossible d'importer grades.urls"))
        print("   Créez un fichier urls.py dans votre application grades")
    except Exception as e:
        print(style.ERROR(f"✗ Erreur lors de la vérification des patterns d'URL: {e}"))
        
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des URLs: {e}"))

# 6. Vérifier les templates
print("\n6. Vérification des templates:")
try:
    templates_to_check = [
        'grades/grade_list.html',
        'grades/grade_detail.html',
        'grades/grade_form.html',
        'grades/grade_confirm_delete.html',
        'grades/category_list.html',
        'grades/category_form.html',
        'grades/practitioner_grades.html',
        'grades/assign_grade.html',
        'grades/bulk_management.html',
    ]
    
    for template_name in templates_to_check:
        try:
            template = get_template(template_name)
            print(style.SUCCESS(f"✓ Template {template_name} trouvé"))
        except TemplateDoesNotExist:
            print(style.ERROR(f"✗ Template {template_name} non trouvé"))
            print(f"   Créez ce template dans templates/{template_name}")
        except Exception as e:
            print(style.ERROR(f"✗ Erreur avec le template {template_name}: {e}"))
            
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des templates: {e}"))

# 7. Vérifier les décorateurs et mixins
print("\n7. Vérification des décorateurs et mixins:")
try:
    from competitions.utils.decorators import club_required, federation_required
    print(style.SUCCESS("✓ Décorateurs club_required et federation_required correctement importés"))
except ImportError:
    print(style.ERROR("✗ Impossible d'importer les décorateurs depuis competitions.utils.decorators"))
    print("   Vérifiez que ces décorateurs existent et sont correctement définis")
except Exception as e:
    print(style.ERROR(f"✗ Erreur lors de la vérification des décorateurs: {e}"))

# 8. Suggestions finales
print("\n8. Suggestions pour résoudre les problèmes:")
print("Si vous avez des erreurs:")
print("1. Assurez-vous que 'grades' est dans INSTALLED_APPS dans settings.py")
print("2. Exécutez les migrations: python manage.py makemigrations grades")
print("3. Appliquez les migrations: python manage.py migrate grades")
print("4. Vérifiez que les URLs sont correctement configurées dans le fichier urls.py principal")
print("5. Créez les templates manquants")
print("6. Vérifiez que les décorateurs et mixins sont correctement définis")
print("7. Si des imports circulaires se produisent, utilisez des imports à l'intérieur des fonctions")

print("\nConsultez les journaux d'erreurs Django pour plus de détails sur les problèmes spécifiques.")
print(style.SUCCESS("\n=== Fin du débogage ===\n"))