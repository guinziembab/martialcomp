from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from competitions.models import Discipline
from grades.models import Grade, GradeCategory


class Command(BaseCommand):
    help = 'Importe les grades standards pour différentes disciplines d\'arts martiaux'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                self.import_grade_system()
            self.stdout.write(self.style.SUCCESS('Importation réussie des systèmes de grades'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de l\'importation: {str(e)}'))

    def import_grade_system(self):
        # Définition des grades pour toutes les disciplines
        all_grades = {
            'grades': [
                # Grades standards pour Karaté
                {"id": 1, "name": "Ceinture Blanche", "discipline": "Karaté", "category": "Débutant", "color": "Blanche", "color_code": "#FFFFFF", "level": 1},
                {"id": 2, "name": "Ceinture Jaune", "discipline": "Karaté", "category": "Débutant", "color": "Jaune", "color_code": "#FFFF00", "level": 2},
                {"id": 3, "name": "Ceinture Orange", "discipline": "Karaté", "category": "Débutant", "color": "Orange", "color_code": "#FFA500", "level": 3},
                {"id": 4, "name": "Ceinture Verte", "discipline": "Karaté", "category": "Intermédiaire", "color": "Verte", "color_code": "#008000", "level": 4},
                {"id": 5, "name": "Ceinture Bleue", "discipline": "Karaté", "category": "Intermédiaire", "color": "Bleue", "color_code": "#0000FF", "level": 5},
                {"id": 6, "name": "Ceinture Marron", "discipline": "Karaté", "category": "Avancé", "color": "Marron", "color_code": "#A52A2A", "level": 6},
                {"id": 7, "name": "Ceinture Noire 1er Dan", "discipline": "Karaté", "category": "Expert", "color": "Noire", "color_code": "#000000", "level": 7, "is_dan_grade": True},
                {"id": 8, "name": "Ceinture Noire 2ème Dan", "discipline": "Karaté", "category": "Expert", "color": "Noire", "color_code": "#000000", "level": 8, "is_dan_grade": True},
                
                # Grades standards pour Judo
                {"id": 9, "name": "Ceinture Blanche", "discipline": "Judo", "category": "Débutant", "color": "Blanche", "color_code": "#FFFFFF", "level": 1},
                {"id": 10, "name": "Ceinture Jaune", "discipline": "Judo", "category": "Débutant", "color": "Jaune", "color_code": "#FFFF00", "level": 2},
                {"id": 11, "name": "Ceinture Orange", "discipline": "Judo", "category": "Débutant", "color": "Orange", "color_code": "#FFA500", "level": 3},
                {"id": 12, "name": "Ceinture Verte", "discipline": "Judo", "category": "Intermédiaire", "color": "Verte", "color_code": "#008000", "level": 4},
                {"id": 13, "name": "Ceinture Bleue", "discipline": "Judo", "category": "Intermédiaire", "color": "Bleue", "color_code": "#0000FF", "level": 5},
                {"id": 14, "name": "Ceinture Marron", "discipline": "Judo", "category": "Avancé", "color": "Marron", "color_code": "#A52A2A", "level": 6},
                {"id": 15, "name": "Ceinture Noire 1er Dan", "discipline": "Judo", "category": "Expert", "color": "Noire", "color_code": "#000000", "level": 7, "is_dan_grade": True},
                
                # Grades standards pour Taekwondo
                {"id": 16, "name": "Ceinture Blanche", "discipline": "Taekwondo", "category": "Débutant", "color": "Blanche", "color_code": "#FFFFFF", "level": 1},
                {"id": 17, "name": "Ceinture Jaune", "discipline": "Taekwondo", "category": "Débutant", "color": "Jaune", "color_code": "#FFFF00", "level": 2},
                {"id": 18, "name": "Ceinture Verte", "discipline": "Taekwondo", "category": "Intermédiaire", "color": "Verte", "color_code": "#008000", "level": 3},
                {"id": 19, "name": "Ceinture Bleue", "discipline": "Taekwondo", "category": "Intermédiaire", "color": "Bleue", "color_code": "#0000FF", "level": 4},
                {"id": 20, "name": "Ceinture Rouge", "discipline": "Taekwondo", "category": "Avancé", "color": "Rouge", "color_code": "#FF0000", "level": 5},
                {"id": 21, "name": "Ceinture Noire 1er Dan", "discipline": "Taekwondo", "category": "Expert", "color": "Noire", "color_code": "#000000", "level": 6, "is_dan_grade": True},
                
                # Grades Qwan Ki Do - Caps Jaunes
                {"id": 22, "name": "1er Cap Jaune", "discipline": "Qwan Ki Do", "category": "Cap Jaune (Enfants 0-6 ans)", "color": "Jaune", "color_code": "#FFEB3B", "level": 1, "min_age": 0},
                {"id": 23, "name": "2ème Cap Jaune", "discipline": "Qwan Ki Do", "category": "Cap Jaune (Enfants 0-6 ans)", "color": "Jaune", "color_code": "#FFEB3B", "level": 2, "min_age": 0},
                {"id": 24, "name": "3ème Cap Jaune", "discipline": "Qwan Ki Do", "category": "Cap Jaune (Enfants 0-6 ans)", "color": "Jaune", "color_code": "#FFEB3B", "level": 3, "min_age": 0},
                {"id": 25, "name": "4ème Cap Jaune", "discipline": "Qwan Ki Do", "category": "Cap Jaune (Enfants 0-6 ans)", "color": "Jaune", "color_code": "#FFEB3B", "level": 4, "min_age": 0},
                
                # Qwan Ki Do - Caps Rouges
                {"id": 26, "name": "1er Cap Rouge", "discipline": "Qwan Ki Do", "category": "Cap Rouge (Enfants 7-12 ans)", "color": "Rouge", "color_code": "#F44336", "level": 5, "min_age": 7},
                {"id": 27, "name": "2ème Cap Rouge", "discipline": "Qwan Ki Do", "category": "Cap Rouge (Enfants 7-12 ans)", "color": "Rouge", "color_code": "#F44336", "level": 6, "min_age": 7},
                {"id": 28, "name": "3ème Cap Rouge", "discipline": "Qwan Ki Do", "category": "Cap Rouge (Enfants 7-12 ans)", "color": "Rouge", "color_code": "#F44336", "level": 7, "min_age": 7},
                {"id": 29, "name": "4ème Cap Rouge", "discipline": "Qwan Ki Do", "category": "Cap Rouge (Enfants 7-12 ans)", "color": "Rouge", "color_code": "#F44336", "level": 8, "min_age": 7},
                
                # Qwan Ki Do - Caps Blancs
                {"id": 30, "name": "1er Cap Blanc", "discipline": "Qwan Ki Do", "category": "Cap Blanc (Enfants 9-12 ans)", "color": "Blanc", "color_code": "#FFFFFF", "level": 9, "min_age": 9},
                {"id": 31, "name": "2ème Cap Blanc", "discipline": "Qwan Ki Do", "category": "Cap Blanc (Enfants 9-12 ans)", "color": "Blanc", "color_code": "#FFFFFF", "level": 10, "min_age": 9},
                {"id": 32, "name": "3ème Cap Blanc", "discipline": "Qwan Ki Do", "category": "Cap Blanc (Enfants 9-12 ans)", "color": "Blanc", "color_code": "#FFFFFF", "level": 11, "min_age": 9},
                {"id": 33, "name": "4ème Cap Blanc", "discipline": "Qwan Ki Do", "category": "Cap Blanc (Enfants 9-12 ans)", "color": "Blanc", "color_code": "#FFFFFF", "level": 12, "min_age": 9},
                
                # Qwan Ki Do - Caps Bleus
                {"id": 34, "name": "1er Cap Bleu", "discipline": "Qwan Ki Do", "category": "Cap Bleu (Juniors/Adultes)", "color": "Bleu", "color_code": "#2196F3", "level": 13, "min_age": 13},
                {"id": 35, "name": "2ème Cap Bleu", "discipline": "Qwan Ki Do", "category": "Cap Bleu (Juniors/Adultes)", "color": "Bleu", "color_code": "#2196F3", "level": 14, "min_age": 13},
                {"id": 36, "name": "3ème Cap Bleu", "discipline": "Qwan Ki Do", "category": "Cap Bleu (Juniors/Adultes)", "color": "Bleu", "color_code": "#2196F3", "level": 15, "min_age": 13},
                {"id": 37, "name": "4ème Cap Bleu", "discipline": "Qwan Ki Do", "category": "Cap Bleu (Juniors/Adultes)", "color": "Bleu", "color_code": "#2196F3", "level": 16, "min_age": 13},
                {"id": 38, "name": "Écharpe Bleue", "discipline": "Qwan Ki Do", "category": "Cap Bleu (Juniors/Adultes)", "color": "Bleu", "color_code": "#2196F3", "level": 17, "min_age": 13},
                
                # Qwan Ki Do - Dangs 1-4
                {"id": 39, "name": "1er Dang", "discipline": "Qwan Ki Do", "category": "Dang 1-4", "color": "Noir", "color_code": "#000000", "level": 18, "min_age": 15, "is_dan_grade": True},
                {"id": 40, "name": "2ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 1-4", "color": "Noir", "color_code": "#000000", "level": 19, "min_age": 18, "is_dan_grade": True},
                {"id": 41, "name": "3ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 1-4", "color": "Noir", "color_code": "#000000", "level": 20, "min_age": 21, "is_dan_grade": True},
                {"id": 42, "name": "4ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 1-4", "color": "Noir", "color_code": "#000000", "level": 21, "min_age": 25, "is_dan_grade": True},
                
                # Qwan Ki Do - Dang 5
                {"id": 43, "name": "5ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 5", "color": "Noir", "color_code": "#000000", "level": 22, "min_age": 30, "is_dan_grade": True},
                
                # Qwan Ki Do - Dangs 6+
                {"id": 44, "name": "6ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 6+", "color": "multicolore", "color_code": "#000000", "level": 23, "min_age": 35, "is_dan_grade": True},
                {"id": 45, "name": "7ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 6+", "color": "multicolore", "color_code": "#000000", "level": 24, "min_age": 40, "is_dan_grade": True},
                {"id": 46, "name": "8ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 6+", "color": "multicolore", "color_code": "#000000", "level": 25, "min_age": 45, "is_dan_grade": True},
                {"id": 47, "name": "9ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 6+", "color": "multicolore", "color_code": "#000000", "level": 26, "min_age": 50, "is_dan_grade": True},
                {"id": 48, "name": "10ème Dang", "discipline": "Qwan Ki Do", "category": "Dang 6+", "color": "multicolore", "color_code": "#000000", "level": 27, "min_age": 55, "is_dan_grade": True}
            ]
        }

        # Dictionnaire pour garder trace des disciplines et catégories créées
        disciplines = {}
        categories = {}
        
        # Compter les éléments créés/mis à jour
        grades_created = 0
        grades_updated = 0
        categories_created = 0
        disciplines_created = 0

        for grade_data in all_grades['grades']:
            # Récupérer ou créer la discipline
            discipline_name = grade_data.get('discipline')
            if discipline_name not in disciplines:
                discipline, created = Discipline.objects.get_or_create(
                    name=discipline_name,
                    defaults={'description': f'Discipline {discipline_name}'}
                )
                disciplines[discipline_name] = discipline
                if created:
                    disciplines_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Discipline créée: {discipline_name}'))
            else:
                discipline = disciplines[discipline_name]
            
            # Récupérer ou créer la catégorie
            category_name = grade_data.get('category')
            category_key = f"{discipline_name}_{category_name}"
            
            if category_name and category_key not in categories:
                category, created = GradeCategory.objects.get_or_create(
                    name=category_name,
                    discipline=discipline,
                    defaults={'order': 0}
                )
                categories[category_key] = category
                if created:
                    categories_created += 1
                    self.stdout.write(self.style.SUCCESS(f'Catégorie créée: {category_name} ({discipline_name})'))
            elif category_name:
                category = categories[category_key]
            else:
                category = None
            
            # Valeurs par défaut pour le grade
            defaults = {
                'category': category,
                'color': grade_data.get('color', ''),
                'color_code': grade_data.get('color_code', ''),
                'level': grade_data.get('level', 0),
                'min_age': grade_data.get('min_age', 0),
                'min_time_in_previous_grade': grade_data.get('min_time_in_previous_grade', 0),
                'is_dan_grade': grade_data.get('is_dan_grade', False),
                'is_active': True,
                'order': grade_data.get('level', 0),
            }
            
            # Créer ou mettre à jour le grade
            grade, created = Grade.objects.update_or_create(
                name=grade_data.get('name'),
                discipline=discipline,
                defaults=defaults
            )
            
            if created:
                grades_created += 1
                self.stdout.write(self.style.SUCCESS(f'Grade créé: {grade.name} ({discipline_name})'))
            else:
                grades_updated += 1
                self.stdout.write(self.style.SUCCESS(f'Grade mis à jour: {grade.name} ({discipline_name})'))
        
        # Résumé des opérations
        self.stdout.write(self.style.SUCCESS(f'\nRécapitulatif:'))
        self.stdout.write(self.style.SUCCESS(f'- Disciplines créées: {disciplines_created}'))
        self.stdout.write(self.style.SUCCESS(f'- Catégories créées: {categories_created}'))
        self.stdout.write(self.style.SUCCESS(f'- Grades créés: {grades_created}'))
        self.stdout.write(self.style.SUCCESS(f'- Grades mis à jour: {grades_updated}'))