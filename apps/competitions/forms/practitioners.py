from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, FileExtensionValidator
from django.db.models import Q
from django.contrib.auth.models import User
import json
from django.utils import timezone
from django.db import transaction

from ..models import (
    Practitioner,
    PractitionerDiscipline,
    MedicalRecord,
    Discipline,
    Club,
    Judge,
    QUALIFICATION_LEVELS,
)

from apps.competitions.models import Club, Practitioner, Discipline
from apps.grades.models import Grade, PractitionerGrade
# Import LicenseNumberGenerator depuis le module services
from apps.competitions.services import LicenseNumberGenerator
# Import des helpers de filtrage par discipline
from apps.competitions.utils.permission_helpers import (
    get_user_disciplines,
    get_user_organization,
    filter_queryset_by_user_disciplines
)

# Liste des pays pour le champ nationalité
COUNTRY_CHOICES = [
    ('', _('-- Sélectionnez un pays --')),
    ('AF', _('Afghanistan')),
    ('ZA', _('Afrique du Sud')),
    ('AL', _('Albanie')),
    ('DZ', _('Algérie')),
    ('DE', _('Allemagne')),
    ('AD', _('Andorre')),
    ('AO', _('Angola')),
    ('AI', _('Anguilla')),
    ('AQ', _('Antarctique')),
    ('AG', _('Antigua-et-Barbuda')),
    ('SA', _('Arabie saoudite')),
    ('AR', _('Argentine')),
    ('AM', _('Arménie')),
    ('AW', _('Aruba')),
    ('AU', _('Australie')),
    ('AT', _('Autriche')),
    ('AZ', _('AzerbaÃ¯djan')),
    ('BS', _('Bahamas')),
    ('BH', _('BahreÃ¯n')),
    ('BD', _('Bangladesh')),
    ('BB', _('Barbade')),
    ('BY', _('Biélorussie')),
    ('BE', _('Belgique')),
    ('BZ', _('Belize')),
    ('BJ', _('Bénin')),
    ('BM', _('Bermudes')),
    ('BT', _('Bhoutan')),
    ('BO', _('Bolivie')),
    ('BA', _('Bosnie-Herzégovine')),
    ('BW', _('Botswana')),
    ('BR', _('Brésil')),
    ('BN', _('Brunei')),
    ('BG', _('Bulgarie')),
    ('BF', _('Burkina Faso')),
    ('BI', _('Burundi')),
    ('KH', _('Cambodge')),
    ('CM', _('Cameroun')),
    ('CA', _('Canada')),
    ('CV', _('Cap-Vert')),
    ('CL', _('Chili')),
    ('CN', _('Chine')),
    ('CY', _('Chypre')),
    ('CO', _('Colombie')),
    ('KM', _('Comores')),
    ('CG', _('Congo')),
    ('CD', _('Congo (Rép. dém.)')),
    ('KR', _('Corée du Sud')),
    ('KP', _('Corée du Nord')),
    ('CR', _('Costa Rica')),
    ('CI', _('CÃ´te d\'Ivoire')),
    ('HR', _('Croatie')),
    ('CU', _('Cuba')),
    ('DK', _('Danemark')),
    ('DJ', _('Djibouti')),
    ('DM', _('Dominique')),
    ('EG', _('Ã‰gypte')),
    ('AE', _('Ã‰mirats arabes unis')),
    ('EC', _('Ã‰quateur')),
    ('ER', _('Ã‰rythrée')),
    ('ES', _('Espagne')),
    ('EE', _('Estonie')),
    ('US', _('Ã‰tats-Unis')),
    ('ET', _('Ã‰thiopie')),
    ('FJ', _('Fidji')),
    ('FI', _('Finlande')),
    ('FR', _('France')),
    ('GA', _('Gabon')),
    ('GM', _('Gambie')),
    ('GE', _('Géorgie')),
    ('GH', _('Ghana')),
    ('GI', _('Gibraltar')),
    ('GR', _('Grèce')),
    ('GD', _('Grenade')),
    ('GL', _('Groenland')),
    ('GP', _('Guadeloupe')),
    ('GU', _('Guam')),
    ('GT', _('Guatemala')),
    ('GN', _('Guinée')),
    ('GW', _('Guinée-Bissau')),
    ('GQ', _('Guinée équatoriale')),
    ('GY', _('Guyana')),
    ('GF', _('Guyane française')),
    ('HT', _('HaÃ¯ti')),
    ('HN', _('Honduras')),
    ('HK', _('Hong Kong')),
    ('HU', _('Hongrie')),
    ('IN', _('Inde')),
    ('ID', _('Indonésie')),
    ('IQ', _('Irak')),
    ('IR', _('Iran')),
    ('IE', _('Irlande')),
    ('IS', _('Islande')),
    ('IL', _('IsraÃ«l')),
    ('IT', _('Italie')),
    ('JM', _('JamaÃ¯que')),
    ('JP', _('Japon')),
    ('JO', _('Jordanie')),
    ('KZ', _('Kazakhstan')),
    ('KE', _('Kenya')),
    ('KG', _('Kirghizistan')),
    ('KI', _('Kiribati')),
    ('KW', _('KoweÃ¯t')),
    ('LA', _('Laos')),
    ('LS', _('Lesotho')),
    ('LV', _('Lettonie')),
    ('LB', _('Liban')),
    ('LR', _('Libéria')),
    ('LY', _('Libye')),
    ('LI', _('Liechtenstein')),
    ('LT', _('Lituanie')),
    ('LU', _('Luxembourg')),
    ('MO', _('Macao')),
    ('MK', _('Macédoine du Nord')),
    ('MG', _('Madagascar')),
    ('MY', _('Malaisie')),
    ('MW', _('Malawi')),
    ('MV', _('Maldives')),
    ('ML', _('Mali')),
    ('MT', _('Malte')),
    ('MA', _('Maroc')),
    ('MH', _('ÃŽles Marshall')),
    ('MQ', _('Martinique')),
    ('MU', _('Maurice')),
    ('MR', _('Mauritanie')),
    ('YT', _('Mayotte')),
    ('MX', _('Mexique')),
    ('FM', _('Micronésie')),
    ('MD', _('Moldavie')),
    ('MC', _('Monaco')),
    ('MN', _('Mongolie')),
    ('ME', _('Monténégro')),
    ('MS', _('Montserrat')),
    ('MZ', _('Mozambique')),
    ('MM', _('Myanmar')),
    ('NA', _('Namibie')),
    ('NR', _('Nauru')),
    ('NP', _('Népal')),
    ('NI', _('Nicaragua')),
    ('NE', _('Niger')),
    ('NG', _('Nigeria')),
    ('NU', _('Niue')),
    ('NF', _('ÃŽle Norfolk')),
    ('NO', _('Norvège')),
    ('NC', _('Nouvelle-Calédonie')),
    ('NZ', _('Nouvelle-Zélande')),
    ('OM', _('Oman')),
    ('UG', _('Ouganda')),
    ('UZ', _('Ouzbékistan')),
    ('PK', _('Pakistan')),
    ('PW', _('Palaos')),
    ('PS', _('Palestine')),
    ('PA', _('Panama')),
    ('PG', _('Papouasie-Nouvelle-Guinée')),
    ('PY', _('Paraguay')),
    ('NL', _('Pays-Bas')),
    ('PE', _('Pérou')),
    ('PH', _('Philippines')),
    ('PN', _('Pitcairn')),
    ('PL', _('Pologne')),
    ('PF', _('Polynésie française')),
    ('PR', _('Porto Rico')),
    ('PT', _('Portugal')),
    ('QA', _('Qatar')),
    ('RE', _('Réunion')),
    ('RO', _('Roumanie')),
    ('GB', _('Royaume-Uni')),
    ('RU', _('Russie')),
    ('RW', _('Rwanda')),
    ('EH', _('Sahara occidental')),
    ('BL', _('Saint-Barthélemy')),
    ('KN', _('Saint-Kitts-et-Nevis')),
    ('SM', _('Saint-Marin')),
    ('MF', _('Saint-Martin')),
    ('PM', _('Saint-Pierre-et-Miquelon')),
    ('VA', _('Saint-Siège')),
    ('VC', _('Saint-Vincent-et-les-Grenadines')),
    ('LC', _('Sainte-Lucie')),
    ('SB', _('Salomon')),
    ('WS', _('Samoa')),
    ('AS', _('Samoa américaines')),
    ('ST', _('Sao Tomé-et-Principe')),
    ('SN', _('Sénégal')),
    ('RS', _('Serbie')),
    ('SC', _('Seychelles')),
    ('SL', _('Sierra Leone')),
    ('SG', _('Singapour')),
    ('SK', _('Slovaquie')),
    ('SI', _('Slovénie')),
    ('SO', _('Somalie')),
    ('SD', _('Soudan')),
    ('SS', _('Soudan du Sud')),
    ('LK', _('Sri Lanka')),
    ('SE', _('Suède')),
    ('CH', _('Suisse')),
    ('SR', _('Suriname')),
    ('SJ', _('Svalbard et Jan Mayen')),
    ('SZ', _('Eswatini')),
    ('SY', _('Syrie')),
    ('TJ', _('Tadjikistan')),
    ('TW', _('TaÃ¯wan')),
    ('TZ', _('Tanzanie')),
    ('TD', _('Tchad')),
    ('CZ', _('Tchéquie')),
    ('TF', _('Terres australes françaises')),
    ('IO', _('Territoire britannique de l\'océan Indien')),
    ('TH', _('ThaÃ¯lande')),
    ('TL', _('Timor oriental')),
    ('TG', _('Togo')),
    ('TK', _('Tokelau')),
    ('TO', _('Tonga')),
    ('TT', _('Trinité-et-Tobago')),
    ('TN', _('Tunisie')),
    ('TM', _('Turkménistan')),
    ('TC', _('ÃŽles Turques-et-CaÃ¯ques')),
    ('TR', _('Turquie')),
    ('TV', _('Tuvalu')),
    ('UA', _('Ukraine')),
    ('UY', _('Uruguay')),
    ('VU', _('Vanuatu')),
    ('VE', _('Venezuela')),
    ('VN', _('ViÃªt Nam')),
    ('WF', _('Wallis-et-Futuna')),
    ('YE', _('Yémen')),
    ('ZM', _('Zambie')),
    ('ZW', _('Zimbabwe')),
]

class PractitionerForm(forms.ModelForm):
    """
    Formulaire pour la création et la modification des pratiquants.
    """
    # Champ pour la sélection des disciplines - sera filtré dans __init__
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.none(),  # Securite: queryset vide par defaut
        label=_("Disciplines pratiquées"),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '4',
            'id': 'id_disciplines',
            'onchange': 'updateGrades()'
        })
    )
    
    # Champ grade simple
    grade = forms.CharField(
        label=_("Grade"),
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Ex: Ceinture noire 1er dan")})
    )
    
    # Champ pour la sélection des grades avancés
    grade_selection = forms.ModelChoiceField(
        queryset=None,  # Sera configuré dans __init__
        label=_("Grade détaillé (optionnel)"),
        required=False,
        empty_label=_("-- Sélectionnez un grade --"),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_grade_selection',
            'data-depends-on': 'disciplines'
        }),
        help_text=_("Sélectionnez un grade pour une meilleure gestion des promotions")
    )
    
    # Validation des fichiers
    photo = forms.ImageField(
        label=_("Photo de profil"),
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    medical_certificate = forms.FileField(
        label=_("Certificat médical"),
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    parental_authorization = forms.FileField(
        label=_("Autorisation parentale"),
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    # ===== PROMPT 7: Champs pour la qualification de juge =====
    is_judge = forms.BooleanField(
        label=_("Ce pratiquant est un juge"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_judge'})
    )

    is_technical_judge = forms.BooleanField(
        label=_("Juge technique"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    is_combat_referee = forms.BooleanField(
        label=_("Arbitre de combat"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    judge_qualification_level = forms.ChoiceField(
        label=_("Niveau de qualification"),
        choices=[('', _('-- Sélectionnez un niveau --'))] + list(QUALIFICATION_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    judge_years_experience = forms.IntegerField(
        label=_("Années d'expérience"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )

    judge_certification_number = forms.CharField(
        label=_("Numéro de certification"),
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    judge_certified_since = forms.DateField(
        label=_("Certifié depuis"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    judge_active = forms.BooleanField(
        label=_("Juge actif"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    judge_notes = forms.CharField(
        label=_("Notes sur la qualification de juge"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': '3'})
    )

    def __init__(self, *args, **kwargs):
        # Extraire request si fourni
        self.request = kwargs.pop('request', None)
        # Extraire user et organization pour le filtrage par discipline
        self.user = kwargs.pop('user', None)
        self.organization = kwargs.pop('organization', None)

        # Log pour debug
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"PractitionerForm.__init__ appelé avec args={args}, kwargs keys={kwargs.keys()}")

        # Appeler directement super().__init__() - Django gère correctement les arguments
        super().__init__(*args, **kwargs)

        # Protection supplémentaire au cas où
        if hasattr(self, 'data') and isinstance(self.data, str):
            from django.http import QueryDict
            self.data = QueryDict('')

        # PHASE 1 SECURITY: Filtrer les disciplines par organisation
        self._configure_discipline_queryset()

        # Configurer le queryset pour grade_selection
        self._configure_grade_queryset()
        
        # Pré-remplir les champs si le pratiquant existe
        if self.instance.pk:
            self._prefill_grade_fields()
            self._prefill_judge_fields()
            # La date de naissance est automatiquement pré-remplie par Django via le widget
            # Pré-remplir les disciplines
            if self.instance.disciplines.exists():
                self.fields['disciplines'].initial = self.instance.disciplines.all()
        
        # Génération automatique du numéro de licence si champ vide
        try:
            # Protection contre l'erreur 'str' object has no attribute 'get'
            # Maintenant self.data et self.initial sont garantis d'être des dict/QueryDict
            if not self.initial.get('license_number') and not self.data.get('license_number'):
                # On tente de générer une valeur par défaut
                birth_date = self.initial.get('birth_date') or self.data.get('birth_date')
                club = self.initial.get('club') or self.data.get('club')
                discipline = self.initial.get('discipline') or self.data.get('discipline')
                # Utiliser le générateur si possible
                try:
                    from apps.competitions.models import Club, Discipline
                    club_obj = Club.objects.filter(id=club).first() if club else None
                    discipline_obj = Discipline.objects.filter(id=discipline).first() if discipline else None
                    value = LicenseNumberGenerator.generate(
                        club_id=club_obj.id if club_obj else None,
                        discipline_id=discipline_obj.id if discipline_obj else None,
                        birth_date=birth_date
                    )
                    if hasattr(self.initial, '__setitem__'):
                        self.initial['license_number'] = value
                except Exception:
                    pass
        except (AttributeError, TypeError) as e:
            # Si une erreur survient, ignorer silencieusement
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur lors de la génération du numéro de licence: {str(e)}")
            pass

    def _configure_discipline_queryset(self):
        """PHASE 1 SECURITY: Configure le queryset des disciplines filtré par organisation."""
        import logging
        logger = logging.getLogger('discipline_isolation')

        # Determiner l'utilisateur
        user = self.user
        if not user and self.request and hasattr(self.request, 'user'):
            user = self.request.user

        if not user or not user.is_authenticated:
            # Pas d'utilisateur = pas de disciplines
            self.fields['disciplines'].queryset = Discipline.objects.none()
            logger.warning("PractitionerForm: No authenticated user - disciplines queryset empty")
            return

        if user.is_superuser:
            # Superuser voit toutes les disciplines actives
            self.fields['disciplines'].queryset = Discipline.objects.filter(is_active=True)
            return

        try:
            # Utiliser les helpers pour obtenir les disciplines accessibles
            accessible_disciplines = get_user_disciplines(user, self.organization)

            if accessible_disciplines.exists():
                self.fields['disciplines'].queryset = accessible_disciplines
            else:
                # Fallback: disciplines du club de l'utilisateur
                club = Club.objects.filter(owner=user).first()
                if club and hasattr(club, 'disciplines'):
                    self.fields['disciplines'].queryset = club.disciplines.filter(is_active=True)
                else:
                    self.fields['disciplines'].queryset = Discipline.objects.none()
                    logger.warning(f"PractitionerForm: User {user} has no accessible disciplines")

        except Exception as e:
            # SECURITE: En cas d'erreur, queryset vide
            logger.critical(f"PractitionerForm discipline filtering FAILED for {user}: {e}")
            self.fields['disciplines'].queryset = Discipline.objects.none()

    def _configure_grade_queryset(self):
        """PHASE 1 SECURITY: Configure le queryset pour le champ grade_selection filtré par discipline."""
        import logging
        logger = logging.getLogger('discipline_isolation')

        try:
            grade_queryset = Grade.objects.filter(is_active=True)

            # Determiner l'utilisateur
            user = self.user
            if not user and self.request and hasattr(self.request, 'user'):
                user = self.request.user

            if user and user.is_authenticated and not user.is_superuser:
                # PHASE 1 SECURITY: Filtrer les grades par disciplines accessibles
                accessible_disciplines = get_user_disciplines(user, self.organization)
                if accessible_disciplines.exists():
                    grade_queryset = grade_queryset.filter(discipline__in=accessible_disciplines)
                else:
                    # Fallback: disciplines du club de l'utilisateur
                    club = Club.objects.filter(owner=user).first()
                    if club and hasattr(club, 'disciplines') and club.disciplines.exists():
                        grade_queryset = grade_queryset.filter(discipline__in=club.disciplines.all())
                    else:
                        # SECURITE: Aucune discipline = aucun grade
                        grade_queryset = Grade.objects.none()
                        logger.warning(f"PractitionerForm: User {user} has no accessible grades")

            self.fields['grade_selection'].queryset = grade_queryset.order_by('discipline', 'level')

        except Exception as e:
            # SECURITE: En cas d'erreur, queryset vide
            logger.critical(f"PractitionerForm grade filtering FAILED: {e}")
            self.fields['grade_selection'].queryset = Grade.objects.none()

        # Filtrer les clubs selon l'utilisateur si le champ club existe
        if 'club' in self.fields and self.request and hasattr(self.request, 'user'):
            user = self.request.user
            if hasattr(user, 'profile') and user.profile.role == 'club_manager':
                self.fields['club'].queryset = Club.objects.filter(owner=user)
            else:
                self.fields['club'].queryset = Club.objects.all()
    
    def _prefill_grade_fields(self):
        """Pré-remplit les champs de grade si le pratiquant existe."""
        try:
            from apps.grades.models import PractitionerGrade
            # Récupérer le grade principal (le plus élevé par niveau)
            current_grade = PractitionerGrade.objects.filter(
                practitioner=self.instance,
                is_current=True
            ).select_related('grade', 'grade__discipline').order_by('-grade__level').first()
            
            if current_grade and current_grade.grade:
                self.fields['grade_selection'].initial = current_grade.grade
                self.fields['grade'].initial = current_grade.grade.name
            elif self.instance.grade:
                # Fallback : utiliser le champ grade du pratiquant
                self.fields['grade'].initial = self.instance.grade if isinstance(self.instance.grade, str) else getattr(self.instance.grade, 'name', '')
        except ImportError:
            # Si le module grades n'est pas disponible, utiliser le champ grade simple
            if self.instance.grade:
                self.fields['grade'].initial = self.instance.grade if isinstance(self.instance.grade, str) else getattr(self.instance.grade, 'name', '')
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Erreur lors du pré-remplissage des grades: {str(e)}")
            # En cas d'erreur, utiliser le champ grade simple
            if self.instance.grade:
                self.fields['grade'].initial = self.instance.grade if isinstance(self.instance.grade, str) else getattr(self.instance.grade, 'name', '')

    def _prefill_judge_fields(self):
        """PROMPT 7: Pré-remplit les champs de juge si le pratiquant a un profil juge."""
        try:
            if hasattr(self.instance, 'judge'):
                judge = self.instance.judge
                self.fields['is_judge'].initial = True
                self.fields['is_technical_judge'].initial = judge.is_technical_judge
                self.fields['is_combat_referee'].initial = judge.is_combat_referee
                self.fields['judge_qualification_level'].initial = judge.qualification_level
                self.fields['judge_years_experience'].initial = judge.years_experience
                self.fields['judge_certification_number'].initial = judge.certification_number
                self.fields['judge_certified_since'].initial = judge.certified_since
                self.fields['judge_active'].initial = judge.active
                self.fields['judge_notes'].initial = judge.notes
        except Exception:
            # Pas de profil juge, laisser les valeurs par défaut
            pass

    class Meta:
        model = Practitioner
        fields = [
            # Informations de base
            'first_name', 'last_name', 'birth_date', 'gender', 'photo', 'email', 'phone',
            
            # Identité et documents
            'nationality', 'birth_place', 'license_number', 'medical_certificate_date', 
            'medical_certificate', 'parental_authorization',
            
            # Adresse
            'address', 'city', 'postal_code',
            
            # Contact d'urgence
            'emergency_contact_name', 'emergency_contact_relation', 
            'emergency_contact_phone', 'emergency_contact_email',
            
            # Informations médicales
            'blood_group', 'weight', 'height', 'allergies', 'medical_conditions',
            
            # Sportif
            'disciplines', 'grade',
            
            # Autres
            'notes'
        ]
        widgets = {
            # Informations de base
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Identité et documents
            'nationality': forms.Select(choices=COUNTRY_CHOICES, attrs={'class': 'form-select'}),
            'birth_place': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_certificate_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            
            # Adresse
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            
            # Contact d'urgence
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            
            # Informations médicales
            'blood_group': forms.TextInput(attrs={'class': 'form-control'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            
            # Autres
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'})
        }
    
    def clean_birth_date(self):
        """Validation spéciale pour la date de naissance."""
        birth_date = self.cleaned_data.get('birth_date')
        
        # Vérifier que la date est fournie
        if not birth_date:
            raise forms.ValidationError(_("La date de naissance est requise."))
        
        # Vérifier que la date n'est pas dans le futur
        today = timezone.now().date()
        if birth_date > today:
            raise forms.ValidationError(_("La date de naissance ne peut pas Ãªtre dans le futur."))
        
        # Note: La validation de l'âge minimum est désormais gérée au niveau des catégories
        # de compétition, pas au niveau du pratiquant. Un pratiquant de tout âge peut être
        # enregistré, mais son éligibilité aux compétitions dépend des critères de catégorie.

        return birth_date
    
    def clean_grade(self):
        """Validation et nettoyage du champ grade."""
        grade = self.cleaned_data.get('grade')
        if grade and grade.strip():
            return grade.strip()
        return None
    
    def clean_photo(self):
        """Validation de la photo."""
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > 5 * 1024 * 1024:  # 5 MB
                raise forms.ValidationError(_("La taille de l'image ne doit pas dépasser 5 Mo"))
        return photo
    
    def clean_medical_certificate(self):
        """Validation du certificat médical."""
        certificate = self.cleaned_data.get('medical_certificate')
        if certificate:
            if certificate.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 10 Mo"))
        return certificate
    
    def clean_parental_authorization(self):
        """Validation de l'autorisation parentale."""
        authorization = self.cleaned_data.get('parental_authorization')
        if authorization:
            if authorization.size > 10 * 1024 * 1024:  # 10 MB
                raise forms.ValidationError(_("La taille du fichier ne doit pas dépasser 10 Mo"))
        return authorization
    
    def save(self, commit=True):
        practitioner = super().save(commit=commit)

        if commit:
            # Sauvegarder les grades
            self._save_grades(practitioner)
            # Sauvegarder les disciplines
            self._save_disciplines(practitioner)
            # PROMPT 7: Sauvegarder les données de juge
            self._save_judge_data(practitioner)

        return practitioner
    
    def _save_grades(self, practitioner):
        """Sauvegarde les informations de grades du pratiquant."""
        # Sauvegarder le grade si sélectionné
        grade_selection = self.cleaned_data.get('grade_selection')
        
        if grade_selection:
            # Mettre Ã  jour le champ grade (string) du pratiquant
            practitioner.grade = grade_selection
            practitioner.save()
            # Mettre à jour aussi le champ grade_text pour compatibilité
            if hasattr(practitioner, "grade_text"):
                practitioner.grade_text = grade_selection.name
            
            # Créer ou mettre Ã  jour l'entrée PractitionerGrade si le module est disponible
            try:
                with transaction.atomic():
                    # Désactiver les grades actuels pour cette discipline
                    PractitionerGrade.objects.filter(
                        practitioner=practitioner,
                        discipline=grade_selection.discipline,
                        is_current=True
                    ).update(is_current=False)
                    
                    # Créer ou mettre Ã  jour le nouveau grade
                    # Supprimer les doublons eventuels avant update_or_create
                    duplicates = PractitionerGrade.objects.filter(
                        practitioner=practitioner,
                        grade=grade_selection,
                        discipline=grade_selection.discipline,
                    )
                    if duplicates.count() > 1:
                        keep = duplicates.order_by('-date_obtained').first()
                        duplicates.exclude(pk=keep.pk).delete()

                    # Creer ou mettre a jour le nouveau grade
                    PractitionerGrade.objects.update_or_create(
                        practitioner=practitioner,
                        grade=grade_selection,
                        discipline=grade_selection.discipline,
                        defaults={
                            'is_current': True,
                            'date_obtained': timezone.now().date()
                        }
                    )
            except ImportError:
                # Si le module grades n'est pas disponible, continuer sans erreur
                pass
        else:
            # Si aucun grade sélectionné mais qu'il y a une valeur dans le champ simple
            # Note: Le champ grade est un ForeignKey, donc on ne peut pas assigner directement une chaîne
            # On met à jour seulement grade_text si disponible
            grade_value = self.cleaned_data.get('grade')
            if grade_value and hasattr(practitioner, 'grade_text'):
                practitioner.grade_text = grade_value
                practitioner.save()
    
    def _save_disciplines(self, practitioner):
        """Sauvegarde les disciplines du pratiquant."""
        disciplines = self.cleaned_data.get('disciplines')
        if disciplines:
            practitioner.disciplines.set(disciplines)

    def _save_judge_data(self, practitioner):
        """PROMPT 7: Sauvegarde les données de qualification de juge."""
        is_judge = self.cleaned_data.get('is_judge')

        if is_judge:
            # Créer ou mettre à jour le profil juge
            judge_data = {
                'is_technical_judge': self.cleaned_data.get('is_technical_judge', False),
                'is_combat_referee': self.cleaned_data.get('is_combat_referee', False),
                'qualification_level': self.cleaned_data.get(
                    'judge_qualification_level', 'novice'
                ) or 'novice',
                'years_experience': self.cleaned_data.get('judge_years_experience') or 0,
                'certification_number': self.cleaned_data.get(
                    'judge_certification_number', ''
                ) or '',
                'certified_since': self.cleaned_data.get('judge_certified_since'),
                'active': self.cleaned_data.get('judge_active', True),
                'notes': self.cleaned_data.get('judge_notes', '') or '',
            }

            # Si le pratiquant a un utilisateur associé, l'ajouter au juge
            if practitioner.user:
                judge_data['user'] = practitioner.user

            try:
                Judge.objects.update_or_create(
                    practitioner=practitioner,
                    defaults=judge_data
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erreur lors de la sauvegarde du profil juge: {str(e)}")
        else:
            # Si is_judge n'est pas coché, supprimer le profil juge s'il existe
            try:
                if hasattr(practitioner, 'judge'):
                    practitioner.judge.delete()
            except Exception:
                pass


class PractitionerBasicForm(forms.ModelForm):
    """
    Formulaire simplifié pour les pratiquants, avec uniquement 
    les champs nécessaires pour les compétitions.
    """
    
    class Meta:
        model = Practitioner
        fields = [
            'first_name', 'last_name', 'birth_date', 'gender', 
            'grade', 'license_number', 'email', 'medical_certificate_date'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'grade': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'medical_certificate_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class MedicalRecordForm(forms.ModelForm):
    """
    Formulaire pour le dossier médical du pratiquant.
    """
    
    class Meta:
        model = MedicalRecord
        exclude = ['practitioner']
        widgets = {
            'last_visit_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'doctor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'doctor_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_type': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'chronic_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'current_medications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'previous_injuries': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'restrictions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_protocols': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'confidential_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PractitionerDisciplineForm(forms.ModelForm):
    """
    Formulaire pour ajouter ou modifier les disciplines pratiquées par un pratiquant.
    """
    
    class Meta:
        model = PractitionerDiscipline
        exclude = ['practitioner']
        widgets = {
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'current_grade': forms.TextInput(attrs={'class': 'form-control'}),
            'grade_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reference_instructor': forms.Select(attrs={'class': 'form-control'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class CreateUserForPractitionerForm(forms.Form):
    """
    Formulaire pour créer un utilisateur pour un pratiquant existant.
    """
    
    username = forms.CharField(
        label=_("Nom d'utilisateur"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text=_("Requis. 150 caractères maximum. Lettres, chiffres et @/./+/-/_ uniquement.")
    )
    
    email = forms.EmailField(
        label=_("Adresse email"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    send_email = forms.BooleanField(
        label=_("Envoyer un email d'invitation"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean_username(self):
        """Vérifie que le nom d'utilisateur n'existe pas déjÃ ."""
        from django.contrib.auth.models import User
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_("Ce nom d'utilisateur existe déjÃ ."))
        return username


class PractitionerImportForm(forms.Form):
    """
    Formulaire pour importer des pratiquants depuis un fichier CSV ou Excel.
    """
    
    file = forms.FileField(
        label=_("Fichier Ã  importer"),
        help_text=_("Formats acceptés: CSV, Excel (.xlsx, .xls)"),
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.all(),  # Sera filtré dans __init__
        label=_("Club"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        # Extraire request des kwargs si présent
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les clubs selon l'utilisateur
        if self.request and hasattr(self.request, 'user'):
            user = self.request.user
            if hasattr(user, 'profile') and user.profile.role == 'club_manager':
                self.fields['club'].queryset = Club.objects.filter(owner=user)
            else:
                self.fields['club'].queryset = Club.objects.all()
        else:
            # Cas oÃ¹ request n'est pas fourni
            self.fields['club'].queryset = Club.objects.all()


class PractitionerSearchForm(forms.Form):
    """
    Formulaire pour rechercher des pratiquants.
    """
    
    search = forms.CharField(
        label=_("Rechercher"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Nom, prénom, licence...")
        })
    )
    
    club = forms.ModelChoiceField(
        queryset=Club.objects.all(),  # Sera filtré dans __init__
        label=_("Club"),
        required=False,
        empty_label=_("Tous les clubs"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    status = forms.ChoiceField(
        label=_("Statut"),
        choices=[('', _('Tous les statuts'))] + list(Practitioner.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.none(),  # PHASE 1 SECURITY: queryset vide par defaut
        label=_("Discipline"),
        required=False,
        empty_label=_("Toutes les disciplines"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    age_min = forms.IntegerField(
        label=_("Ã‚ge minimum"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    age_max = forms.IntegerField(
        label=_("Ã‚ge maximum"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, user=None, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.organization = organization

        # PHASE 1 SECURITY: Filtrer les disciplines par organisation
        if user:
            if user.is_superuser:
                self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
            else:
                accessible_disciplines = get_user_disciplines(user, organization)
                self.fields['discipline'].queryset = accessible_disciplines
        else:
            self.fields['discipline'].queryset = Discipline.objects.none()

        # Filtrer les clubs selon l'utilisateur
        if user and hasattr(user, 'profile') and user.profile.role == 'club_manager':
            self.fields['club'].queryset = Club.objects.filter(owner=user)
        else:
            self.fields['club'].queryset = Club.objects.all()


class PractitionerGradeForm(forms.Form):
    """
    Formulaire pour modifier uniquement le grade d'un pratiquant.
    PHASE 1 SECURITY: Filtrage par discipline de l'organisation.
    """

    grade = forms.ModelChoiceField(
        queryset=None,
        label=_("Grade"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    grade_date = forms.DateField(
        label=_("Date d'obtention"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def __init__(self, *args, user=None, organization=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.organization = organization

        import logging
        logger = logging.getLogger('discipline_isolation')

        try:
            from apps.grades.models import Grade
            grade_queryset = Grade.objects.filter(is_active=True)

            # PHASE 1 SECURITY: Filtrer par disciplines accessibles
            if user and user.is_authenticated and not user.is_superuser:
                accessible_disciplines = get_user_disciplines(user, organization)
                if accessible_disciplines.exists():
                    grade_queryset = grade_queryset.filter(discipline__in=accessible_disciplines)
                else:
                    grade_queryset = Grade.objects.none()
                    logger.warning(f"PractitionerGradeForm: User {user} has no accessible disciplines")

            self.fields['grade'].queryset = grade_queryset.order_by('discipline', 'level')

        except ImportError:
            self.fields['grade'].queryset = Grade.objects.none()
        except Exception as e:
            logger.critical(f"PractitionerGradeForm grade filtering FAILED: {e}")
            self.fields['grade'].queryset = Grade.objects.none()


