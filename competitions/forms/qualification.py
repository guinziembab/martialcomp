from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import PractitionerQualification, PractitionerDiscipline, Practitioner


class PractitionerGradeForm(forms.ModelForm):
    """Formulaire pour modifier le grade d'un pratiquant dans une discipline spécifique."""
    
    discipline = forms.ModelChoiceField(
        queryset=None,  # Sera défini dans __init__
        label=_("Discipline"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    current_grade = forms.CharField(
        label=_("Grade"),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    grade_date = forms.DateField(
        label=_("Date d'obtention"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    years_experience = forms.IntegerField(
        label=_("Années d'expérience"),
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    notes = forms.CharField(
        label=_("Notes"),
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    
    class Meta:
        model = PractitionerDiscipline
        fields = ['discipline', 'current_grade', 'grade_date', 'years_experience', 'notes']
    
    def __init__(self, *args, practitioner=None, **kwargs):
        super().__init__(*args, **kwargs)
        from ..models import Discipline
        
        # Définir le queryset des disciplines
        self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
        
        # Si un pratiquant est fourni et qu'une instance existe,
        # pré-remplir les disciplines déjà associées au pratiquant
        if practitioner and not self.instance.pk:
            # Récupérer les disciplines déjà associées
            existing_disciplines = practitioner.practitioner_disciplines.values_list(
                'discipline_id', flat=True
            )
            # Filtrer pour ne montrer que les disciplines non encore associées
            self.fields['discipline'].queryset = self.fields['discipline'].queryset.exclude(
                id__in=existing_disciplines
            )
        
        # Si c'est une modification, mettre le champ discipline en lecture seule
        if self.instance.pk:
            self.fields['discipline'].disabled = True


class QualificationForm(forms.ModelForm):
    """Formulaire pour les qualifications des pratiquants (juge, arbitre, etc.)."""
    
    class Meta:
        model = PractitionerQualification
        exclude = ['practitioner']
        widgets = {
            'qualification_type': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'certified_by': forms.Select(attrs={'class': 'form-control'}),
            'certification_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'certificate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, practitioner=None, **kwargs):
        super().__init__(*args, **kwargs)
        from ..models import Discipline
        
        # Définir le queryset des disciplines
        self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
        
        # Si un pratiquant est fourni, filtrer pour ne montrer que ses disciplines
        if practitioner:
            practitioner_disciplines = practitioner.disciplines.all()
            self.fields['discipline'].queryset = practitioner_disciplines
            
            # Si le pratiquant n'a pas de disciplines, ajouter un message d'aide
            if not practitioner_disciplines.exists():
                self.fields['discipline'].help_text = _(
                    "Le pratiquant n'a pas encore de disciplines associées. "
                    "Veuillez d'abord ajouter une discipline."
                )


class UpdateMainGradeForm(forms.ModelForm):
    """Formulaire pour mettre à jour le grade principal d'un pratiquant."""
    
    grade = forms.CharField(
        label=_("Grade principal"),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Practitioner
        fields = ['grade']
        
    def __init__(self, *args, practitioner=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si un pratiquant est fourni, pré-remplir avec son grade actuel
        if practitioner:
            self.fields['grade'].initial = practitioner.grade


class BulkGradeUpdateForm(forms.Form):
    """Formulaire pour mettre à jour en masse les grades de plusieurs pratiquants."""
    
    practitioners = forms.ModelMultipleChoiceField(
        queryset=Practitioner.objects.none(),
        label=_("Pratiquants"),
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    discipline = forms.ModelChoiceField(
        queryset=None,
        label=_("Discipline"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_grade = forms.CharField(
        label=_("Nouveau grade"),
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    grade_date = forms.DateField(
        label=_("Date d'obtention"),
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    update_main_grade = forms.BooleanField(
        label=_("Mettre également à jour le grade principal"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, club=None, **kwargs):
        super().__init__(*args, **kwargs)
        from ..models import Discipline
        
        # Définir le queryset des disciplines
        self.fields['discipline'].queryset = Discipline.objects.filter(is_active=True)
        
        # Si un club est fourni, filtrer les pratiquants par club
        if club:
            self.fields['practitioners'].queryset = Practitioner.objects.filter(
                club=club, is_active=True
            ).order_by('last_name', 'first_name')
        else:
            self.fields['practitioners'].queryset = Practitioner.objects.filter(
                is_active=True
            ).order_by('last_name', 'first_name')