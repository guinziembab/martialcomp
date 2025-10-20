#!/usr/bin/env python3
"""
Script de synchronisation des systèmes de grades de développement vers la production
Aligne les grades, catégories et systèmes de graduation entre les environnements
"""

import os
import sys
import json
from datetime import datetime

# Configuration pour la production
PRODUCTION_PATH = "/var/www/vhosts/martialcomp.com/httpdocs"
VENV_PATH = "/var/www/vhosts/martialcomp.com/apps/martialcomp/venv"

def setup_django():
    """Configure Django pour la production"""
    sys.path.insert(0, PRODUCTION_PATH)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    import django
    django.setup()
    
    from apps.grades.models import Grade, GradeCategory, GradingSystem
    from apps.competitions.models import Discipline
    return Grade, GradeCategory, GradingSystem, Discipline

def load_dev_grades():
    """Charge les données de grades depuis le fichier de développement"""
    dev_file = "grades_dev.clean.json"
    
    if not os.path.exists(dev_file):
        print(f"❌ Fichier {dev_file} non trouvé")
        return None
    
    with open(dev_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Organiser les données par type
    grade_categories = [item for item in data if item['model'] == 'grades.gradecategory']
    grades = [item for item in data if item['model'] == 'grades.grade']
    grading_systems = [item for item in data if item['model'] == 'grades.gradingsystem']
    
    return {
        'grade_categories': grade_categories,
        'grades': grades,
        'grading_systems': grading_systems
    }

def sync_grades():
    """Synchronise les systèmes de grades"""
    print("🔄 SYNCHRONISATION DES SYSTÈMES DE GRADES")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Configuration Django
    Grade, GradeCategory, GradingSystem, Discipline = setup_django()
    
    # Charger les données de développement
    print("1️⃣ Chargement des données de développement...")
    dev_data = load_dev_grades()
    
    if not dev_data:
        print("❌ Impossible de charger les données de développement")
        return False
    
    print(f"✅ {len(dev_data['grade_categories'])} catégories de grades")
    print(f"✅ {len(dev_data['grades'])} grades")
    print(f"✅ {len(dev_data['grading_systems'])} systèmes de graduation")
    print()
    
    # Analyser l'état actuel de la production
    print("2️⃣ Analyse de l'état actuel de la production...")
    prod_categories = GradeCategory.objects.all()
    prod_grades = Grade.objects.all()
    prod_systems = GradingSystem.objects.all()
    prod_disciplines = Discipline.objects.all()
    
    print(f"📊 Production actuelle:")
    print(f"   - Catégories de grades: {prod_categories.count()}")
    print(f"   - Grades: {prod_grades.count()}")
    print(f"   - Systèmes de graduation: {prod_systems.count()}")
    print(f"   - Disciplines: {prod_disciplines.count()}")
    print()
    
    # Créer un mapping des disciplines
    discipline_mapping = {}
    for discipline in prod_disciplines:
        discipline_mapping[discipline.id] = discipline
    
    print("3️⃣ Synchronisation des catégories de grades...")
    
    # Synchroniser les catégories de grades
    categories_added = 0
    categories_updated = 0
    
    for dev_category in dev_data['grade_categories']:
        fields = dev_category['fields']
        discipline_id = fields['discipline']
        
        if discipline_id in discipline_mapping:
            discipline = discipline_mapping[discipline_id]
            
            # Vérifier si la catégorie existe déjà
            try:
                existing_category = GradeCategory.objects.get(
                    name=fields['name'],
                    discipline=discipline
                )
                # Mettre à jour si nécessaire
                if (existing_category.description != fields['description'] or
                    existing_category.order != fields['order'] or
                    existing_category.is_active != fields['is_active']):
                    existing_category.description = fields['description']
                    existing_category.order = fields['order']
                    existing_category.is_active = fields['is_active']
                    existing_category.save()
                    categories_updated += 1
                    print(f"   ✅ Mis à jour: {fields['name']} ({discipline.name})")
            except GradeCategory.DoesNotExist:
                # Créer nouvelle catégorie
                GradeCategory.objects.create(
                    name=fields['name'],
                    description=fields['description'],
                    discipline=discipline,
                    order=fields['order'],
                    is_active=fields['is_active']
                )
                categories_added += 1
                print(f"   ✅ Ajouté: {fields['name']} ({discipline.name})")
        else:
            print(f"   ⚠️ Discipline {discipline_id} non trouvée pour {fields['name']}")
    
    print(f"   📊 Catégories ajoutées: {categories_added}")
    print(f"   📊 Catégories mises à jour: {categories_updated}")
    print()
    
    print("4️⃣ Synchronisation des grades...")
    
    # Synchroniser les grades
    grades_added = 0
    grades_updated = 0
    
    for dev_grade in dev_data['grades']:
        fields = dev_grade['fields']
        discipline_id = fields['discipline']
        
        if discipline_id in discipline_mapping:
            discipline = discipline_mapping[discipline_id]
            
            # Trouver la catégorie si elle existe
            category = None
            if fields.get('category'):
                try:
                    category = GradeCategory.objects.get(
                        name=fields['category'],
                        discipline=discipline
                    )
                except GradeCategory.DoesNotExist:
                    pass
            
            # Vérifier si le grade existe déjà
            try:
                existing_grade = Grade.objects.get(
                    name=fields['name'],
                    discipline=discipline
                )
                # Mettre à jour si nécessaire
                updated = False
                if existing_grade.category != category:
                    existing_grade.category = category
                    updated = True
                if existing_grade.color != fields.get('color', ''):
                    existing_grade.color = fields.get('color', '')
                    updated = True
                if existing_grade.color_code != fields.get('color_code', ''):
                    existing_grade.color_code = fields.get('color_code', '')
                    updated = True
                if existing_grade.level != fields.get('level', 0):
                    existing_grade.level = fields.get('level', 0)
                    updated = True
                if existing_grade.min_age != fields.get('min_age', 0):
                    existing_grade.min_age = fields.get('min_age', 0)
                    updated = True
                if existing_grade.min_time_in_previous_grade != fields.get('min_time_in_previous_grade', 0):
                    existing_grade.min_time_in_previous_grade = fields.get('min_time_in_previous_grade', 0)
                    updated = True
                if existing_grade.requirements_text != fields.get('requirements_text', ''):
                    existing_grade.requirements_text = fields.get('requirements_text', '')
                    updated = True
                if existing_grade.is_active != fields.get('is_active', True):
                    existing_grade.is_active = fields.get('is_active', True)
                    updated = True
                if existing_grade.is_dan_grade != fields.get('is_dan_grade', False):
                    existing_grade.is_dan_grade = fields.get('is_dan_grade', False)
                    updated = True
                if existing_grade.order != fields.get('order', 0):
                    existing_grade.order = fields.get('order', 0)
                    updated = True
                
                if updated:
                    existing_grade.save()
                    grades_updated += 1
                    print(f"   ✅ Mis à jour: {fields['name']} ({discipline.name})")
            except Grade.DoesNotExist:
                # Créer nouveau grade
                Grade.objects.create(
                    name=fields['name'],
                    discipline=discipline,
                    category=category,
                    color=fields.get('color', ''),
                    color_code=fields.get('color_code', ''),
                    level=fields.get('level', 0),
                    min_age=fields.get('min_age', 0),
                    min_time_in_previous_grade=fields.get('min_time_in_previous_grade', 0),
                    requirements_text=fields.get('requirements_text', ''),
                    is_active=fields.get('is_active', True),
                    is_dan_grade=fields.get('is_dan_grade', False),
                    order=fields.get('order', 0)
                )
                grades_added += 1
                print(f"   ✅ Ajouté: {fields['name']} ({discipline.name})")
        else:
            print(f"   ⚠️ Discipline {discipline_id} non trouvée pour {fields['name']}")
    
    print(f"   📊 Grades ajoutés: {grades_added}")
    print(f"   📊 Grades mis à jour: {grades_updated}")
    print()
    
    print("5️⃣ Synchronisation des systèmes de graduation...")
    
    # Synchroniser les systèmes de graduation
    systems_added = 0
    systems_updated = 0
    
    for dev_system in dev_data['grading_systems']:
        fields = dev_system['fields']
        discipline_id = fields['discipline']
        
        if discipline_id in discipline_mapping:
            discipline = discipline_mapping[discipline_id]
            
            # Vérifier si le système existe déjà
            try:
                existing_system = GradingSystem.objects.get(
                    name=fields['name'],
                    discipline=discipline
                )
                # Mettre à jour si nécessaire
                if existing_system.description != fields.get('description', ''):
                    existing_system.description = fields.get('description', '')
                    existing_system.save()
                    systems_updated += 1
                    print(f"   ✅ Mis à jour: {fields['name']} ({discipline.name})")
            except GradingSystem.DoesNotExist:
                # Créer nouveau système
                GradingSystem.objects.create(
                    name=fields['name'],
                    description=fields.get('description', ''),
                    discipline=discipline
                )
                systems_added += 1
                print(f"   ✅ Ajouté: {fields['name']} ({discipline.name})")
        else:
            print(f"   ⚠️ Discipline {discipline_id} non trouvée pour {fields['name']}")
    
    print(f"   📊 Systèmes ajoutés: {systems_added}")
    print(f"   📊 Systèmes mis à jour: {systems_updated}")
    print()
    
    print("6️⃣ Résumé de la synchronisation...")
    
    # Vérification finale
    final_categories = GradeCategory.objects.count()
    final_grades = Grade.objects.count()
    final_systems = GradingSystem.objects.count()
    
    print(f"✅ Catégories de grades: {final_categories}")
    print(f"✅ Grades: {final_grades}")
    print(f"✅ Systèmes de graduation: {final_systems}")
    
    # Afficher quelques exemples
    print()
    print("📝 EXEMPLES DE GRADES SYNCHRONISÉS:")
    for i, grade in enumerate(Grade.objects.all()[:10], 1):
        print(f"   {i:2d}. {grade.name} ({grade.discipline.name}) - Niveau {grade.level}")
    
    print()
    print("🎉 Synchronisation des grades terminée avec succès!")
    return True

def main():
    """Fonction principale"""
    try:
        success = sync_grades()
        if success:
            print("\n✅ La production est maintenant alignée avec le développement pour les grades")
        else:
            print("\n❌ La synchronisation a échoué")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la synchronisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()