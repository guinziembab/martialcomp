from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from competitions.models import Practitioner, Discipline
from grades.models import Grade, GradeCategory, PractitionerGrade

class Command(BaseCommand):
    help = 'Migre les données des grades depuis les anciens modèles vers les nouveaux'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE(_("Début de la migration des données de grades...")))
        
        try:
            with transaction.atomic():
                # 1. Vérifier si des données existent déjà dans les nouvelles tables
                if Grade.objects.exists():
                    self.stdout.write(self.style.WARNING(
                        _("Des grades existent déjà dans le nouveau modèle. "
                          "La migration pourrait créer des doublons.")
                    ))
                    proceed = input("Voulez-vous continuer? (o/n): ")
                    if proceed.lower() != 'o':
                        self.stdout.write(self.style.ERROR(_("Migration annulée.")))
                        return
                
                self.stdout.write(self.style.NOTICE(_("Migration des données en cours...")))
                
                # 2. Créer les catégories de grade par discipline
                disciplines = Discipline.objects.all()
                for discipline in disciplines:
                    self.stdout.write(f"Traitement de la discipline: {discipline.name}")
                    
                    # Créer des catégories standard pour chaque discipline
                    categories = {
                        'Débutant': GradeCategory.objects.create(
                            name='Débutant',
                            description='Niveaux débutants',
                            discipline=discipline,
                            order=1,
                            is_active=True
                        ),
                        'Intermédiaire': GradeCategory.objects.create(
                            name='Intermédiaire',
                            description='Niveaux intermédiaires',
                            discipline=discipline,
                            order=2,
                            is_active=True
                        ),
                        'Avancé': GradeCategory.objects.create(
                            name='Avancé',
                            description='Niveaux avancés',
                            discipline=discipline,
                            order=3,
                            is_active=True
                        ),
                        'Expert': GradeCategory.objects.create(
                            name='Expert',
                            description='Niveaux experts (ceintures noires)',
                            discipline=discipline,
                            order=4,
                            is_active=True
                        ),
                    }
                    
                    # 3. Pour chaque discipline, créer les grades standards
                    # Cette partie doit être adaptée selon vos besoins spécifiques
                    if discipline.name.lower() in ['karate', 'karaté']:
                        self._create_karate_grades(discipline, categories)
                    elif discipline.name.lower() in ['judo']:
                        self._create_judo_grades(discipline, categories)
                    elif discipline.name.lower() in ['taekwondo']:
                        self._create_taekwondo_grades(discipline, categories)
                    elif discipline.name.lower() in ['kung fu', 'kung-fu']:
                        self._create_kungfu_grades(discipline, categories)
                    else:
                        # Grades génériques pour les autres disciplines
                        self._create_generic_grades(discipline, categories)
                
                # 4. Migrer les grades existants des pratiquants
                self._migrate_practitioner_grades()
                
                self.stdout.write(self.style.SUCCESS(_("Migration des données de grades terminée avec succès!")))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(_(f"Une erreur est survenue lors de la migration: {str(e)}")))
            raise
    
    def _create_karate_grades(self, discipline, categories):
        """Crée les grades standard pour le Karaté."""
        grades = [
            # Débutants
            {'name': 'Ceinture blanche', 'color': 'Blanche', 'color_code': '#FFFFFF', 'level': 1, 'category': categories['Débutant']},
            {'name': 'Ceinture jaune', 'color': 'Jaune', 'color_code': '#FFFF00', 'level': 2, 'category': categories['Débutant']},
            {'name': 'Ceinture orange', 'color': 'Orange', 'color_code': '#FFA500', 'level': 3, 'category': categories['Débutant']},
            
            # Intermédiaires
            {'name': 'Ceinture verte', 'color': 'Verte', 'color_code': '#008000', 'level': 4, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture bleue', 'color': 'Bleue', 'color_code': '#0000FF', 'level': 5, 'category': categories['Intermédiaire']},
            
            # Avancés
            {'name': 'Ceinture marron', 'color': 'Marron', 'color_code': '#8B4513', 'level': 6, 'category': categories['Avancé']},
            
            # Experts
            {'name': 'Ceinture noire 1er Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 7, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 2ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 8, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 3ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 9, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 4ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 10, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 5ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 11, 'category': categories['Expert'], 'is_dan_grade': True},
        ]
        
        for grade_data in grades:
            Grade.objects.create(
                discipline=discipline,
                **grade_data
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Créé: {grade_data['name']}"))
    
    def _create_judo_grades(self, discipline, categories):
        """Crée les grades standard pour le Judo."""
        grades = [
            # Débutants
            {'name': 'Ceinture blanche', 'color': 'Blanche', 'color_code': '#FFFFFF', 'level': 1, 'category': categories['Débutant']},
            {'name': 'Ceinture blanche-jaune', 'color': 'Blanche-jaune', 'color_code': '#FFFFCC', 'level': 2, 'category': categories['Débutant']},
            {'name': 'Ceinture jaune', 'color': 'Jaune', 'color_code': '#FFFF00', 'level': 3, 'category': categories['Débutant']},
            {'name': 'Ceinture jaune-orange', 'color': 'Jaune-orange', 'color_code': '#FFD700', 'level': 4, 'category': categories['Débutant']},
            {'name': 'Ceinture orange', 'color': 'Orange', 'color_code': '#FFA500', 'level': 5, 'category': categories['Débutant']},
            
            # Intermédiaires
            {'name': 'Ceinture orange-verte', 'color': 'Orange-verte', 'color_code': '#9ACD32', 'level': 6, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture verte', 'color': 'Verte', 'color_code': '#008000', 'level': 7, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture bleue', 'color': 'Bleue', 'color_code': '#0000FF', 'level': 8, 'category': categories['Intermédiaire']},
            
            # Avancés
            {'name': 'Ceinture marron', 'color': 'Marron', 'color_code': '#8B4513', 'level': 9, 'category': categories['Avancé']},
            
            # Experts
            {'name': 'Ceinture noire 1er Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 10, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 2ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 11, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 3ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 12, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 4ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 13, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 5ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 14, 'category': categories['Expert'], 'is_dan_grade': True},
        ]
        
        for grade_data in grades:
            Grade.objects.create(
                discipline=discipline,
                **grade_data
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Créé: {grade_data['name']}"))
    
    def _create_taekwondo_grades(self, discipline, categories):
        """Crée les grades standard pour le Taekwondo."""
        grades = [
            # Débutants
            {'name': 'Ceinture blanche (10ème Keup)', 'color': 'Blanche', 'color_code': '#FFFFFF', 'level': 1, 'category': categories['Débutant']},
            {'name': 'Ceinture blanche-jaune (9ème Keup)', 'color': 'Blanche-jaune', 'color_code': '#FFFFCC', 'level': 2, 'category': categories['Débutant']},
            {'name': 'Ceinture jaune (8ème Keup)', 'color': 'Jaune', 'color_code': '#FFFF00', 'level': 3, 'category': categories['Débutant']},
            {'name': 'Ceinture jaune-verte (7ème Keup)', 'color': 'Jaune-verte', 'color_code': '#9ACD32', 'level': 4, 'category': categories['Débutant']},
            
            # Intermédiaires
            {'name': 'Ceinture verte (6ème Keup)', 'color': 'Verte', 'color_code': '#008000', 'level': 5, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture verte-bleue (5ème Keup)', 'color': 'Verte-bleue', 'color_code': '#20B2AA', 'level': 6, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture bleue (4ème Keup)', 'color': 'Bleue', 'color_code': '#0000FF', 'level': 7, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture bleue-rouge (3ème Keup)', 'color': 'Bleue-rouge', 'color_code': '#9370DB', 'level': 8, 'category': categories['Intermédiaire']},
            
            # Avancés
            {'name': 'Ceinture rouge (2ème Keup)', 'color': 'Rouge', 'color_code': '#FF0000', 'level': 9, 'category': categories['Avancé']},
            {'name': 'Ceinture rouge-noire (1er Keup)', 'color': 'Rouge-noire', 'color_code': '#8B0000', 'level': 10, 'category': categories['Avancé']},
            
            # Experts
            {'name': 'Ceinture noire 1er Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 11, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 2ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 12, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 3ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 13, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 4ème Dan', 'color': 'Noire', 'color_code': '#000000', 'level': 14, 'category': categories['Expert'], 'is_dan_grade': True},
        ]
        
        for grade_data in grades:
            Grade.objects.create(
                discipline=discipline,
                **grade_data
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Créé: {grade_data['name']}"))
    
    def _create_kungfu_grades(self, discipline, categories):
        """Crée les grades standard pour le Kung Fu."""
        grades = [
            # Débutants
            {'name': 'Ceinture blanche', 'color': 'Blanche', 'color_code': '#FFFFFF', 'level': 1, 'category': categories['Débutant']},
            {'name': 'Ceinture jaune', 'color': 'Jaune', 'color_code': '#FFFF00', 'level': 2, 'category': categories['Débutant']},
            
            # Intermédiaires
            {'name': 'Ceinture verte', 'color': 'Verte', 'color_code': '#008000', 'level': 3, 'category': categories['Intermédiaire']},
            {'name': 'Ceinture bleue', 'color': 'Bleue', 'color_code': '#0000FF', 'level': 4, 'category': categories['Intermédiaire']},
            
            # Avancés
            {'name': 'Ceinture rouge', 'color': 'Rouge', 'color_code': '#FF0000', 'level': 5, 'category': categories['Avancé']},
            {'name': 'Ceinture marron', 'color': 'Marron', 'color_code': '#8B4513', 'level': 6, 'category': categories['Avancé']},
            
            # Experts
            {'name': 'Ceinture noire 1er Duan', 'color': 'Noire', 'color_code': '#000000', 'level': 7, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 2ème Duan', 'color': 'Noire', 'color_code': '#000000', 'level': 8, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 3ème Duan', 'color': 'Noire', 'color_code': '#000000', 'level': 9, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 4ème Duan', 'color': 'Noire', 'color_code': '#000000', 'level': 10, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Ceinture noire 5ème Duan', 'color': 'Noire', 'color_code': '#000000', 'level': 11, 'category': categories['Expert'], 'is_dan_grade': True},
        ]
        
        for grade_data in grades:
            Grade.objects.create(
                discipline=discipline,
                **grade_data
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Créé: {grade_data['name']}"))
    
    def _create_generic_grades(self, discipline, categories):
        """Crée des grades génériques pour les disciplines qui n'ont pas de système spécifique."""
        grades = [
            # Débutants
            {'name': 'Niveau 1 - Débutant', 'color': 'Blanc', 'color_code': '#FFFFFF', 'level': 1, 'category': categories['Débutant']},
            {'name': 'Niveau 2 - Débutant avancé', 'color': 'Jaune', 'color_code': '#FFFF00', 'level': 2, 'category': categories['Débutant']},
            
            # Intermédiaires
            {'name': 'Niveau 3 - Intermédiaire', 'color': 'Vert', 'color_code': '#008000', 'level': 3, 'category': categories['Intermédiaire']},
            {'name': 'Niveau 4 - Intermédiaire avancé', 'color': 'Bleu', 'color_code': '#0000FF', 'level': 4, 'category': categories['Intermédiaire']},
            
            # Avancés
            {'name': 'Niveau 5 - Avancé', 'color': 'Marron', 'color_code': '#8B4513', 'level': 5, 'category': categories['Avancé']},
            {'name': 'Niveau 6 - Avancé supérieur', 'color': 'Rouge', 'color_code': '#FF0000', 'level': 6, 'category': categories['Avancé']},
            
            # Experts
            {'name': 'Niveau 7 - Expert 1er degré', 'color': 'Noir', 'color_code': '#000000', 'level': 7, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Niveau 8 - Expert 2ème degré', 'color': 'Noir', 'color_code': '#000000', 'level': 8, 'category': categories['Expert'], 'is_dan_grade': True},
            {'name': 'Niveau 9 - Expert 3ème degré', 'color': 'Noir', 'color_code': '#000000', 'level': 9, 'category': categories['Expert'], 'is_dan_grade': True},
        ]
        
        for grade_data in grades:
            Grade.objects.create(
                discipline=discipline,
                **grade_data
            )
            self.stdout.write(self.style.SUCCESS(f"  ✓ Créé: {grade_data['name']}"))
    
    def _migrate_practitioner_grades(self):
        """Migre les grades des pratiquants depuis l'ancien système."""
        self.stdout.write(self.style.NOTICE(_("Migration des grades des pratiquants...")))
        
        try:
            # Vérifier si l'ancien modèle existe encore
            # Cette partie doit être adaptée selon votre configuration actuelle
            
            # Si l'ancien modèle n'existe plus, on peut seulement créer les grades actuels
            practitioners = Practitioner.objects.all()
            count = 0
            
            for practitioner in practitioners:
                # Si le pratiquant a un grade défini
                if hasattr(practitioner, 'grade') and practitioner.grade:
                    try:
                        # Trouver la discipline du pratiquant (prendre la première si plusieurs)
                        disciplines = practitioner.disciplines.all()
                        if not disciplines.exists():
                            continue
                        
                        discipline = disciplines.first()
                        
                        # Chercher un grade similaire dans le nouveau système
                        grade_name = practitioner.grade.lower()
                        
                        # Essayez de trouver un grade correspondant
                        matching_grades = Grade.objects.filter(
                            discipline=discipline,
                            name__icontains=grade_name
                        )
                        
                        if matching_grades.exists():
                            grade = matching_grades.first()
                            
                            # Créer le grade du pratiquant
                            PractitionerGrade.objects.create(
                                practitioner=practitioner,
                                grade=grade,
                                discipline=discipline,
                                is_current=True
                            )
                            
                            count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(
                            f"Erreur lors de la migration du grade pour {practitioner.full_name}: {str(e)}"
                        ))
            
            self.stdout.write(self.style.SUCCESS(f"Migrés {count} grades de pratiquants sur {practitioners.count()} pratiquants"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors de la migration des grades des pratiquants: {str(e)}"))