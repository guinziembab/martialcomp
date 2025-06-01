from django.core.management.base import BaseCommand
from django.db import transaction
from competitions.models import Discipline, GradeSystem, GradeCategory, Grade
from django.utils import timezone
import re

class Command(BaseCommand):
    help = 'Crée les systèmes de grades pour différentes disciplines d\'arts martiaux'

    def get_color_code(self, color_name):
        """Retourne le code hexadécimal correspondant à une couleur donnée."""
        color_codes = {
            'blanc': '#FFFFFF',
            'blanche': '#FFFFFF',
            'jaune': '#FFEB3B',
            'orange': '#FF9800',
            'vert': '#4CAF50',
            'verte': '#4CAF50',
            'bleu': '#2196F3',
            'bleue': '#2196F3',
            'rouge': '#F44336',
            'marron': '#795548',
            'noir': '#000000',
            'noire': '#000000',
            'violet': '#9C27B0',
            'violette': '#9C27B0',
            'crue': '#E0E0E0',  # Gris clair pour corde crue
        }
        
        # Chercher d'abord les correspondances exactes
        for key, value in color_codes.items():
            if key in color_name.lower():
                return value
        
        # Par défaut
        return '#777777'  # Gris pour les couleurs non reconnues

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Début de la création des systèmes de grades...'))
        
        # Définition de tous les systèmes de grades
        grades_data = {
            "Karate": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Orange", "Ceinture Verte", "Ceinture Bleue", "Ceinture Marron", "Ceinture Noire 1er Dan", "Ceinture Noire 2e Dan", "Ceinture Noire 3e Dan", "Ceinture Noire 4e Dan", "Ceinture Noire 5e Dan"],
            "Taekwondo": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Verte", "Ceinture Bleue", "Ceinture Rouge", "Ceinture Noire 1er Dan", "Ceinture Noire 2e Dan", "Ceinture Noire 3e Dan", "Ceinture Noire 4e Dan"],
            "Judo": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Orange", "Ceinture Verte", "Ceinture Bleue", "Ceinture Marron", "Ceinture Noire 1er Dan", "Ceinture Noire 2e Dan", "Ceinture Noire 3e Dan", "Ceinture Noire 4e Dan", "Ceinture Noire 5e Dan"],
            "Kung Fu": ["Débutant", "Intermédiaire", "Avancé", "Maître"],
            "Viet Vo Dao": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Verte", "Ceinture Bleue", "Ceinture Noire 1er Dang", "Ceinture Noire 2e Dang"],
            "Aikido": ["Ceinture Blanche", "Ceinture Marron", "Ceinture Noire 1er Dan", "Ceinture Noire 2e Dan", "Ceinture Noire 3e Dan", "Ceinture Noire 4e Dan", "Ceinture Noire 5e Dan"],
            "Muay Thai": ["Niveau Débutant", "Niveau Intermédiaire", "Niveau Avancé", "Niveau Expert"],
            "Jiu-Jitsu Brésilien": ["Ceinture Blanche", "Ceinture Bleue", "Ceinture Violette", "Ceinture Marron", "Ceinture Noire"],
            "Krav Maga": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Orange", "Ceinture Verte", "Ceinture Bleue", "Ceinture Marron", "Ceinture Noire"],
            "Capoeira": ["Corde Crue", "Corde Jaune", "Corde Verte", "Corde Bleue", "Corde Marron", "Corde Noire"],
            "Sambo": ["Débutant", "Intermédiaire", "Avancé", "Maître"],
            "Systema": ["Débutant", "Intermédiaire", "Avancé"],
            "Pencak Silat": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Verte", "Ceinture Bleue", "Ceinture Noire"],
            "Savate": ["Gant Bleu", "Gant Vert", "Gant Rouge", "Gant Blanc", "Gant Jaune"],
            "Kickboxing": ["Débutant", "Intermédiaire", "Avancé", "Maître"],
            "Escrime": ["Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4"],
            "Hapkido": ["Ceinture Blanche", "Ceinture Jaune", "Ceinture Verte", "Ceinture Bleue", "Ceinture Noire 1er Dan", "Ceinture Noire 2e Dan", "Ceinture Noire 3e Dan"],
            "Boxe Anglaise": ["Débutant", "Intermédiaire", "Avancé"],
        }
        
        try:
            with transaction.atomic():
                # Traiter chaque discipline
                for discipline_name, grades_list in grades_data.items():
                    # 1. Créer ou récupérer la discipline
                    discipline, created = Discipline.objects.get_or_create(
                        name=discipline_name,
                        defaults={
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Discipline créée: {discipline_name}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Discipline existante: {discipline_name}'))
                    
                    # 2. Créer le système de grades
                    system_name = f"Système de grades - {discipline_name}"
                    system_description = f"Système de grades standard pour {discipline_name}"
                    
                    grade_system, created = GradeSystem.objects.get_or_create(
                        name=system_name,
                        discipline=discipline,
                        defaults={
                            'description': system_description,
                            'is_default': True,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'Système de grades créé: {system_name}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'Système de grades existant: {system_name}'))
                    
                    # 3. Définir les catégories de grades en fonction de la discipline
                    categories = []
                    
                    # Définir les catégories selon le type de discipline
                    if discipline_name in ["Karate", "Judo", "Taekwondo", "Aikido", "Hapkido"]:
                        categories = [
                            {"name": "Kyu", "order": 1, "description": "Grades d'apprentissage"},
                            {"name": "Dan", "order": 2, "description": "Grades de maîtrise"}
                        ]
                    elif discipline_name in ["Viet Vo Dao", "Qwan Ki Do"]:
                        categories = [
                            {"name": "Cap", "order": 1, "description": "Grades d'apprentissage"},
                            {"name": "Dang", "order": 2, "description": "Grades de maîtrise"}
                        ]
                    elif discipline_name in ["Muay Thai", "Systema", "Boxe Anglaise", "Kickboxing", "Sambo"]:
                        categories = [
                            {"name": "Niveaux", "order": 1, "description": "Progression technique"}
                        ]
                    elif discipline_name == "Savate":
                        categories = [
                            {"name": "Gants", "order": 1, "description": "Niveaux techniques en Savate"}
                        ]
                    elif discipline_name == "Capoeira":
                        categories = [
                            {"name": "Cordes", "order": 1, "description": "Grades en Capoeira"}
                        ]
                    elif discipline_name == "Escrime":
                        categories = [
                            {"name": "Niveaux", "order": 1, "description": "Niveaux techniques en escrime"}
                        ]
                    else:
                        # Catégorie par défaut pour les autres disciplines
                        categories = [
                            {"name": "Grades", "order": 1, "description": f"Grades pour {discipline_name}"}
                        ]
                    
                    created_categories = {}
                    
                    # Créer les catégories
                    for cat_data in categories:
                        category, created = GradeCategory.objects.get_or_create(
                            name=cat_data['name'],
                            system=grade_system,
                            defaults={
                                'order': cat_data['order'],
                                'description': cat_data['description']
                            }
                        )
                        created_categories[cat_data['name']] = category
                        
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Catégorie créée: {category.name}'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'Catégorie existante: {category.name}'))
                    
                    # 4. Répartir les grades dans les bonnes catégories
                    for i, grade_name in enumerate(grades_list):
                        # Déterminer la catégorie appropriée pour ce grade
                        category_key = None
                        
                        # Ceintures noires / grades avancés
                        if any(term in grade_name.lower() for term in ['dan', 'dang', 'noire', 'noir', 'maître', 'expert']):
                            if "Dan" in created_categories:
                                category_key = "Dan"
                            elif "Dang" in created_categories:
                                category_key = "Dang"
                            else:
                                category_key = list(created_categories.keys())[0]  # Catégorie par défaut
                        # Grades colorés / débutants et intermédiaires
                        else:
                            if "Kyu" in created_categories:
                                category_key = "Kyu"
                            elif "Cap" in created_categories:
                                category_key = "Cap"
                            elif "Cordes" in created_categories:
                                category_key = "Cordes"
                            elif "Gants" in created_categories:
                                category_key = "Gants"
                            else:
                                category_key = list(created_categories.keys())[0]  # Catégorie par défaut
                        
                        category = created_categories[category_key]
                        
                        # Déterminer si c'est un grade accessible aux clubs
                        accessible_to_clubs = not any(term in grade_name.lower() for term in ['dan', 'dang', 'noire 3', 'noire 4', 'noire 5', 'maître', 'expert'])
                        
                        # Extraire le niveau à partir du nom du grade
                        level = i + 1
                        dan_match = re.search(r'(\d+)[eèr]+\s*(?:Dan|Dang)', grade_name)
                        if dan_match:
                            level = int(dan_match.group(1)) + 10  # Les Dan/Dang commencent à partir de 10
                        
                        # Obtenir la couleur à partir du nom
                        color = self.get_color_code(grade_name)
                        
                        # Âge minimum (estimation)
                        min_age = None
                        if 'Dan' in grade_name or 'Dang' in grade_name:
                            dan_level = int(dan_match.group(1)) if dan_match else 1
                            min_age = 16 + (dan_level - 1) * 2  # Première dan à 16 ans, puis +2 ans par niveau
                        
                        # Créer le grade
                        defaults = {
                            'level': level,
                            'order': i + 1,
                            'color': color,
                            'accessible_to_clubs': accessible_to_clubs,
                            'min_age': min_age,
                        }
                        
                        grade, created = Grade.objects.get_or_create(
                            name=grade_name,
                            category=category,
                            defaults=defaults
                        )
                        
                        if created:
                            self.stdout.write(self.style.SUCCESS(f'Grade créé: {grade_name}'))
                        else:
                            self.stdout.write(self.style.SUCCESS(f'Grade existant mis à jour: {grade_name}'))
                
                self.stdout.write(self.style.SUCCESS('Tous les systèmes de grades ont été créés avec succès'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erreur lors de la création des systèmes de grades: {str(e)}'))
            raise