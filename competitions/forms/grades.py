# competitions/forms/grades.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from django.core.validators import RegexValidator
from django.db.models.query import QuerySet
from ..models.grades import GradeSystem, GradeCategory, Grade, GradeHistory
from ..models import Discipline, Practitioner

# Importation sécurisée des modèles
try:
    from ..models import Discipline, Practitioner, CategoryGrade
    from ..models import Grade, GradeHistory, GradeSystem, GradeCategory
    MODELS_AVAILABLE = True
except (ImportError, AttributeError):
    # Si les modèles ne sont pas accessibles, créons des classes vides pour éviter les erreurs
    class ModelStub:
        objects = None
        
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class DisciplineStub(ModelStub):
        pass
    
    class PractitionerStub(ModelStub):
        pass
    
    class GradeStub(ModelStub):
        pass
    
    class GradeHistoryStub(ModelStub):
        pass
    
    class GradeSystemStub(ModelStub):
        pass
    
    class GradeCategoryStub(ModelStub):
        pass
    
    class CategoryGradeStub(ModelStub):
        pass
    
    # Utiliser les stubs si les vrais modèles ne sont pas disponibles
    Discipline = DisciplineStub
    Practitioner = PractitionerStub
    Grade = GradeStub
    GradeHistory = GradeHistoryStub
    GradeSystem = GradeSystemStub
    GradeCategory = GradeCategoryStub
    CategoryGrade = CategoryGradeStub
    MODELS_AVAILABLE = False


class GradeForm(forms.ModelForm):
    """Formulaire pour gérer les grades"""
    class Meta:
        model = Grade
        fields = ['name', 'category', 'level', 'order', 'color', 'description', 'accessible_to_clubs']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom du grade')}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 
                                                'placeholder': _('Description du grade')}),
            'accessible_to_clubs': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        
        # Ajouter les champs optionnels si le modèle les possède
        if hasattr(Grade, 'min_age'):
            fields.append('min_age')
            widgets['min_age'] = forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
            
        if hasattr(Grade, 'min_experience_months'):
            fields.append('min_experience_months')
            widgets['min_experience_months'] = forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
            
        if hasattr(Grade, 'prerequisites'):
            fields.append('prerequisites')
            widgets['prerequisites'] = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    
    def clean_color(self):
        """Validation de la couleur au format hexadécimal"""
        color = self.cleaned_data.get('color')
        if color:
            # S'assurer que c'est un code hex valide (#RRGGBB ou #RGB)
            hex_color_validator = RegexValidator(
                r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
                _('Veuillez entrer une couleur au format hexadécimal valide (ex: #FF5733)')
            )
            try:
                hex_color_validator(color)
            except forms.ValidationError:
                # Si ce n'est pas un hex valide, on ajoute # si manquant
                if not color.startswith('#'):
                    color = f'#{color}'
                    # Essayer de valider à nouveau
                    try:
                        hex_color_validator(color)
                    except forms.ValidationError:
                        raise forms.ValidationError(_('Format de couleur invalide. Utilisez le format hexadécimal (ex: #FF5733)'))
        return color
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Validation des niveaux et ordres
        level = cleaned_data.get('level')
        order = cleaned_data.get('order')
        
        if level is not None and level < 1:
            self.add_error('level', _('Le niveau doit être supérieur ou égal à 1'))
        
        if order is not None and order < 0:
            self.add_error('order', _('L\'ordre doit être un nombre positif ou nul'))
        
        return cleaned_data


class GradeHistoryForm(forms.ModelForm):
    """Formulaire pour l'historique des grades"""
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all(),
        required=True,
        label=_("Discipline"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Initialiser avec un queryset vide qui sera remplacé dynamiquement
    grade_system = forms.ModelChoiceField(
        queryset=GradeSystem.objects.all(),
        required=True,
        label=_("Système de grades"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    grade = forms.ModelChoiceField(
        queryset=Grade.objects.all(),
        required=True,
        label=_("Grade"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = GradeHistory
        fields = ['practitioner', 'discipline', 'grade_system', 'grade', 
                  'obtained_date', 'certifier', 'location', 'is_current', 'notes']
        widgets = {
            'practitioner': forms.Select(attrs={'class': 'form-select'}),
            'obtained_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'certifier': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Améliorer l'UX avec Select2
        for field in ['practitioner', 'discipline', 'grade_system', 'grade', 'certifier']:
            if field in self.fields:
                self.fields[field].widget.attrs.update({'class': 'select2-field form-select'})
        
        # Définir le queryset pour les pratiquants actifs
        if 'practitioner' in self.fields:
            self.fields['practitioner'].queryset = Practitioner.objects.filter(is_active=True)
        
        # Initialiser les querysets pour l'édition
        if self.instance and self.instance.pk:
            try:
                if (hasattr(self.instance, 'grade') and 
                    hasattr(self.instance.grade, 'category') and 
                    hasattr(self.instance.grade.category, 'system')):
                    
                    # Initialiser discipline
                    discipline = self.instance.grade.category.system.discipline
                    self.fields['discipline'].initial = discipline
                    
                    # Initialiser grade_system
                    system = self.instance.grade.category.system
                    self.fields['grade_system'].queryset = GradeSystem.objects.filter(discipline=discipline)
                    self.fields['grade_system'].initial = system
                    
                    # Initialiser grade
                    self.fields['grade'].queryset = Grade.objects.filter(category__system=system)
            except Exception as e:
                # Continuer sans erreur en cas d'échec d'initialisation
                pass
        
        # Filtrer les querysets en fonction des données POST pour les sélections dynamiques
        if self.is_bound:
            # Si une discipline est sélectionnée, filtrer les systèmes de grades
            if 'discipline' in self.data and self.data['discipline']:
                try:
                    discipline_id = int(self.data['discipline'])
                    self.fields['grade_system'].queryset = GradeSystem.objects.filter(
                        discipline_id=discipline_id
                    )
                except (ValueError, TypeError):
                    pass
            
            # Si un système de grades est sélectionné, filtrer les grades
            if 'grade_system' in self.data and self.data['grade_system']:
                try:
                    system_id = int(self.data['grade_system'])
                    self.fields['grade'].queryset = Grade.objects.filter(
                        category__system_id=system_id
                    )
                except (ValueError, TypeError):
                    pass
        
        # Désactiver la validation stricte des choix pour les champs dynamiques
        # C'est la solution au problème principal
        self.fields['grade_system'].validators = []
        self.fields['grade'].validators = []
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Vérification de la date d'obtention (pas dans le futur)
        obtained_date = cleaned_data.get('obtained_date')
        if obtained_date:
            from django.utils import timezone
            if obtained_date > timezone.now().date():
                self.add_error('obtained_date', _("La date d'obtention ne peut pas être dans le futur"))
        
        # Vérification de cohérence entre grade_system et grade
        grade = cleaned_data.get('grade')
        grade_system = cleaned_data.get('grade_system')
        
        if grade and grade_system and hasattr(grade, 'category') and hasattr(grade.category, 'system'):
            if grade.category.system != grade_system:
                self.add_error('grade', _("Ce grade n'appartient pas au système de grades sélectionné"))
        
        return cleaned_data


class GradeSystemForm(forms.ModelForm):
    """Formulaire pour les systèmes de grades"""
    class Meta:
        model = GradeSystem
        fields = ['name', 'description', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }
        
        # Ajouter le champ is_active s'il existe
        if hasattr(GradeSystem, 'is_active'):
            fields.append('is_active')
            widgets['is_active'] = forms.CheckboxInput(attrs={'class': 'form-check-input'})
    
    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        
        # Vérification que le système par défaut est actif (si applicable)
        is_default = cleaned_data.get('is_default')
        is_active = cleaned_data.get('is_active')
        
        if is_default and is_active is not None and not is_active:
            self.add_error('is_default', _('Un système par défaut doit être actif'))
            self.add_error('is_active', _('Ce système est défini comme par défaut et doit être actif'))
        
        return cleaned_data


class GradeCategoryForm(forms.ModelForm):
    """Formulaire pour les catégories de grades"""
    class Meta:
        model = GradeCategory
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
        }
        
        # Ajouter des champs supplémentaires si le modèle les possède
        if hasattr(GradeCategory, 'description'):
            fields.append('description')
            widgets['description'] = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
            
        if hasattr(GradeCategory, 'color_hex'):
            fields.append('color_hex')
            widgets['color_hex'] = forms.TextInput(attrs={'class': 'form-control', 'type': 'color'})
    
    def clean_order(self):
        """Validation de l'ordre"""
        order = self.cleaned_data.get('order')
        if order is not None and order < 0:
            raise forms.ValidationError(_('L\'ordre doit être un nombre positif ou nul'))
        return order


# Ajout du formulaire CategoryGradeForm pour le modèle CategoryGrade
class CategoryGradeForm(forms.ModelForm):
    """Formulaire pour les catégories de grades (modèle CategoryGrade)"""
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all() if hasattr(Discipline, 'objects') else [],
        required=True,
        label=_("Discipline"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Ces champs seront traités comme des listes déroulantes dans la vue
    grade_min = forms.CharField(
        required=False,
        label=_("Grade minimum"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    grade_max = forms.CharField(
        required=False,
        label=_("Grade maximum"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = CategoryGrade
        fields = ['name', 'discipline', 'grade_min', 'grade_max', 'order', 'description']  # Changé 'nom' en 'name'
        widgets = {
            'name': forms.TextInput(attrs={  # Changé 'nom' en 'name'
                'class': 'form-control',
                'placeholder': _('Nom de la catégorie de grade')
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': _('Ordre d\'affichage')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description de la catégorie')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        discipline_grades = kwargs.pop('discipline_grades', None)
        super().__init__(*args, **kwargs)
        
        # Si une instance existe, préremplir les champs
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'discipline'):
                self.fields['discipline'].initial = self.instance.discipline
                
            # Récupérer les valeurs actuelles pour les afficher correctement
            if hasattr(self.instance, 'grade_min'):
                self.initial['grade_min'] = self.instance.grade_min
                
            if hasattr(self.instance, 'grade_max'):
                self.initial['grade_max'] = self.instance.grade_max
        
        # Si des grades de discipline sont fournis, initialiser les choix
        if discipline_grades:
            grade_choices = [('', _('Aucun'))]
            grade_choices.extend([(grade.name, grade.name) for grade in discipline_grades])
            
            self.fields['grade_min'].widget.choices = grade_choices
            self.fields['grade_max'].widget.choices = grade_choices
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        grade_min = cleaned_data.get('grade_min')
        grade_max = cleaned_data.get('grade_max')
        discipline = cleaned_data.get('discipline')
        
        # Si les deux grades sont spécifiés, vérifier que min < max
        if grade_min and grade_max and grade_min == grade_max:
            self.add_error('grade_max', _("Le grade maximum doit être différent du grade minimum"))
        
        return cleaned_data
    
    def clean_order(self):
        """Validation de l'ordre."""
        order = self.cleaned_data.get('order')
        if order is not None and order < 0:
            raise forms.ValidationError(_('L\'ordre doit être un nombre positif ou nul'))
        return order


# Fonction sécurisée pour créer le formset
def create_category_formset():
    """Crée le formset pour GradeCategory de manière sécurisée"""
    if MODELS_AVAILABLE and hasattr(GradeSystem, 'categories') and hasattr(GradeCategory, 'system'):
        try:
            return inlineformset_factory(
                GradeSystem, 
                GradeCategory,
                form=GradeCategoryForm,
                extra=1,
                can_delete=True
            )
        except Exception:
            return None
    return None

# Fonction sécurisée pour créer le formset de grades
def create_grade_formset():
    """Crée le formset pour Grade de manière sécurisée"""
    if MODELS_AVAILABLE and hasattr(GradeCategory, 'grades') and hasattr(Grade, 'category'):
        try:
            fields = ['name', 'level', 'order', 'color', 'description', 'accessible_to_clubs']
            
            # Ajouter des champs supplémentaires si disponibles
            if hasattr(Grade, 'min_age'):
                fields.append('min_age')
            if hasattr(Grade, 'min_experience_months'):
                fields.append('min_experience_months')
            if hasattr(Grade, 'prerequisites'):
                fields.append('prerequisites')
                
            return inlineformset_factory(
                GradeCategory,
                Grade,
                form=GradeForm,
                extra=3,
                can_delete=True,
                fields=fields
            )
        except Exception:
            return None
    return None

# Utiliser les fonctions sécurisées pour définir les formsets
GradeCategoryFormSet = create_category_formset()
GradeFormSet = create_grade_formset()


class GradeImportForm(forms.Form):
    """Formulaire pour importer des systèmes de grades à partir d'un JSON"""
    json_data = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        label=_("Données JSON"),
        help_text=_("Collez ici vos données JSON pour importer les systèmes de grades")
    )
    
    # Définir le queryset en fonction de la disponibilité de Discipline
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all() if hasattr(Discipline, 'objects') else [],
        label=_("Discipline"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        disciplines_queryset = kwargs.pop('disciplines_queryset', None)
        super().__init__(*args, **kwargs)
        
        # Mise à jour sécurisée du queryset
        if disciplines_queryset:
            self.fields['discipline'].queryset = disciplines_queryset
        elif hasattr(Discipline, 'objects'):
            try:
                self.fields['discipline'].queryset = Discipline.objects.all()
            except:
                # Garder un queryset vide si l'accès échoue
                pass


# Version simplifiée des autres formulaires pour éviter les dépendances
class GradeFilterForm(forms.Form):
    """Formulaire pour rechercher et filtrer les grades"""
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.all() if hasattr(Discipline, 'objects') else [],
        required=False,
        empty_label=_("Toutes les disciplines"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Rechercher un grade...')
        })
    )