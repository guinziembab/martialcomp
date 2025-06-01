from django.core.management.base import BaseCommand
from competitions.models import Discipline, CompetitionType

class Command(BaseCommand):
    help = 'Charge les types de compétition par défaut'

    def handle(self, *args, **options):
        # Récupérer les disciplines
        try:
            qwan_ki_do = Discipline.objects.get(name="Qwan Ki Do")
        except Discipline.DoesNotExist:
            self.stdout.write(self.style.WARNING('Discipline "Qwan Ki Do" non trouvée'))
            return
            
        # Types pour Qwan Ki Do
        qwan_ki_do_types = [
            {
                "name": "Technique traditionnelle individuel",
                "description": "Compétition de techniques Quyen traditionnelles en individuel",
                "team_based": False,
                "order": 1
            },
            {
                "name": "Technique synchronisé en équipe",
                "description": "Compétition de techniques Quyen synchronisées en équipe",
                "team_based": True,
                "min_team_size": 3,
                "max_team_size": 5,
                "order": 2
            },
            {
                "name": "Technique armes traditionnelles individuel",
                "description": "Compétition de techniques avec armes traditionnelles en individuel",
                "team_based": False,
                "order": 3
            },
            {
                "name": "Technique armes traditionnelles en équipe",
                "description": "Compétition de techniques avec armes traditionnelles en équipe",
                "team_based": True,
                "min_team_size": 3,
                "max_team_size": 5,
                "order": 4
            },
            {
                "name": "Song Luyen",
                "description": "Compétition de techniques à deux (Song Luyen)",
                "team_based": True,
                "min_team_size": 2,
                "max_team_size": 2,
                "order": 5
            },
            {
                "name": "Démonstration",
                "description": "Compétition de démonstration",
                "team_based": True,
                "min_team_size": 5,
                "max_team_size": 15,
                "order": 6
            },
            {
                "name": "Combat individuel",
                "description": "Compétition de combat en individuel",
                "team_based": False,
                "weight_category": True,
                "order": 7
            },
            {
                "name": "Combat par équipe",
                "description": "Compétition de combat par équipe",
                "team_based": True,
                "min_team_size": 3,
                "max_team_size": 5,
                "order": 8
            },
            {
                "name": "Combat armes traditionnelles individuel",
                "description": "Compétition de combat avec armes traditionnelles en individuel",
                "team_based": False,
                "order": 9
            },
            {
                "name": "Combat armes traditionnelles en équipe",
                "description": "Compétition de combat avec armes traditionnelles en équipe",
                "team_based": True,
                "min_team_size": 3,
                "max_team_size": 5,
                "order": 10
            },
            {
                "name": "Combat libre par catégorie de poids",
                "description": "Compétition de combat libre par catégorie de poids",
                "team_based": False,
                "weight_category": True,
                "order": 11
            }
        ]
        
        # Créer les types pour Qwan Ki Do
        counter = 0
        for type_data in qwan_ki_do_types:
            comp_type, created = CompetitionType.objects.update_or_create(
                name=type_data["name"],
                discipline=qwan_ki_do,
                defaults={
                    "description": type_data["description"],
                    "team_based": type_data["team_based"],
                    "min_team_size": type_data.get("min_team_size", 1),
                    "max_team_size": type_data.get("max_team_size", 1),
                    "weight_category": type_data.get("weight_category", False),
                    "order": type_data["order"]
                }
            )
            
            if created:
                counter += 1
        
        self.stdout.write(self.style.SUCCESS(f'{counter} types de compétition créés pour le Qwan Ki Do'))

        # Ajouter ici d'autres disciplines comme le Karaté, Judo, etc.