from django.core.management.base import BaseCommand
from competitions.models import Discipline, CompetitionType

class Command(BaseCommand):
    help = 'Populate database with competition types for various martial arts disciplines'

    def handle(self, *args, **kwargs):
        # Dictionnaire des disciplines et leurs types de compétition
        disciplines_and_types = {
            'Qwan Ki Do': [
                'Techniques traditionnelles individuelles',
                'Techniques traditionnelles synchronisées par équipe de 3',
                'Techniques traditionnelles "Song Luyen" à deux',
                'Co Vo Dao - Techniques individuelles armes traditionnelles',
                'Co Vo Dao - Techniques armes traditionnelles "Song Luyen" à deux',
                'Techniques de démonstration',
                'Combat traditionnel individuel',
                'Combat traditionnel par équipe',
                'Co Vo Dao - Combat traditionnel individuel',
                'Co Vo Dao - Combat traditionnel par équipe',
            ],
            'Karaté': [
                'Kata individuel',
                'Kata par équipe',
                'Kumite individuel',
                'Kumite par équipe',
                'Bunkai',
                'Self-défense',
            ],
            'Judo': [
                'Randori',
                'Shiai',
                'Kata',
                'Ne-waza (combat au sol)',
                'Tachi-waza (combat debout)',
            ],
            'Taekwondo': [
                'Poomsae individuel',
                'Poomsae par équipe',
                'Combat olympique',
                'Cassages',
                'Démonstration technique',
            ],
            'Kung Fu': [
                'Taolu main nue',
                'Taolu avec armes',
                'Sanda (combat)',
                'Duilian (combat chorégraphié)',
                'Qigong',
            ],
        }

        # Compteurs pour le rapport
        created_count = 0
        existing_count = 0

        # Pour chaque discipline
        for discipline_name, competition_types in disciplines_and_types.items():
            # Récupérer ou créer la discipline
            discipline, discipline_created = Discipline.objects.get_or_create(
                name=discipline_name,
                defaults={'description': f'Discipline des arts martiaux: {discipline_name}'}
            )
            
            if discipline_created:
                self.stdout.write(self.style.SUCCESS(f'Discipline créée: {discipline_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Discipline existante: {discipline_name}'))
            
            # Pour chaque type de compétition
            for i, comp_type in enumerate(competition_types):
                # Vérifier si le type existe déjà
                exists = CompetitionType.objects.filter(
                    name=comp_type,
                    discipline=discipline
                ).exists()
                
                if not exists:
                    # Créer le type de compétition
                    CompetitionType.objects.create(
                        name=comp_type,
                        description=f'Type de compétition {comp_type} pour {discipline_name}',
                        discipline=discipline,
                        order=i,
                        team_based='équipe' in comp_type.lower() or 'duilian' in comp_type.lower()
                    )
                    created_count += 1
                    self.stdout.write(f'    - Créé: {comp_type}')
                else:
                    existing_count += 1
                    self.stdout.write(f'    - Existant: {comp_type}')
        
        # Afficher un résumé
        self.stdout.write(self.style.SUCCESS(
            f'Terminé ! {created_count} types de compétition créés, {existing_count} déjà existants.'
        ))