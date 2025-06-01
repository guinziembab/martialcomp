# competitions/management/commands/load_disciplines.py
from django.core.management.base import BaseCommand
from competitions.models import Discipline

class Command(BaseCommand):
    help = 'Charge les disciplines d\'arts martiaux par défaut'

    def handle(self, *args, **options):
        disciplines = [
            {
                "name": "Qwan Ki Do",
                "description": "Art martial sino-vietnamien fondé par Maître Châu Quan Ky en 1981. Il combine des techniques traditionnelles du nord et du sud de la Chine et du Vietnam, intégrant techniques de poing, pied, projection, clés et armes traditionnelles.",
                "country_origin": "Vietnam/France",
                "is_active": True
            },
            {
                "name": "Viet Vo Dao",
                "description": "Art martial vietnamien traditionnel qui met l'accent sur le développement de l'énergie interne, les mouvements fluides et précis. Les techniques comprennent des coups de pied acrobatiques, des frappes rapides et des enchaînements circulaires inspirés des mouvements animaux.",
                "country_origin": "Vietnam",
                "is_active": True
            },
            {
                "name": "Vo Co Truyen",
                "description": "Art martial vietnamien ancestral signifiant \"arts martiaux traditionnels\". Il met l'accent sur la préservation des techniques de combat authentiques transmises à travers les générations, incluant le travail des armes traditionnelles et les techniques à mains nues.",
                "country_origin": "Vietnam",
                "is_active": True
            },
            {
                "name": "Karaté",
                "description": "Art martial japonais basé sur des techniques de percussion utilisant différentes parties du corps. Il met l'accent sur la maîtrise technique, la discipline mentale et développe à la fois puissance et précision à travers différents katas codifiés.",
                "country_origin": "Japon (Okinawa)",
                "is_active": True
            },
            {
                "name": "Judo",
                "description": "Art martial japonais fondé par Jigoro Kano en 1882, orienté vers la compétition sportive. Il se caractérise par des techniques de projection, d'immobilisation, d'étranglement et de clés articulaires, mettant l'accent sur l'utilisation efficace de l'énergie.",
                "country_origin": "Japon",
                "is_active": True
            },
            {
                "name": "Taekwondo",
                "description": "Art martial coréen caractérisé par ses techniques de coups de pied spectaculaires, sautés et retournés. Devenu sport olympique, il combine un travail technique rigoureux avec des enchaînements dynamiques et acrobatiques.",
                "country_origin": "Corée",
                "is_active": True
            },
            {
                "name": "Kung Fu",
                "description": "Terme générique désignant les arts martiaux chinois traditionnels. Il englobe une grande diversité de styles (Wing Chun, Shaolin, Hung Gar, etc.) qui combinent travail interne et externe, avec des techniques inspirées des mouvements des animaux.",
                "country_origin": "Chine",
                "is_active": True
            },
            {
                "name": "Aïkido",
                "description": "Art martial japonais fondé par Morihei Ueshiba, basé sur le principe de non-résistance et d'harmonie avec l'énergie de l'adversaire. Les techniques consistent principalement à rediriger la force de l'attaquant à travers des mouvements circulaires.",
                "country_origin": "Japon",
                "is_active": True
            },
            {
                "name": "Jiu-Jitsu Brésilien",
                "description": "Art martial dérivé du judo et du jiu-jitsu traditionnel, développé par la famille Gracie. Il se spécialise dans le combat au sol et les techniques de soumission, avec une philosophie permettant au plus faible de vaincre un adversaire plus fort.",
                "country_origin": "Brésil",
                "is_active": True
            },
            {
                "name": "Muay Thaï",
                "description": "Boxe thaïlandaise utilisant poings, coudes, genoux et tibias comme armes naturelles. Surnommée \"l'art des huit membres\", elle est connue pour son efficacité en combat debout et ses techniques de corps-à-corps puissantes.",
                "country_origin": "Thaïlande",
                "is_active": True
            },
            {
                "name": "Krav Maga",
                "description": "Système d'autodéfense et de combat rapproché développé pour l'armée israélienne. Pragmatique et orienté vers l'efficacité réelle, il combine des techniques de différents arts martiaux et enseigne à neutraliser rapidement toute menace.",
                "country_origin": "Israël",
                "is_active": True
            },
            {
                "name": "Capoeira",
                "description": "Art martial afro-brésilien combinant combat, danse, acrobaties et musique. Développé par les esclaves africains au Brésil, il dissimule des techniques de combat efficaces derrière des mouvements artistiques et rythmés.",
                "country_origin": "Brésil",
                "is_active": True
            },
            {
                "name": "Wing Chun",
                "description": "Style de kung-fu développé selon la légende par une femme (Yim Wing Chun) et optimisé pour des combattants plus petits. Il privilégie l'économie de mouvements, la rapidité et les techniques à courte distance.",
                "country_origin": "Chine",
                "is_active": True
            },
            {
                "name": "Sambo",
                "description": "Art martial et sport de combat russe développé pour l'armée soviétique. Combinant lutte, judo et diverses techniques de combat traditionnelles, il est très efficace tant en lutte qu'en combat réel.",
                "country_origin": "Russie",
                "is_active": True
            },
            {
                "name": "Pencak Silat",
                "description": "Art martial traditionnel d'Indonésie comprenant de nombreux styles régionaux. Il combine self-défense, art et aspects spirituels avec des techniques fluides, explosives et des mouvements inspirés des animaux.",
                "country_origin": "Indonésie",
                "is_active": True
            },
            {
                "name": "Hapkido",
                "description": "Art martial coréen combinant techniques de frappe, projections, clés articulaires et utilisation d'armes traditionnelles. Il met l'accent sur les mouvements circulaires et la redirection de l'énergie de l'adversaire.",
                "country_origin": "Corée",
                "is_active": True
            },
            {
                "name": "Kyokushin",
                "description": "Style de karaté fondé par Masutatsu Oyama, connu pour sa rigueur et ses combats en plein contact sans protection. Il met l'accent sur l'endurance, la puissance et la condition physique à travers un entraînement intensif.",
                "country_origin": "Japon",
                "is_active": True
            },
            {
                "name": "Systema",
                "description": "Art martial russe axé sur le contrôle de la respiration, la relaxation et les mouvements naturels du corps. Développé pour les forces spéciales, il enseigne à adapter les techniques aux situations réelles sans formes codifiées.",
                "country_origin": "Russie",
                "is_active": True
            },
            {
                "name": "Bokator",
                "description": "Art martial cambodgien ancien datant de l'empire Khmer. Il comprend plus de 10,000 techniques et s'inspire des mouvements de différents animaux. Presque disparu pendant le régime des Khmers rouges, il connaît une renaissance.",
                "country_origin": "Cambodge",
                "is_active": True
            },
            {
                "name": "Ninjutsu",
                "description": "Art martial japonais traditionnel des ninjas, comprenant techniques de combat, d'espionnage et de survie. Il englobe 18 disciplines différentes incluant combat à mains nues, armes et tactiques de guerre psychologique.",
                "country_origin": "Japon",
                "is_active": True
            },
            {
                "name": "Kali/Escrima/Arnis",
                "description": "Arts martiaux philippins principalement axés sur le combat avec armes (bâtons, couteaux). Les techniques à mains nues dérivent des mouvements avec armes, rendant la transition naturelle et efficace.",
                "country_origin": "Philippines",
                "is_active": True
            },
            {
                "name": "Lethwei",
                "description": "Boxe birmane traditionnelle utilisant poings, pieds, genoux, coudes et même la tête. Combat sans gants (mains bandées), il est considéré comme l'un des sports de combat les plus brutaux et sans compromis.",
                "country_origin": "Birmanie (Myanmar)",
                "is_active": True
            },
            {
                "name": "Sanda/Sanshou",
                "description": "Boxe chinoise moderne développée à partir des techniques traditionnelles de kung-fu. Sport de combat complet combinant frappes et projections, elle est pratiquée en compétition avec protections.",
                "country_origin": "Chine",
                "is_active": True
            },
            {
                "name": "Tang Soo Do",
                "description": "Art martial coréen traditionnel préservant les influences chinoises et japonaises. Il combine des techniques de karaté, des mouvements fluides du kung-fu et des coups de pied dynamiques propres aux arts martiaux coréens.",
                "country_origin": "Corée",
                "is_active": True
            },
            {
                "name": "Panantukan",
                "description": "Boxe des Philippines axée sur les techniques de frappe à mains nues. Très efficace en combat rapproché, elle utilise toutes les parties du corps comme armes et cible les points vulnérables de l'adversaire.",
                "country_origin": "Philippines",
                "is_active": True
            },
            {
                "name": "Kendo",
                "description": "Art martial japonais moderne du sabre, dérivé des techniques de combat des samouraïs. Pratiqué avec armure (bogu) et sabre en bambou (shinai), il combine aspects techniques, spirituels et compétitifs.",
                "country_origin": "Japon",
                "is_active": True
            },
            {
                "name": "Iaido",
                "description": "Art martial japonais centré sur l'art de dégainer le sabre et de trancher en un seul mouvement fluide. Pratique traditionnelle axée sur la précision, la concentration et la perfection technique plutôt que sur le combat.",
                "country_origin": "Japon",
                "is_active": True
            },
            {
                "name": "Baguazhang",
                "description": "Art martial chinois interne caractérisé par ses mouvements circulaires et ses changements de direction, inspirés du principe du Tai Chi. Il utilise des déplacements en cercle et des techniques de paumes pour le combat.",
                "country_origin": "Chine",
                "is_active": True
            },
            {
                "name": "Kajukenbo",
                "description": "Art martial hybride américain créé à Hawaï, combinant Karaté, Judo/Jujitsu, Kenpo et Boxe chinoise. Système de défense personnelle complet intégrant frappes, projections, clés et combat au sol.",
                "country_origin": "États-Unis (Hawaï)",
                "is_active": True
            },
            {
                "name": "Dambe",
                "description": "Art martial traditionnel de l'ethnie Haoussa (Afrique de l'Ouest). Forme de boxe où le poing droit est enveloppé de corde et la main gauche sert de bouclier. Les coups de pied puissants sont également utilisés.",
                "country_origin": "Nigeria",
                "is_active": True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for discipline_data in disciplines:
            discipline, created = Discipline.objects.update_or_create(
                name=discipline_data["name"],
                defaults={
                    "description": discipline_data.get("description", ""),
                    "country_origin": discipline_data.get("country_origin", ""),
                    "is_active": discipline_data.get("is_active", True)
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Discipline '{discipline.name}' créée avec succès"))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"Discipline '{discipline.name}' mise à jour"))
        
        self.stdout.write(self.style.SUCCESS(f"Opération terminée: {created_count} disciplines créées, {updated_count} disciplines mises à jour"))