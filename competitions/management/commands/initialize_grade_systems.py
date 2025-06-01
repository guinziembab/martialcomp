# competitions/management/commands/initialize_grade_systems.py

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from competitions.models import Discipline

class Command(BaseCommand):
    help = 'Initialise les systèmes de grades pour les disciplines d\'arts martiaux'

    def handle(self, *args, **kwargs):
        # Vérifier si la classe GradeSystem existe
        try:
            from grades.models import GradeCategory, Grade
            
            # Vérifier les champs disponibles sur le modèle Grade
            grade_fields = [f.name for f in Grade._meta.get_fields()]
            self.stdout.write(self.style.SUCCESS(f"Champs disponibles sur Grade: {grade_fields}"))
            
            # Vérifier si le modèle GradeCategory a le champ is_default
            has_is_default = hasattr(GradeCategory, 'is_default') or 'is_default' in [f.name for f in GradeCategory._meta.get_fields()]
            has_is_active = hasattr(GradeCategory, 'is_active') or 'is_active' in [f.name for f in GradeCategory._meta.get_fields()]
            
            self.stdout.write(self.style.SUCCESS(
                f"Info: GradeCategory - has_is_default: {has_is_default}, has_is_active: {has_is_active}"
            ))
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "❌ Erreur: Le modèle GradeCategory n'a pas été trouvé.\n"
                "Assurez-vous que grades/models.py existe et contient les classes GradeCategory et Grade."
            ))
            return

        # Compteurs pour les statistiques
        created_systems = 0
        updated_systems = 0
        failed_systems = 0
        created_grades = 0
        
        # Définition des systèmes de grades par discipline
        grade_systems = {
            'Qwan Ki Do': {
                'name': 'Système de grades Qwan Ki Do',
                'grades': [
                    {'name': 'Ceinture blanche', 'color': 'white', 'rank': 0},
                    {'name': 'Ceinture jaune', 'color': 'yellow', 'rank': 1},
                    {'name': 'Ceinture orange', 'color': 'orange', 'rank': 2},
                    {'name': 'Ceinture verte', 'color': 'green', 'rank': 3},
                    {'name': 'Ceinture bleue', 'color': 'blue', 'rank': 4},
                    {'name': 'Ceinture violette', 'color': 'purple', 'rank': 5},
                    {'name': 'Ceinture marron', 'color': 'brown', 'rank': 6},
                    {'name': 'Ceinture rouge', 'color': 'red', 'rank': 7},
                    {'name': 'Ceinture noire 1er Dang', 'color': 'black', 'rank': 8, 'is_dan': True},
                    {'name': 'Ceinture noire 2ème Dang', 'color': 'black', 'rank': 9, 'is_dan': True},
                    {'name': 'Ceinture noire 3ème Dang', 'color': 'black', 'rank': 10, 'is_dan': True},
                    {'name': 'Ceinture noire 4ème Dang', 'color': 'black', 'rank': 11, 'is_dan': True},
                    {'name': 'Ceinture noire 5ème Dang', 'color': 'black', 'rank': 12, 'is_dan': True},
                    {'name': 'Ceinture noire 6ème Dang', 'color': 'black', 'rank': 13, 'is_dan': True},
                    {'name': 'Ceinture noire 7ème Dang', 'color': 'black', 'rank': 14, 'is_dan': True},
                    {'name': 'Ceinture noire 8ème Dang', 'color': 'black', 'rank': 15, 'is_dan': True},
                    {'name': 'Ceinture noire 9ème Dang', 'color': 'black', 'rank': 16, 'is_dan': True},
                    {'name': 'Ceinture noire 10ème Dang', 'color': 'black', 'rank': 17, 'is_dan': True},
                ]
            },
            'Karaté': {
                'name': 'Système de grades Karaté',
                'grades': [
                    {'name': 'Ceinture blanche', 'color': 'white', 'rank': 0},
                    {'name': 'Ceinture jaune', 'color': 'yellow', 'rank': 1},
                    {'name': 'Ceinture orange', 'color': 'orange', 'rank': 2},
                    {'name': 'Ceinture verte', 'color': 'green', 'rank': 3},
                    {'name': 'Ceinture bleue', 'color': 'blue', 'rank': 4},
                    {'name': 'Ceinture marron', 'color': 'brown', 'rank': 5},
                    {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 6, 'is_dan': True},
                    {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 7, 'is_dan': True},
                    {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 8, 'is_dan': True},
                    {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 9, 'is_dan': True},
                    {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 10, 'is_dan': True},
                    {'name': 'Ceinture noire 6ème Dan', 'color': 'black', 'rank': 11, 'is_dan': True},
                    {'name': 'Ceinture noire 7ème Dan', 'color': 'black', 'rank': 12, 'is_dan': True},
                    {'name': 'Ceinture noire 8ème Dan', 'color': 'black', 'rank': 13, 'is_dan': True},
                    {'name': 'Ceinture noire 9ème Dan', 'color': 'black', 'rank': 14, 'is_dan': True},
                    {'name': 'Ceinture noire 10ème Dan', 'color': 'black', 'rank': 15, 'is_dan': True},
                ]
            },
            'Judo': {
                'name': 'Système de grades Judo',
                'grades': [
                    {'name': 'Ceinture blanche', 'color': 'white', 'rank': 0},
                    {'name': 'Ceinture blanche-jaune', 'color': 'white-yellow', 'rank': 1},
                    {'name': 'Ceinture jaune', 'color': 'yellow', 'rank': 2},
                    {'name': 'Ceinture jaune-orange', 'color': 'yellow-orange', 'rank': 3},
                    {'name': 'Ceinture orange', 'color': 'orange', 'rank': 4},
                    {'name': 'Ceinture orange-verte', 'color': 'orange-green', 'rank': 5},
                    {'name': 'Ceinture verte', 'color': 'green', 'rank': 6},
                    {'name': 'Ceinture bleue', 'color': 'blue', 'rank': 7},
                    {'name': 'Ceinture marron', 'color': 'brown', 'rank': 8},
                    {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 9, 'is_dan': True},
                    {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 10, 'is_dan': True},
                    {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 11, 'is_dan': True},
                    {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 12, 'is_dan': True},
                    {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 13, 'is_dan': True},
                    {'name': 'Ceinture rouge-blanc 6ème Dan', 'color': 'red-white', 'rank': 14, 'is_dan': True},
                    {'name': 'Ceinture rouge-blanc 7ème Dan', 'color': 'red-white', 'rank': 15, 'is_dan': True},
                    {'name': 'Ceinture rouge-blanc 8ème Dan', 'color': 'red-white', 'rank': 16, 'is_dan': True},
                    {'name': 'Ceinture rouge 9ème Dan', 'color': 'red', 'rank': 17, 'is_dan': True},
                    {'name': 'Ceinture rouge 10ème Dan', 'color': 'red', 'rank': 18, 'is_dan': True},
                ]
            },
            'Taekwondo': {
                'name': 'Système de grades Taekwondo',
                'grades': [
                    {'name': 'Ceinture blanche (10ème Keup)', 'color': 'white', 'rank': 0},
                    {'name': 'Ceinture blanche-jaune (9ème Keup)', 'color': 'white-yellow', 'rank': 1},
                    {'name': 'Ceinture jaune (8ème Keup)', 'color': 'yellow', 'rank': 2},
                    {'name': 'Ceinture jaune-verte (7ème Keup)', 'color': 'yellow-green', 'rank': 3},
                    {'name': 'Ceinture verte (6ème Keup)', 'color': 'green', 'rank': 4},
                    {'name': 'Ceinture verte-bleue (5ème Keup)', 'color': 'green-blue', 'rank': 5},
                    {'name': 'Ceinture bleue (4ème Keup)', 'color': 'blue', 'rank': 6},
                    {'name': 'Ceinture bleue-rouge (3ème Keup)', 'color': 'blue-red', 'rank': 7},
                    {'name': 'Ceinture rouge (2ème Keup)', 'color': 'red', 'rank': 8},
                    {'name': 'Ceinture rouge-noire (1er Keup)', 'color': 'red-black', 'rank': 9},
                    {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 10, 'is_dan': True},
                    {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 11, 'is_dan': True},
                    {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 12, 'is_dan': True},
                    {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 13, 'is_dan': True},
                    {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 14, 'is_dan': True},
                    {'name': 'Ceinture noire 6ème Dan', 'color': 'black', 'rank': 15, 'is_dan': True},
                    {'name': 'Ceinture noire 7ème Dan', 'color': 'black', 'rank': 16, 'is_dan': True},
                    {'name': 'Ceinture noire 8ème Dan', 'color': 'black', 'rank': 17, 'is_dan': True},
                    {'name': 'Ceinture noire 9ème Dan', 'color': 'black', 'rank': 18, 'is_dan': True},
                ]
            }
        }
        
        # Ajouter d'autres disciplines
        for discipline_name in ['Aikido', 'Kung Fu', 'Viet Vo Dao']:
            if discipline_name not in grade_systems:
                grade_systems[discipline_name] = {
                    'name': f'Système de grades {discipline_name}',
                    'grades': [
                        {'name': 'Ceinture blanche', 'color': 'white', 'rank': 0},
                        {'name': 'Ceinture jaune', 'color': 'yellow', 'rank': 1},
                        {'name': 'Ceinture verte', 'color': 'green', 'rank': 2},
                        {'name': 'Ceinture bleue', 'color': 'blue', 'rank': 3},
                        {'name': 'Ceinture marron', 'color': 'brown', 'rank': 4},
                        {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 5, 'is_dan': True},
                        {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 6, 'is_dan': True},
                        {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 7, 'is_dan': True},
                        {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 8, 'is_dan': True},
                        {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 9, 'is_dan': True},
                    ]
                }
        
        # Pour chaque discipline, créer ou mettre à jour le système de grades
        for discipline_name, system_data in grade_systems.items():
            try:
                # Récupérer la discipline
                try:
                    discipline = Discipline.objects.get(name=discipline_name)
                    self.stdout.write(self.style.SUCCESS(f"Discipline trouvée: {discipline.name} (ID: {discipline.id})"))
                except Discipline.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"La discipline {discipline_name} n'existe pas, création ignorée"
                    ))
                    continue
                
                # Créer ou mettre à jour le système de grades
                with transaction.atomic():
                    # Préparer les defaults en fonction des champs disponibles
                    defaults = {}
                    if has_is_active:
                        defaults['is_active'] = True
                    if has_is_default:
                        defaults['is_default'] = True
                    
                    # Créer ou mettre à jour la catégorie de grade
                    system, created = GradeCategory.objects.update_or_create(
                        discipline=discipline,
                        name=system_data['name'],
                        defaults=defaults
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Système de grades créé pour {discipline_name}"
                        ))
                        created_systems += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Le système de grades pour {discipline_name} existe déjà"
                        ))
                        updated_systems += 1
                    
                    # Ajouter les grades
                    for grade_data in system_data['grades']:
                        try:
                            # Préparer les données du grade
                            grade_defaults = {
                                'name': grade_data['name'],
                                'color': grade_data.get('color', ''),
                                'order': grade_data.get('rank', 0),  # Utiliser 'rank' pour 'order' également
                            }
                            
                            # Ajouter le champ is_dan_grade s'il existe
                            if 'is_dan' in grade_data:
                                grade_defaults['is_dan_grade'] = grade_data['is_dan']
                            
                            # Créer ou mettre à jour le grade
                            grade, grade_created = Grade.objects.update_or_create(
                                category=system,
                                discipline=discipline,
                                level=grade_data['rank'],
                                defaults=grade_defaults
                            )
                            
                            if grade_created:
                                created_grades += 1
                                self.stdout.write(f"  ✓ Grade créé: {grade.name}")
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(
                                f"  ✗ Erreur lors de la création du grade {grade_data['name']}: {str(e)}"
                            ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Erreur lors du chargement des grades pour {discipline_name}: {str(e)}"
                ))
                failed_systems += 1
                continue
        
        # Afficher le résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("✨ Initialisation terminée!"))
        self.stdout.write("📊 Bilan:")
        self.stdout.write(f"   - Systèmes créés: {created_systems}")
        self.stdout.write(f"   - Systèmes existants: {updated_systems}")
        self.stdout.write(f"   - Échecs: {failed_systems}")
        self.stdout.write(f"   - Grades créés: {created_grades}")
        self.stdout.write("="*50)