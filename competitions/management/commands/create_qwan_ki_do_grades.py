from django.core.management.base import BaseCommand
from django.db import transaction
from competitions.models import Discipline
from grades.models import Grade, GradeCategory
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crée le système de grades complet pour le Qwan Ki Do'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Début de la création du système de grades Qwan Ki Do...'))
        
        try:
            with transaction.atomic():
                # 1. Vérifier si la discipline Qwan Ki Do existe, sinon la créer
                qwan_ki_do, created = Discipline.objects.get_or_create(
                    name='Qwan Ki Do',
                    defaults={
                        'description': 'Art martial sino-vietnamien moderne combinant techniques traditionnelles du Sud et du Nord.',
                        'country_origin': 'Vietnam',
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Discipline Qwan Ki Do créée'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Discipline Qwan Ki Do trouvée'))
                
                # 2. Créer les catégories de grades
                categories = [
                    {
                        'name': 'Cap Jaune (Enfants 0-6 ans)',
                        'order': 1,
                        'description': 'Grades pour les très jeunes enfants de 0 à 6 ans'
                    },
                    {
                        'name': 'Cap Rouge (Enfants 7-12 ans)',
                        'order': 2,
                        'description': 'Grades pour les enfants de 7 à 12 ans'
                    },
                    {
                        'name': 'Cap Blanc (Enfants 9-12 ans)',
                        'order': 3,
                        'description': 'Grades spécifiques pour les enfants de 9 à 12 ans (Ceinture Violette)'
                    },
                    {
                        'name': 'Cap Bleu (Juniors/Adultes)',
                        'order': 4,
                        'description': 'Grades pour les juniors et adultes (13 ans et plus)'
                    },
                    {
                        'name': 'Dang 1-4',
                        'order': 5,
                        'description': 'Ceinture noire avec liseret rouge (1er au 4ème Dang)'
                    },
                    {
                        'name': 'Dang 5',
                        'order': 6,
                        'description': 'Ceinture noire avec liseret jaune (5ème Dang)'
                    },
                    {
                        'name': 'Dang 6+',
                        'order': 7,
                        'description': 'Ceinture multicolore - rouge, jaune, blanc (6ème Dang et plus)'
                    },
                ]
                
                created_categories = {}
                
                for cat_data in categories:
                    category, created = GradeCategory.objects.get_or_create(
                        name=cat_data['name'],
                        discipline=qwan_ki_do,
                        defaults={
                            'order': cat_data['order'],
                            'description': cat_data['description']
                        }
                    )
                    created_categories[cat_data['name']] = category
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Catégorie créée: {category.name}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Catégorie trouvée: {category.name}'))
                
                # 4. Créer les grades pour chaque catégorie
                grades_data = [
                    # Cap Jaune (Enfants 0-6 ans)
                    {
                        'category': 'Cap Jaune (Enfants 0-6 ans)',
                        'grades': [
                            {'name': '1er Cap Jaune', 'level': 1, 'order': 1, 'color': '#FFEB3B', 'min_age': 0},
                            {'name': '2ème Cap Jaune', 'level': 2, 'order': 2, 'color': '#FFEB3B', 'min_age': 0},
                            {'name': '3ème Cap Jaune', 'level': 3, 'order': 3, 'color': '#FFEB3B', 'min_age': 0},
                            {'name': '4ème Cap Jaune', 'level': 4, 'order': 4, 'color': '#FFEB3B', 'min_age': 0},
                        ]
                    },
                    # Cap Rouge (Enfants 7-12 ans)
                    {
                        'category': 'Cap Rouge (Enfants 7-12 ans)',
                        'grades': [
                            {'name': '1er Cap Rouge', 'level': 5, 'order': 1, 'color': '#F44336', 'min_age': 7},
                            {'name': '2ème Cap Rouge', 'level': 6, 'order': 2, 'color': '#F44336', 'min_age': 7},
                            {'name': '3ème Cap Rouge', 'level': 7, 'order': 3, 'color': '#F44336', 'min_age': 7},
                            {'name': '4ème Cap Rouge', 'level': 8, 'order': 4, 'color': '#F44336', 'min_age': 7},
                        ]
                    },
                    # Cap Blanc (Enfants 9-12 ans)
                    {
                        'category': 'Cap Blanc (Enfants 9-12 ans)',
                        'grades': [
                            {'name': '1er Cap Blanc', 'level': 9, 'order': 1, 'color': '#FFFFFF', 'min_age': 9},
                            {'name': '2ème Cap Blanc', 'level': 10, 'order': 2, 'color': '#FFFFFF', 'min_age': 9},
                            {'name': '3ème Cap Blanc', 'level': 11, 'order': 3, 'color': '#FFFFFF', 'min_age': 9},
                            {'name': '4ème Cap Blanc', 'level': 12, 'order': 4, 'color': '#FFFFFF', 'min_age': 9},
                        ]
                    },
                    # Cap Bleu (Juniors/Adultes)
                    {
                        'category': 'Cap Bleu (Juniors/Adultes)',
                        'grades': [
                            {'name': '1er Cap Bleu', 'level': 13, 'order': 1, 'color': '#2196F3', 'min_age': 13},
                            {'name': '2ème Cap Bleu', 'level': 14, 'order': 2, 'color': '#2196F3', 'min_age': 13},
                            {'name': '3ème Cap Bleu', 'level': 15, 'order': 3, 'color': '#2196F3', 'min_age': 13},
                            {'name': '4ème Cap Bleu', 'level': 16, 'order': 4, 'color': '#2196F3', 'min_age': 13},
                            {'name': 'Écharpe Bleue', 'level': 17, 'order': 5, 'color': '#2196F3', 'min_age': 13},
                        ]
                    },
                    # Dang 1-4 (Ceinture noire avec liseret rouge)
                    {
                        'category': 'Dang 1-4',
                        'grades': [
                            {'name': '1er Dang', 'level': 18, 'order': 1, 'color': '#000000', 'min_age': 15, 'is_dan_grade': True},
                            {'name': '2ème Dang', 'level': 19, 'order': 2, 'color': '#000000', 'min_age': 18, 'is_dan_grade': True},
                            {'name': '3ème Dang', 'level': 20, 'order': 3, 'color': '#000000', 'min_age': 21, 'is_dan_grade': True},
                            {'name': '4ème Dang', 'level': 21, 'order': 4, 'color': '#000000', 'min_age': 25, 'is_dan_grade': True},
                        ]
                    },
                    # Dang 5 (Ceinture noire avec liseret jaune)
                    {
                        'category': 'Dang 5',
                        'grades': [
                            {'name': '5ème Dang', 'level': 22, 'order': 1, 'color': '#000000', 'min_age': 30, 'is_dan_grade': True},
                        ]
                    },
                    # Dang 6+ (Ceinture multicolore)
                    {
                        'category': 'Dang 6+',
                        'grades': [
                            {'name': '6ème Dang', 'level': 23, 'order': 1, 'color': 'multicolore', 'min_age': 35, 'is_dan_grade': True},
                            {'name': '7ème Dang', 'level': 24, 'order': 2, 'color': 'multicolore', 'min_age': 40, 'is_dan_grade': True},
                            {'name': '8ème Dang', 'level': 25, 'order': 3, 'color': 'multicolore', 'min_age': 45, 'is_dan_grade': True},
                            {'name': '9ème Dang', 'level': 26, 'order': 4, 'color': 'multicolore', 'min_age': 50, 'is_dan_grade': True},
                            {'name': '10ème Dang', 'level': 27, 'order': 5, 'color': 'multicolore', 'min_age': 55, 'is_dan_grade': True},
                        ]
                    },
                ]
                
                grades_count = 0
                
                for grade_category in grades_data:
                    category = created_categories[grade_category['category']]
                    
                    for grade_info in grade_category['grades']:
                        defaults = {
                            'level': grade_info['level'],
                            'order': grade_info['order'],
                            'color': grade_info['color'],
                            'color_code': grade_info['color'] if grade_info['color'].startswith('#') else '',
                            'min_age': grade_info.get('min_age', 0),
                            'is_dan_grade': grade_info.get('is_dan_grade', False),
                            'is_active': True,
                            # Suppression des champs description/requirements qui posent problème
                        }
                        
                        grade, created = Grade.objects.get_or_create(
                            name=grade_info['name'],
                            discipline=qwan_ki_do,
                            category=category,
                            defaults=defaults
                        )
                        
                        if created:
                            grades_count += 1
                            self.stdout.write(f'Grade créé: {grade.name}')
                
                self.stdout.write(self.style.SUCCESS(f'Total de {grades_count} grades créés pour le Qwan Ki Do'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la création du système de grades: {str(e)}'))
            raise
        
        self.stdout.write(self.style.SUCCESS('Création du système de grades Qwan Ki Do terminée avec succès'))