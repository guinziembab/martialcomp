from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from competitions.models import Discipline, Practitioner
from .models import (
    Grade, 
    PractitionerGrade, 
    GradeCategory, 
    GradeExam, 
    GradeExamRegistration,
    GradeRequirement
)


class GradeCategoryForm(forms.ModelForm):
    """Formulaire pour la création et modification des catégories de grades."""
    
    class Meta:
        model = GradeCategory
        fields = ['name', 'description', 'discipline', 'order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de la catégorie')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': _('Description de la catégorie')}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class GradeForm(forms.ModelForm):
    """Formulaire pour la création et modification des grades."""
    
    class Meta:
        model = Grade
        fields = [
            'name', 'discipline', 'category', 'color', 'color_code', 
            'level', 'min_age', 'min_time_in_previous_grade',
            'is_active', 'is_dan_grade', 'order'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du grade')}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: Rouge, Bleu, Noir...')}),
            'color_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Ex: #FF0000')}),
            'level': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_time_in_previous_grade': forms.NumberInput(attrs={'class': 'form-control'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_dan_grade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si une discipline est sélectionnée, filtrer les catégories par discipline
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                self.fields['category'].queryset = GradeCategory.objects.filter(discipline_id=discipline_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.discipline:
            self.fields['category'].queryset = GradeCategory.objects.filter(discipline=self.instance.discipline)


class PractitionerGradeForm(forms.ModelForm):
    """Formulaire pour attribuer un grade à un pratiquant."""
    
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
            
        # Ne pas filtrer les grades ici - laisser le JavaScript s'en charger
        # Mais s'assurer que tous les grades actifs sont disponibles
        self.fields['grade'].queryset = Grade.objects.filter(is_active=True).order_by('discipline__name', 'level')
        
        # Si on édite un grade existant, filtrer par la discipline du grade
        if self.instance.pk and self.instance.grade:
            self.fields['grade'].queryset = Grade.objects.filter(
                discipline=self.instance.grade.discipline,
                is_active=True
            ).order_by('level')
    
    def clean(self):
        cleaned_data = super().clean()
        grade = cleaned_data.get('grade')
        discipline = cleaned_data.get('discipline')
        date_obtained = cleaned_data.get('date_obtained')
        
        # Utiliser self.practitioner au lieu de cleaned_data.get('practitioner')
        practitioner = self.practitioner
        
        # Assurer que la discipline est cohérente avec le grade sélectionné
        if grade and discipline and grade.discipline != discipline:
            self.add_error('grade', _("Le grade sélectionné n'appartient pas à la discipline choisie."))
        
        # Vérifier que le pratiquant a l'âge minimum requis pour ce grade
        if practitioner and grade and date_obtained:
            practitioner_age = (date_obtained - practitioner.birth_date).days // 365
            if practitioner_age < grade.min_age:
                self.add_error('grade', _(
                    f"Le pratiquant n'a pas l'âge minimum requis pour ce grade. "
                    f"Âge minimum: {grade.min_age} ans, âge du pratiquant: {practitioner_age} ans."
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
        
        return cleaned_data
        
    def save(self, commit=True):
        # Assigner le practitioner avant de sauvegarder
        instance = super().save(commit=False)
        
        if self.practitioner:
            instance.practitioner = self.practitioner
            
        if commit:
            instance.save()
            self.save_m2m()
            
        return instance


class BulkGradeAssignmentForm(forms.Form):
    """Formulaire pour attribuer des grades en masse aux pratiquants."""
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(),
        label=_("Discipline"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.none(),
        label=_("Grade à attribuer"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    practitioners = forms.ModelMultipleChoiceField(
        queryset=Practitioner.objects.all(),
        label=_("Pratiquants"),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10})
    )
    
    date_obtained = forms.DateField(
        label=_("Date d'obtention"),
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    awarded_by = forms.CharField(
        label=_("Décerné par"),
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
        label=_("Définir comme grade actuel"),
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si une discipline est sélectionnée, filtrer les grades
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                self.fields['grade'].queryset = Grade.objects.filter(discipline_id=discipline_id).order_by('level')
            except (ValueError, TypeError):
                pass
        else:
            self.fields['grade'].queryset = Grade.objects.none()
            
        # Si un club est fourni, filtrer les pratiquants par club
        club = kwargs.pop('club', None) if 'club' not in kwargs else None
        if club:
            # Récupérer l'organisation associée au club
            organization = club.organization or club.as_organization
            if organization:
                self.fields['practitioners'].queryset = Practitioner.objects.filter(organization=organization)


class GradeExamForm(forms.ModelForm):
    """Formulaire pour la création et modification d'examens de passage de grade."""
    
    class Meta:
        model = GradeExam
        fields = [
            'title', 'description', 'date', 'location', 'discipline',
            'max_participants', 'registration_deadline', 'examiners',
            'fee', 'status', 'notes'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'examiners': forms.TextInput(attrs={'class': 'form-control'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    available_grades = forms.ModelMultipleChoiceField(
        queryset=Grade.objects.all(),
        label=_("Grades disponibles"),
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': 10}),
        required=False
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si l'instance existe, charger les grades disponibles
        if self.instance.pk:
            self.fields['available_grades'].initial = self.instance.available_grades.all()
        
        # Si une discipline est sélectionnée, filtrer les grades
        if 'discipline' in self.data:
            try:
                discipline_id = int(self.data.get('discipline'))
                self.fields['available_grades'].queryset = Grade.objects.filter(
                    discipline_id=discipline_id
                ).order_by('level')
            except (ValueError, TypeError):
                pass
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
                _("La date limite d'inscription doit être antérieure à la date de l'examen.")
            )
        
        return cleaned_data


class GradeExamRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription à un examen de passage de grade."""
    
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
        
        # Vérifier que le pratiquant n'est pas déjà inscrit à cet examen
        if practitioner and GradeExamRegistration.objects.filter(
            exam=self.exam,
            practitioner=practitioner
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            self.add_error('practitioner', _("Ce pratiquant est déjà inscrit à cet examen."))
        
        # Vérifier que le pratiquant a l'âge minimum pour ce grade
        if practitioner and target_grade:
            practitioner_age = (timezone.now().date() - practitioner.birth_date).days // 365
            if practitioner_age < target_grade.min_age:
                self.add_error('target_grade', _(
                    f"Le pratiquant n'a pas l'âge minimum requis pour ce grade. "
                    f"Âge minimum: {target_grade.min_age} ans, âge du pratiquant: {practitioner_age} ans."
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
    """Formulaire pour la création et modification des exigences de grade."""
    
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