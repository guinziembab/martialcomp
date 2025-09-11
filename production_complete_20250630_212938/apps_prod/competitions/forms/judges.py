from django import forms
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from competitions.models import JudgeAssignment, Judge, CompetitionCategory

# Imports optimisés des modèles
from competitions.models import (
    Discipline, 
    Practitioner,
    Judge,
    JudgeQualification, 
    JudgeCompetitionAssignment, 
    CompetitionRegistration,
    JudgeTechnicalApplication
)

# Import explicite des modèles de grade
from grades.models import Grade, GradeCategory 

class JudgeProfileForm(forms.ModelForm):
    """Formulaire pour la création et modification d'un profil de juge."""
    
    class Meta:
        model = Judge
        fields = ['qualification_level', 'years_experience', 'certification_number', 'notes',
                 'is_technical_judge', 'is_combat_referee']
        widgets = {
            'qualification_level': forms.Select(attrs={'class': 'form-control'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'certification_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_technical_judge': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_combat_referee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    # Champs supplémentaires pour les informations du pratiquant
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        label=_("Email"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    birth_date = forms.DateField(
        label=_("Date de naissance"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        required=True
    )
    
    # Champ pour la discipline principale
    main_discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        label=_("Discipline principale"),
        required=False,
        empty_label=_("Sélectionnez une discipline"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Champ pour "Autre discipline" si non listée
    other_discipline = forms.CharField(
        label=_("Autre discipline"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Champ pour stocker le nom du grade (texte)
    grade = forms.CharField(
        label=_("Grade (nom)"),
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'grade'})
    )
    
    # Champ pour sélectionner un grade à partir d'une liste déroulante
    grade_display = forms.ChoiceField(
        label=_("Sélection du grade"),
        required=False,
        choices=[],  # Les choix seront définis dynamiquement
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_grade_display'})
    )
    
    # Champ caché pour stocker l'ID du grade sélectionné
    selected_grade_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'selected_grade_id'})
    )
    
    # Champ caché pour stocker le nom du grade sélectionné
    selected_grade_name = forms.CharField(
        required=False,
        widget=forms.HiddenInput(attrs={'id': 'selected_grade_name'})
    )
    
    disciplines = forms.ModelMultipleChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        label=_("Disciplines pratiquées"),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Définir les choix de base pour grade_display
        self.fields['grade_display'].choices = [
            ('', _('Sélectionnez d\'abord une discipline')),
            ('custom', _('Saisie personnalisée'))
        ]
        
        # Préremplir avec les données de l'utilisateur si disponibles
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
            
            # Si l'utilisateur a déjà un praticien
            practitioner = Practitioner.objects.filter(user=self.user).first()
            if practitioner:
                self.fields['birth_date'].initial = practitioner.birth_date
                
                # Gestion du grade
                if hasattr(practitioner, 'grade') and practitioner.grade:
                    if isinstance(practitioner.grade, str):
                        self.fields['grade'].initial = practitioner.grade
                    elif hasattr(practitioner.grade, 'name'):  # Si c'est un objet Grade
                        self.fields['grade'].initial = practitioner.grade.name
                        self.fields['selected_grade_id'].initial = practitioner.grade.id
                    else:
                        self.fields['grade'].initial = str(practitioner.grade)
                
                # Si le praticien a des disciplines
                if hasattr(practitioner, 'disciplines'):
                    disciplines = practitioner.disciplines.all()
                    self.fields['disciplines'].initial = disciplines
                    
                    # Si le pratiquant a au moins une discipline, la définir comme discipline principale
                    if disciplines.exists():
                        self.fields['main_discipline'].initial = disciplines.first().id
    
    def clean_grade_display(self):
        """Validation spécifique pour le champ grade_display."""
        value = self.cleaned_data.get('grade_display')
        
        # Accepter les valeurs vides, 'custom', ou les IDs numériques de grades
        if not value or value == 'custom' or (value.isdigit() and int(value) > 0):
            return value
        
        # Vérifier si c'est un ID de grade valide
        if value.isdigit():
            try:
                Grade.objects.get(id=int(value))
                return value
            except Grade.DoesNotExist:
                raise forms.ValidationError(_("Grade invalide sélectionné."))
        
        raise forms.ValidationError(_("Sélection de grade invalide."))
    
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Au moins un type de juge doit être sélectionné
        is_technical_judge = cleaned_data.get('is_technical_judge')
        is_combat_referee = cleaned_data.get('is_combat_referee')
        
        if not is_technical_judge and not is_combat_referee:
            raise forms.ValidationError(
                _("Vous devez sélectionner au moins un type de rôle : juge technique ou arbitre de combat.")
            )
        
        # Traitement du grade
        grade_display = cleaned_data.get('grade_display')
        selected_grade_id = cleaned_data.get('selected_grade_id') 
        grade_text = cleaned_data.get('grade')
        
        # Stockage pour la sélection du grade
        cleaned_data['selected_grade_id'] = None
        
        if grade_display and grade_display != 'custom' and grade_display.isdigit():
            # Grade sélectionné dans la liste déroulante
            try:
                grade_obj = Grade.objects.get(id=int(grade_display))
                cleaned_data['grade'] = grade_obj.name
                cleaned_data['selected_grade_id'] = grade_obj.id
            except Grade.DoesNotExist:
                self.add_error('grade_display', _("Grade invalide."))
        elif selected_grade_id: 
            try:
                grade_obj = Grade.objects.get(id=selected_grade_id)  
                cleaned_data['grade'] = grade_obj.name
            except Grade.DoesNotExist:
                self.add_error('selected_grade_id', _("Grade invalide."))  
        elif grade_display == 'custom' and grade_text:
            # Saisie libre ("Autre grade")
            cleaned_data['grade'] = grade_text
            cleaned_data['selected_grade_id'] = None
        elif grade_text:
            # Saisie directe dans le champ texte
            cleaned_data['grade'] = grade_text
            cleaned_data['selected_grade_id'] = None
        else:
            # Aucun grade spécifié
            cleaned_data['grade'] = ''
            cleaned_data['selected_grade_id'] = None
        
        # Traitement de la discipline principale
        main_discipline = cleaned_data.get('main_discipline')
        other_discipline = cleaned_data.get('other_discipline')
        
        # Si "Autre discipline" est sélectionnée et renseignée, on la garde en mémoire
        if not main_discipline and other_discipline:
            # On va la traiter dans la méthode save()
            pass
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Surcharge de la méthode save pour gérer le cas où nous n'avons pas d'instance existante.
        Cette méthode crée ou met à jour à la fois le Judge et le Practitioner associé.
        """
        judge = super().save(commit=False)
        
        # Si nous sommes en train de créer un nouveau juge (pas d'ID existant)
        if not judge.pk and hasattr(self, 'user'):
            # Vérifier si un Practitioner existe déjà pour cet utilisateur
            practitioner, created = Practitioner.objects.get_or_create(
                user=self.user,
                defaults={
                    'first_name': self.cleaned_data['first_name'],
                    'last_name': self.cleaned_data['last_name'],
                    'birth_date': self.cleaned_data.get('birth_date'),
                }
            )
            
            # Si le Practitioner existait déjà, mettre à jour ses informations
            if not created:
                practitioner.first_name = self.cleaned_data['first_name']
                practitioner.last_name = self.cleaned_data['last_name']
                if self.cleaned_data.get('birth_date'):
                    practitioner.birth_date = self.cleaned_data['birth_date']
                practitioner.save()
            
            # Associer le Judge au Practitioner
            judge.practitioner = practitioner
        
            # Traitement du grade
            grade_id = self.cleaned_data.get('selected_grade_id')
            grade_text = self.cleaned_data.get('grade', '')
            
            if hasattr(judge, 'practitioner') and judge.practitioner:
                grade_obj = None
                
                if grade_id:
                    # Si un ID de grade est fourni, essayer de le récupérer
                    try:
                        grade_obj = Grade.objects.get(id=grade_id)
                    except Grade.DoesNotExist:
                        # En cas d'erreur, laisser grade_obj à None
                        pass
                
                # Assigner l'objet Grade ou None au pratiquant
                judge.practitioner.grade = grade_obj
                
                # Si nous avons une valeur texte, l'enregistrer dans grade_text
                if grade_text and not grade_obj:
                    if hasattr(judge.practitioner, 'grade_text'):
                        judge.practitioner.grade_text = grade_text
                    
                # Sauvegarder le pratiquant
                judge.practitioner.save()
        
        if commit:
            judge.save()
            
            # Gérer les relations ManyToMany
            if hasattr(judge, 'practitioner') and hasattr(judge.practitioner, 'disciplines'):
                # Récupérer les disciplines déjà sélectionnées
                selected_disciplines = list(self.cleaned_data.get('disciplines', []))
                
                # Ajouter la discipline principale si elle est différente des disciplines déjà sélectionnées
                main_discipline = self.cleaned_data.get('main_discipline')
                if main_discipline and main_discipline not in selected_disciplines:
                    selected_disciplines.append(main_discipline)
                
                # Assigner toutes les disciplines au pratiquant
                if selected_disciplines:
                    judge.practitioner.disciplines.set(selected_disciplines)
        
        return judge

class JudgeTechnicalApplicationForm(forms.ModelForm):
    """Formulaire pour les candidatures de juge technique."""
    
    class Meta:
        model = JudgeTechnicalApplication
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'qualification_level', 'experience_years', 'qualifications',
            'certifications', 'message', 'agree_to_terms',
            'resume', 'certification_document'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification_level': forms.Select(attrs={'class': 'form-select'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'required': True}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'required': True}),
            'certifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'agree_to_terms': forms.CheckboxInput(attrs={'class': 'form-check-input', 'required': True}),
            'resume': forms.FileInput(attrs={'id': 'id_resume'}),
            'certification_document': forms.FileInput(attrs={'id': 'id_certification_document'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Préremplir avec les données de l'utilisateur si disponibles
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
            
            # Si l'utilisateur a déjà un profil de juge
            judge = Judge.objects.filter(user=user).first()
            if judge:
                self.fields['qualification_level'].initial = judge.qualification_level
                self.fields['experience_years'].initial = judge.experience_years
                self.fields['qualifications'].initial = judge.notes
                
    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        
        # Assurer la cohérence entre qualifications et certifications
        qualifications = cleaned_data.get('qualifications')
        certifications = cleaned_data.get('certifications')
        
        if not qualifications and certifications:
            # Si qualifications est vide mais certifications ne l'est pas, utiliser certifications
            cleaned_data['qualifications'] = certifications
        
        return cleaned_data


class JudgeQualificationForm(forms.ModelForm):
    """Formulaire pour les qualifications spécifiques des juges."""
    
    class Meta:
        model = JudgeQualification
        fields = ['qualification_type', 'level', 'certified_date']
        widgets = {
            'qualification_type': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'certified_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Ajouter d'autres validations si nécessaire
        return cleaned_data


class JudgeCompetitionAssignmentForm(forms.ModelForm):
    """Formulaire pour l'assignation des juges aux catégories de compétition."""
    
    class Meta:
        model = JudgeCompetitionAssignment
        fields = ['registration', 'category', 'assignment_type']
        widgets = {
            'registration': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'assignment_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        competition = kwargs.pop('competition', None)
        super().__init__(*args, **kwargs)
        
        if competition:
            # Filtrer les inscriptions pour cet événement
            self.fields['registration'].queryset = CompetitionRegistration.objects.filter(
                competition=competition,
                status='approved'
            ).filter(
                Q(is_technical_judge=True) | Q(is_combat_referee=True)
            )
            # Filtrer les catégories pour cet événement
            self.fields['category'].queryset = competition.categories.all()

    def clean(self):
        cleaned_data = super().clean()
        registration = cleaned_data.get('registration')
        category = cleaned_data.get('category')
        assignment_type = cleaned_data.get('assignment_type')
        
        # Vérifier qu'il n'y a pas d'assignation en double
        if registration and category and assignment_type:
            # Créer d'abord une requête de base
            base_query = JudgeCompetitionAssignment.objects.all()
            
            # Si nous modifions une instance existante, l'exclure de la recherche
            if self.instance and self.instance.pk:
                base_query = base_query.exclude(pk=self.instance.pk)
            
            # Vérifier les doublons
            duplicates = base_query.filter(
                registration=registration,
                category=category,
                assignment_type=assignment_type
            )
            
            if duplicates.exists():
                self.add_error(
                    None,
                    _("Ce juge est déjà assigné à cette catégorie avec ce type d'assignation.")
                )
        
        return cleaned_data


class JudgeSearchForm(forms.Form):
    """Formulaire pour la recherche de juges."""
    
    name = forms.CharField(
        label=_("Nom ou prénom"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _("Rechercher par nom...")})
    )
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.filter(is_active=True),
        label=_("Discipline"),
        required=False,
        empty_label=_("Toutes les disciplines"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    qualification_type = forms.ChoiceField(
        choices=[('', _("Tous types"))] + list(JudgeQualification._meta.get_field('qualification_type').choices),
        label=_("Type de qualification"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    level = forms.ChoiceField(
        choices=[('', _("Tous niveaux"))] + list(JudgeQualification._meta.get_field('level').choices),
        label=_("Niveau"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class JudgeAssignmentForm(forms.ModelForm):
    """
    Formulaire pour assigner des juges à des catégories de compétition.
    """
    class Meta:
        model = JudgeAssignment
        fields = [
            'registration', 
            'category', 
            'assignment_type', 
            'start_time', 
            'end_time', 
            'tatami', 
            'notes'
        ]
        widgets = {
            'judge': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'assignment_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tatami': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }
    
    def __init__(self, *args, competition=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if competition:
            # Filtrer les catégories pour cette compétition
            self.fields['category'].queryset = CompetitionCategory.objects.filter(
                competition=competition
            ).order_by('name')
            
            # Filtrer les juges ayant les qualifications pour cette compétition
            # ou les juges déjà assignés pour cette compétition
            qualified_judges = Judge.objects.filter(
                # Juges qualifiés dans la discipline
                qualifications__discipline=competition.discipline,
                # Juges actifs
                active=True
            ).distinct()
            
            assigned_judges = Judge.objects.filter(
                # Juges déjà assignés à cette compétition
                judgements__category__competition=competition
            ).distinct()
            
            # Combiner les deux querysets
            all_judges = (qualified_judges | assigned_judges).distinct()
            
            self.fields['judge'].queryset = all_judges.order_by('practitioner__last_name')
        
        # Si c'est une modification, désactiver certains champs
        if self.instance and self.instance.pk:
            if hasattr(self.instance, 'status') and self.instance.status == 'completed':
                for field in self.fields:
                    self.fields[field].widget.attrs['disabled'] = 'disabled'
                    
    def clean(self):
        cleaned_data = super().clean()
        judge = cleaned_data.get('judge')
        category = cleaned_data.get('category')
        assignment_type = cleaned_data.get('assignment_type')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Vérifier que le juge n'est pas déjà assigné à un autre événement au même moment
        if judge and category and start_time and end_time:
            # Créer la condition pour exclure l'instance actuelle
            if self.instance and self.instance.pk:
                base_query = JudgeAssignment.objects.exclude(pk=self.instance.pk)
            else:
                base_query = JudgeAssignment.objects.all()
            
            # Créer la condition de chevauchement temporel
            time_overlap_condition = (
                # Soit l'assignment existant commence pendant notre plage
                (Q(start_time__gte=start_time) & Q(start_time__lt=end_time)) |
                # Soit l'assignment existant finit pendant notre plage
                (Q(end_time__gt=start_time) & Q(end_time__lte=end_time)) |
                # Soit notre plage est entièrement contenue dans un assignment existant
                (Q(start_time__lte=start_time) & Q(end_time__gte=end_time))
            )
            
            # Appliquer les filtres séparément pour éviter le mélange d'arguments positionnels et nommés
            conflicting_assignments = base_query.filter(judge=judge)
            conflicting_assignments = conflicting_assignments.filter(time_overlap_condition)
            # Exclure également séparément
            conflicting_assignments = conflicting_assignments.exclude(category=category)
            conflicting_assignments = conflicting_assignments.exclude(assignment_type=assignment_type)
            
            if conflicting_assignments.exists():
                conflicts = [
                    f"{a.category.name} ({a.get_assignment_type_display()}): {a.start_time.strftime('%H:%M')} - {a.end_time.strftime('%H:%M')}"
                    for a in conflicting_assignments
                ]
                
                self.add_error(
                    None, 
                    _("Le juge est déjà assigné à d'autres événements qui se chevauchent: {}").format(
                        ", ".join(conflicts)
                    )
                )
        
        # Vérifier que la fin est après le début
        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', _("L'heure de fin doit être après l'heure de début."))
            
        return cleaned_data