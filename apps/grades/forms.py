from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import logging

from apps.competitions.models import Discipline, Practitioner
from .models import (
    Grade,
    PractitionerGrade,
    GradeCategory,
    GradeExam,
    GradeExamRegistration,
    GradeRequirement,
    ExamScoringModule,
    ExamScoringCriterion,
)
from .services import CertificateFileNamer

# PHASE 1 SECURITY: Import helpers de filtrage par discipline
from apps.competitions.utils.permission_helpers import (
    get_user_disciplines,
    get_user_organization,
    filter_queryset_by_user_disciplines
)

logger = logging.getLogger('discipline_isolation')


class GradeCategoryForm(forms.ModelForm):
    """Formulaire pour la création et modification des catégories de grades.
    PHASE 2 SECURITY: Filtrage par disciplines accessibles.
    """

    class Meta:
        model = GradeCategory
        fields = ['name', 'description', 'discipline', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom de la catégorie')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description de la catégorie')
            }),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # PHASE 2 SECURITY: Filtrer les disciplines
        if user:
            if user.is_superuser:
                self.fields['discipline'].queryset = Discipline.objects.filter(
                    is_active=True
                )
            else:
                self.fields['discipline'].queryset = get_user_disciplines(user)
        else:
            self.fields['discipline'].queryset = Discipline.objects.none()
            logger.warning("GradeCategoryForm: No user - disciplines empty")


class GradeForm(forms.ModelForm):
    """Formulaire pour la création et modification des grades.
    PHASE 2 SECURITY: Filtrage par disciplines accessibles.
    """

    class Meta:
        model = Grade
        fields = [
            'name', 'discipline', 'category', 'color', 'color_code',
            'level', 'min_age', 'min_time_in_previous_grade',
            'is_active', 'is_dan_grade', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom du grade')
            }),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Rouge, Bleu, Noir...')
            }),
            'color_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: #FF0000')
            }),
            'level': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_time_in_previous_grade': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_dan_grade': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # PHASE 2 SECURITY: Filtrer les disciplines
        if user:
            if user.is_superuser:
                self.fields['discipline'].queryset = Discipline.objects.filter(
                    is_active=True
                )
            else:
                self.fields['discipline'].queryset = get_user_disciplines(user)
        else:
            self.fields['discipline'].queryset = Discipline.objects.none()
            logger.warning("GradeForm: No user - disciplines empty")

        # Si une discipline est sélectionnée, filtrer les catégories
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                self.fields['category'].queryset = GradeCategory.objects.filter(
                    discipline_id=discipline_id
                )
            except (ValueError, TypeError):
                self.fields['category'].queryset = GradeCategory.objects.none()
        elif self.instance.pk and self.instance.discipline:
            self.fields['category'].queryset = GradeCategory.objects.filter(
                discipline=self.instance.discipline
            )
        else:
            self.fields['category'].queryset = GradeCategory.objects.none()


class PractitionerGradeForm(forms.ModelForm):
    """Formulaire pour attribuer un grade Ã  un pratiquant."""
    
    certificate_file = forms.FileField(
        label=_("Certificat"),
        required=False,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])
        ],
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = PractitionerGrade
        fields = [
            'grade', 'discipline', 'date_obtained', 'date_expiry',
            'awarded_by', 'location', 'certificate_number', 'certificate_file',
            'notes', 'is_current'
        ]  # Retiré 'practitioner' de la liste des champs
        widgets = {
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'date_obtained': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_expiry': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'awarded_by': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }  # Retiré 'practitioner' des widgets
    
    def __init__(self, *args, **kwargs):
        # Extraire les paramètres personnalisés AVANT d'appeler super().__init__
        self.practitioner = kwargs.pop('practitioner', None)
        discipline = kwargs.pop('discipline', None)
        
        # Maintenant on peut appeler super().__init__ avec les kwargs nettoyés
        super().__init__(*args, **kwargs)
        
        # Si une discipline est fournie, la définir comme valeur initiale
        if discipline:
            self.fields['discipline'].initial = discipline
            self.fields['discipline'].widget.attrs['readonly'] = True
            
        # Filtrer les grades par discipline si une discipline est fournie
        if discipline:
            self.fields['grade'].queryset = Grade.objects.filter(
                discipline=discipline,
                is_active=True
            ).order_by('level')
        elif self.instance.pk and self.instance.grade:
            # Si on édite un grade existant, filtrer par la discipline du grade
            self.fields['grade'].queryset = Grade.objects.filter(
                discipline=self.instance.grade.discipline,
                is_active=True
            ).order_by('level')
        else:
            # Par défaut, tous les grades actifs (le JavaScript filtrera selon la discipline sélectionnée)
            self.fields['grade'].queryset = Grade.objects.filter(is_active=True).order_by('discipline__name', 'level')
    
    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get('grade')
        discipline = cleaned_data.get('discipline')
        date_obtained = cleaned_data.get('date_obtained')
        
        # Utiliser self.practitioner au lieu de cleaned_data.get('practitioner')
        practitioner = self.practitioner
        
        # Assurer que la discipline est cohérente avec le grade sélectionné
        if grade and discipline and grade.discipline != discipline:
            self.add_error('grade', _("Le grade sélectionné n'appartient pas Ã  la discipline choisie."))
        
        # Vérifier que le pratiquant a l'Ã¢ge minimum requis pour ce grade
        if practitioner and grade and date_obtained:
            practitioner_age = (date_obtained - practitioner.birth_date).days // 365
            if practitioner_age < grade.min_age:
                self.add_error('grade', _(
                    f"Le pratiquant n'a pas l'Ã¢ge minimum requis pour ce grade. "
                    f"Ã‚ge minimum: {grade.min_age} ans, Ã¢ge du pratiquant: {practitioner_age} ans."
                ))
        
        # Vérifier que le pratiquant a eu le grade précédent pendant assez longtemps
        if practitioner and grade and hasattr(grade, 'previous_grade') and grade.previous_grade and date_obtained:
            previous_grade = PractitionerGrade.objects.filter(
                practitioner=practitioner,
                grade=grade.previous_grade,
                discipline=discipline
            ).order_by('-date_obtained').first()
            
            if previous_grade:
                months_in_previous_grade = (
                    (date_obtained.year - previous_grade.date_obtained.year) * 12 +
                    date_obtained.month - previous_grade.date_obtained.month
                )
                
                if months_in_previous_grade < grade.min_time_in_previous_grade:
                    self.add_error('grade', _(
                        f"Le pratiquant n'a pas passé suffisamment de temps avec le grade précédent. "
                        f"Minimum requis: {grade.min_time_in_previous_grade} mois, "
                        f"temps passé: {months_in_previous_grade} mois."
                    ))
            elif grade.min_time_in_previous_grade > 0:
                self.add_error('grade', _(
                    f"Le pratiquant doit avoir le grade précédent "
                    f"({grade.previous_grade.name}) avant d'obtenir ce grade."
                ))
        
        # Génération automatique du code de certificat si non renseigné
        if practitioner and discipline and date_obtained:
            code = CertificateFileNamer.generate_code(practitioner=practitioner, discipline=discipline, date=date_obtained)
            cleaned_data['certificate_number'] = code
            self.data = self.data.copy()
            self.data['certificate_number'] = code
        return cleaned_data
        
    def save(self, commit=True):
        # Assigner le practitioner avant de sauvegarder
        instance = super().save(commit=False)
        
        if self.practitioner:
            instance.practitioner = self.practitioner
            
        # Génération du nom de fichier pour le certificat si upload
        cert_file = self.cleaned_data.get('certificate_file')
        if cert_file and instance.certificate_number:
            ext = cert_file.name.split('.')[-1]
            filename = CertificateFileNamer.generate_filename(practitioner=instance.practitioner, discipline=instance.discipline, date=instance.date_obtained, extension=ext)
            cert_file.name = filename
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance


class BulkGradeAssignmentForm(forms.Form):
    """
    Formulaire pour attribuer des grades en masse aux pratiquants.
    PHASE 1 SECURITY: Filtrage par discipline de l'organisation.
    """

    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.none(),  # PHASE 1 SECURITY: queryset vide par defaut
        label=_("Discipline"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    grade = forms.ModelChoiceField(
        queryset=Grade.objects.none(),
        label=_("Grade a attribuer"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    practitioners = forms.ModelMultipleChoiceField(
        queryset=Practitioner.objects.none(),  # PHASE 1 SECURITY: queryset vide par defaut
        label=_("Pratiquants"),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10})
    )

    date_obtained = forms.DateField(
        label=_("Date d'obtention"),
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    awarded_by = forms.CharField(
        label=_("Decerne par"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    location = forms.CharField(
        label=_("Lieu d'obtention"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    set_as_current = forms.BooleanField(
        label=_("Definir comme grade actuel"),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, user=None, organization=None, club=None, **kwargs):
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
            logger.warning("BulkGradeAssignmentForm: No user provided - disciplines empty")

        # Si une discipline est selectionnee, filtrer les grades
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                # PHASE 1 SECURITY: Verifier que la discipline est accessible
                if user and not user.is_superuser:
                    accessible_ids = list(get_user_disciplines(user, organization).values_list('id', flat=True))
                    if discipline_id not in accessible_ids:
                        logger.warning(f"BulkGradeAssignmentForm: User {user} tried to access discipline {discipline_id}")
                        self.fields['grade'].queryset = Grade.objects.none()
                    else:
                        self.fields['grade'].queryset = Grade.objects.filter(discipline_id=discipline_id).order_by('level')
                else:
                    self.fields['grade'].queryset = Grade.objects.filter(discipline_id=discipline_id).order_by('level')
            except (ValueError, TypeError):
                pass
        else:
            self.fields['grade'].queryset = Grade.objects.none()

        # Filtrer les pratiquants par club/organisation
        if club:
            org = getattr(club, 'organization', None) or getattr(club, 'as_organization', None)
            if org:
                self.fields['practitioners'].queryset = Practitioner.objects.filter(organization=org)
        elif organization:
            self.fields['practitioners'].queryset = Practitioner.objects.filter(organization=organization)


class GradeExamForm(forms.ModelForm):
    """Formulaire pour la création et modification d'examens de passage de grade.
    PHASE 2 SECURITY: Filtrage par disciplines accessibles.
    """

    class Meta:
        model = GradeExam
        fields = [
            'title', 'description', 'date', 'location', 'discipline',
            'max_participants', 'registration_deadline',
            'fee', 'status', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={
                'class': 'form-control'
            }),
            'registration_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    available_grades = forms.ModelMultipleChoiceField(
        queryset=Grade.objects.none(),  # PHASE 2 SECURITY: vide par defaut
        label=_("Grades disponibles"),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10}),
        required=False
    )

    examiner_users = forms.ModelMultipleChoiceField(
        queryset=Practitioner.objects.none(),
        label=_("Examinateurs"),
        widget=forms.CheckboxSelectMultiple(),
        required=False
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # PHASE 2 SECURITY: Filtrer les disciplines
        if user:
            if user.is_superuser:
                self.fields['discipline'].queryset = Discipline.objects.filter(
                    is_active=True
                )
            else:
                self.fields['discipline'].queryset = get_user_disciplines(user)
        else:
            self.fields['discipline'].queryset = Discipline.objects.none()
            logger.warning("GradeExamForm: No user - disciplines empty")

        # Populate examiner_users with organization members (Practitioners)
        if user:
            org = get_user_organization(user)
            if org:
                self.fields['examiner_users'].queryset = Practitioner.objects.filter(
                    organization=org
                ).select_related('user').order_by('last_name', 'first_name')
            elif user.is_superuser:
                self.fields['examiner_users'].queryset = Practitioner.objects.all(
                ).select_related('user').order_by('last_name', 'first_name')

        # Pre-select examiners from the stored CharField
        if self.instance.pk and self.instance.examiners:
            stored_names = [n.strip() for n in self.instance.examiners.split(',') if n.strip()]
            if stored_names:
                from django.db.models import Q
                q = Q()
                for name in stored_names:
                    parts = name.split()
                    if len(parts) >= 2:
                        q |= Q(first_name__iexact=parts[0], last_name__iexact=' '.join(parts[1:]))
                    else:
                        q |= Q(last_name__iexact=name) | Q(first_name__iexact=name)
                matching = self.fields['examiner_users'].queryset.filter(q)
                self.fields['examiner_users'].initial = matching

        # Si l'instance existe, charger les grades disponibles
        if self.instance.pk:
            self.fields['available_grades'].initial = \
                self.instance.available_grades.all()

        # Si une discipline est sélectionnée, filtrer les grades
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                self.fields['available_grades'].queryset = Grade.objects.filter(
                    discipline_id=discipline_id
                ).order_by('level')
            except (ValueError, TypeError):
                self.fields['available_grades'].queryset = Grade.objects.none()
        elif self.instance.pk and self.instance.discipline:
            self.fields['available_grades'].queryset = Grade.objects.filter(
                discipline=self.instance.discipline
            ).order_by('level')
        else:
            self.fields['available_grades'].queryset = Grade.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        registration_deadline = cleaned_data.get('registration_deadline')
        
        if date and registration_deadline and date < registration_deadline:
            self.add_error(
                'registration_deadline', 
                _("La date limite d'inscription doit Ãªtre antérieure Ã  la date de l'examen.")
            )
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Store selected examiner names as comma-separated text in CharField
        examiner_users = self.cleaned_data.get('examiner_users')
        if examiner_users:
            names = []
            for p in examiner_users:
                full_name = f"{p.first_name} {p.last_name}".strip()
                names.append(full_name if full_name else str(p))
            instance.examiners = ', '.join(names)
        else:
            instance.examiners = ''
        if commit:
            instance.save()
            self.save_m2m()
        return instance



class GradeExamRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription Ã  un examen de passage de grade."""
    
    class Meta:
        model = GradeExamRegistration
        fields = ['practitioner', 'target_grade', 'payment_confirmed']
        widgets = {
            'practitioner': forms.Select(attrs={'class': 'form-control'}),
            'target_grade': forms.Select(attrs={'class': 'form-control'}),
            'payment_confirmed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        exam = kwargs.pop('exam', None)
        club = kwargs.pop('club', None)
        super().__init__(*args, **kwargs)
        
        if exam:
            self.exam = exam
            
            # Filtrer les grades disponibles pour cet examen
            self.fields['target_grade'].queryset = exam.available_grades.all().order_by('level')
            
            # Si un club est spécifié, filtrer les pratiquants par club
            if club:
                # Récupérer l'organisation associée au club
                organization = club.organization or club.as_organization
                if organization:
                    self.fields['practitioner'].queryset = Practitioner.objects.filter(organization=organization)
        else:
            self.fields['target_grade'].queryset = Grade.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        practitioner = cleaned_data.get('practitioner')
        target_grade = cleaned_data.get('target_grade')
        
        if not hasattr(self, 'exam'):
            raise ValidationError(_("L'examen n'a pas été spécifié."))
        
        # Vérifier que le pratiquant n'est pas déjÃ  inscrit Ã  cet examen
        if practitioner and GradeExamRegistration.objects.filter(
            exam=self.exam,
            practitioner=practitioner
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            self.add_error('practitioner', _("Ce pratiquant est déjÃ  inscrit Ã  cet examen."))
        
        # Vérifier que le pratiquant a l'Ã¢ge minimum pour ce grade
        if practitioner and target_grade:
            practitioner_age = (timezone.now().date() - practitioner.birth_date).days // 365
            if practitioner_age < target_grade.min_age:
                self.add_error('target_grade', _(
                    f"Le pratiquant n'a pas l'Ã¢ge minimum requis pour ce grade. "
                    f"Ã‚ge minimum: {target_grade.min_age} ans, Ã¢ge du pratiquant: {practitioner_age} ans."
                ))
        
        # Vérifier que le pratiquant a le grade précédent
        if practitioner and target_grade and target_grade.previous_grade:
            has_previous_grade = PractitionerGrade.objects.filter(
                practitioner=practitioner,
                grade=target_grade.previous_grade,
                is_current=True
            ).exists()
            
            if not has_previous_grade:
                self.add_error('target_grade', _(
                    f"Le pratiquant doit avoir le grade {target_grade.previous_grade.name} "
                    f"avant de pouvoir passer le grade {target_grade.name}."
                ))
        
        return cleaned_data


class GradeRequirementForm(forms.ModelForm):
    """Formulaire pour la creation et modification des exigences de grade.
    PHASE 2 SECURITY: Filtrage des grades par disciplines accessibles.
    """

    class Meta:
        model = GradeRequirement
        fields = [
            'grade', 'name', 'description', 'is_mandatory',
            'min_age', 'min_time_in_previous_grade', 'required_points', 'order'
        ]
        widgets = {
            'grade': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_time_in_previous_grade': forms.NumberInput(attrs={'class': 'form-control'}),
            'required_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # PHASE 2 SECURITY: Filtrer les grades par disciplines accessibles
        if user:
            if user.is_superuser:
                self.fields['grade'].queryset = Grade.objects.filter(
                    is_active=True
                ).select_related('discipline')
            else:
                accessible_disciplines = get_user_disciplines(user)
                self.fields['grade'].queryset = Grade.objects.filter(
                    discipline__in=accessible_disciplines,
                    is_active=True
                ).select_related('discipline')
        else:
            # PHASE 2 SECURITY: Sans user, aucun grade disponible
            self.fields['grade'].queryset = Grade.objects.none()
            logger.warning("GradeRequirementForm: No user provided - grades empty")


class ExamScoringModuleForm(forms.ModelForm):
    """Formulaire pour un module de notation d'examen."""

    class Meta:
        model = ExamScoringModule
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Technique, Kata, Combat...')
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class ExamScoringCriterionForm(forms.ModelForm):
    """Formulaire pour un critère de notation."""

    class Meta:
        model = ExamScoringCriterion
        fields = ['name', 'coefficient', 'max_score', 'order', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ex: Mae Geri, Kata Heian Shodan...')
            }),
            'coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '1',
            }),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Description optionnelle du critère')
            }),
        }

