# competitions/management/commands/initialize_grade_systems.py

from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from apps.competitions.models import Discipline

class Command(BaseCommand):
    help = 'Initialise les systèmes de grades pour les disciplines d\'arts martiaux'

            from apps.grades.models import GradeCategory as GradeSystem, Grade
    def handle(self, *args, **kwargs):
        # Vérifier si la classe GradeSystem existe
        try:
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "âŒ Erreur: Le modèle GradeSystem n'a pas été trouvé.\n"
                "Assurez-vous que competitions/models/grades.py existe et contient les classes GradeSystem et Grade."
            ))
            return

        # Compteurs pour les statistiques
        created_systems = 0
        updated_systems = 0
        failed_systems = 0
        
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
                    {'name': 'Ceinture noire 1er Dang', 'color': 'black', 'rank': 8, 'is_dan': True, 'dan_level': 1},
                    {'name': 'Ceinture noire 2ème Dang', 'color': 'black', 'rank': 9, 'is_dan': True, 'dan_level': 2},
                    {'name': 'Ceinture noire 3ème Dang', 'color': 'black', 'rank': 10, 'is_dan': True, 'dan_level': 3},
                    {'name': 'Ceinture noire 4ème Dang', 'color': 'black', 'rank': 11, 'is_dan': True, 'dan_level': 4},
                    {'name': 'Ceinture noire 5ème Dang', 'color': 'black', 'rank': 12, 'is_dan': True, 'dan_level': 5},
                    {'name': 'Ceinture noire 6ème Dang', 'color': 'black', 'rank': 13, 'is_dan': True, 'dan_level': 6},
                    {'name': 'Ceinture noire 7ème Dang', 'color': 'black', 'rank': 14, 'is_dan': True, 'dan_level': 7},
                    {'name': 'Ceinture noire 8ème Dang', 'color': 'black', 'rank': 15, 'is_dan': True, 'dan_level': 8},
                    {'name': 'Ceinture noire 9ème Dang', 'color': 'black', 'rank': 16, 'is_dan': True, 'dan_level': 9},
                    {'name': 'Ceinture noire 10ème Dang', 'color': 'black', 'rank': 17, 'is_dan': True, 'dan_level': 10},
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
                    {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 6, 'is_dan': True, 'dan_level': 1},
                    {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 7, 'is_dan': True, 'dan_level': 2},
                    {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 8, 'is_dan': True, 'dan_level': 3},
                    {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 9, 'is_dan': True, 'dan_level': 4},
                    {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 10, 'is_dan': True, 'dan_level': 5},
                    {'name': 'Ceinture noire 6ème Dan', 'color': 'black', 'rank': 11, 'is_dan': True, 'dan_level': 6},
                    {'name': 'Ceinture noire 7ème Dan', 'color': 'black', 'rank': 12, 'is_dan': True, 'dan_level': 7},
                    {'name': 'Ceinture noire 8ème Dan', 'color': 'black', 'rank': 13, 'is_dan': True, 'dan_level': 8},
                    {'name': 'Ceinture noire 9ème Dan', 'color': 'black', 'rank': 14, 'is_dan': True, 'dan_level': 9},
                    {'name': 'Ceinture noire 10ème Dan', 'color': 'black', 'rank': 15, 'is_dan': True, 'dan_level': 10},
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
                    {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 9, 'is_dan': True, 'dan_level': 1},
                    {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 10, 'is_dan': True, 'dan_level': 2},
                    {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 11, 'is_dan': True, 'dan_level': 3},
                    {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 12, 'is_dan': True, 'dan_level': 4},
                    {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 13, 'is_dan': True, 'dan_level': 5},
                    {'name': 'Ceinture rouge-blanc 6ème Dan', 'color': 'red-white', 'rank': 14, 'is_dan': True, 'dan_level': 6},
                    {'name': 'Ceinture rouge-blanc 7ème Dan', 'color': 'red-white', 'rank': 15, 'is_dan': True, 'dan_level': 7},
                    {'name': 'Ceinture rouge-blanc 8ème Dan', 'color': 'red-white', 'rank': 16, 'is_dan': True, 'dan_level': 8},
                    {'name': 'Ceinture rouge 9ème Dan', 'color': 'red', 'rank': 17, 'is_dan': True, 'dan_level': 9},
                    {'name': 'Ceinture rouge 10ème Dan', 'color': 'red', 'rank': 18, 'is_dan': True, 'dan_level': 10},
                ]
            },
            'Taekwondo': {
                'name': 'Système de grades Taekwondo',
                'grades': [
                    {'name': 'Ceinture blanche', 'color': 'white', 'rank': 0, 'abbreviation': '10ème Keup'},
                    {'name': 'Ceinture blanche-jaune', 'color': 'white-yellow', 'rank': 1, 'abbreviation': '9ème Keup'},
                    {'name': 'Ceinture jaune', 'color': 'yellow', 'rank': 2, 'abbreviation': '8ème Keup'},
                    {'name': 'Ceinture jaune-verte', 'color': 'yellow-green', 'rank': 3, 'abbreviation': '7ème Keup'},
                    {'name': 'Ceinture verte', 'color': 'green', 'rank': 4, 'abbreviation': '6ème Keup'},
                    {'name': 'Ceinture verte-bleue', 'color': 'green-blue', 'rank': 5, 'abbreviation': '5ème Keup'},
                    {'name': 'Ceinture bleue', 'color': 'blue', 'rank': 6, 'abbreviation': '4ème Keup'},
                    {'name': 'Ceinture bleue-rouge', 'color': 'blue-red', 'rank': 7, 'abbreviation': '3ème Keup'},
                    {'name': 'Ceinture rouge', 'color': 'red', 'rank': 8, 'abbreviation': '2ème Keup'},
                    {'name': 'Ceinture rouge-noire', 'color': 'red-black', 'rank': 9, 'abbreviation': '1er Keup'},
                    {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 10, 'is_dan': True, 'dan_level': 1},
                    {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 11, 'is_dan': True, 'dan_level': 2},
                    {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 12, 'is_dan': True, 'dan_level': 3},
                    {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 13, 'is_dan': True, 'dan_level': 4},
                    {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 14, 'is_dan': True, 'dan_level': 5},
                    {'name': 'Ceinture noire 6ème Dan', 'color': 'black', 'rank': 15, 'is_dan': True, 'dan_level': 6},
                    {'name': 'Ceinture noire 7ème Dan', 'color': 'black', 'rank': 16, 'is_dan': True, 'dan_level': 7},
                    {'name': 'Ceinture noire 8ème Dan', 'color': 'black', 'rank': 17, 'is_dan': True, 'dan_level': 8},
                    {'name': 'Ceinture noire 9ème Dan', 'color': 'black', 'rank': 18, 'is_dan': True, 'dan_level': 9},
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
                        {'name': 'Ceinture noire 1er Dan', 'color': 'black', 'rank': 5, 'is_dan': True, 'dan_level': 1},
                        {'name': 'Ceinture noire 2ème Dan', 'color': 'black', 'rank': 6, 'is_dan': True, 'dan_level': 2},
                        {'name': 'Ceinture noire 3ème Dan', 'color': 'black', 'rank': 7, 'is_dan': True, 'dan_level': 3},
                        {'name': 'Ceinture noire 4ème Dan', 'color': 'black', 'rank': 8, 'is_dan': True, 'dan_level': 4},
                        {'name': 'Ceinture noire 5ème Dan', 'color': 'black', 'rank': 9, 'is_dan': True, 'dan_level': 5},
                    ]
                }
        
        # Pour chaque discipline, créer ou mettre Ã  jour le système de grades
        for discipline_name, system_data in grade_systems.items():
            try:
                # Récupérer la discipline
                try:
                    discipline = Discipline.objects.get(name=discipline_name)
                except Discipline.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"La discipline {discipline_name} n'existe pas, création ignorée"
                    ))
                    continue
                
                # Créer ou mettre Ã  jour le système de grades
                with transaction.atomic():
                    system, created = GradeSystem.objects.update_or_create(
                        discipline=discipline,
                        name=system_data['name'],
                        defaults={
                            'is_default': True,
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f"âœ… Système de grades créé pour {discipline_name}"
                        ))
                        created_systems += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Le système de grades pour {discipline_name} existe déjÃ "
                        ))
                        updated_systems += 1
                    
                    # Ajouter les grades
                    for grade_data in system_data['grades']:
                        Grade.objects.update_or_create(
                            system=system,
                            rank=grade_data['rank'],
                            defaults={
                                'name': grade_data['name'],
                                'color': grade_data.get('color', ''),
                                'abbreviation': grade_data.get('abbreviation', ''),
                                'is_dan': grade_data.get('is_dan', False),
                                'dan_level': grade_data.get('dan_level', None),
                            }
                        )
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Erreur lors du chargement des grades pour {discipline_name}: {e}"
                ))
                failed_systems += 1
                continue
        
        # Afficher le résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("âœ¨ Initialisation terminée!"))
        self.stdout.write("ðŸ“Š Bilan:")
        self.stdout.write(f"   - Systèmes créés: {created_systems}")
        self.stdout.write(f"   - Systèmes existants: {updated_systems}")
        self.stdout.write(f"   - Ã‰checs: {failed_systems}")
        self.stdout.write("="*50)

