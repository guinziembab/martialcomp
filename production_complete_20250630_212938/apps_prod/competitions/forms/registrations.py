from django import forms
from django.utils.translation import gettext_lazy as _
from ..models import CompetitionRegistration, CompetitionRole, Practitioner, CompetitionCategory

class CompetitionRegistrationForm(forms.ModelForm):
    """
    Formulaire d'inscription à une compétition.
    Gère les champs dynamiques pour les types de compétition et catégories,
    ainsi que la mise à jour des informations personnelles du pratiquant.
    """
    # Champs pour les informations personnelles du pratiquant
    first_name = forms.CharField(
        label=_("Prénom"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        label=_("Nom"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    birth_date = forms.DateField(
        label=_("Date de naissance"),
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    grade = forms.CharField(
        label=_("Grade"),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    # Champ calculé automatiquement basé sur la date de naissance
    age = forms.IntegerField(
        label=_("Âge"),
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Ajout de champs pour les rôles supplémentaires
    is_competitor = forms.BooleanField(
        label=_("Compétiteur"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_coach = forms.BooleanField(
        label=_("Coach"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_volunteer = forms.BooleanField(
        label=_("Bénévole"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Niveaux de qualification pour les juges - non requis, définis par l'administration
    QUALIFICATION_LEVELS = [
        ('', _('Sera défini par l\'administration')),
        ('pending', _('En attente de validation')),
        ('novice', _('Novice')),
        ('regional', _('Régional')),
        ('national', _('National')),
        ('international', _('International')),
    ]
    
    is_technical_judge = forms.BooleanField(
        label=_("Juge Technique"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    technical_judge_level = forms.ChoiceField(
        label=_("Niveau de qualification"),
        choices=QUALIFICATION_LEVELS,
        required=False,
        initial='pending',
        help_text=_("Votre niveau de qualification sera validé par l'administration."),
        widget=forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'})
    )
    
    is_combat_referee = forms.BooleanField(
        label=_("Arbitre Combat"),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    combat_referee_level = forms.ChoiceField(
        label=_("Niveau de qualification"),
        choices=QUALIFICATION_LEVELS,
        required=False,
        initial='pending',
        help_text=_("Votre niveau de qualification sera validé par l'administration."),
        widget=forms.Select(attrs={'class': 'form-control', 'disabled': 'disabled'})
    )
    
    # Champ pour les notes/commentaires
    notes = forms.CharField(
        label=_("Notes ou commentaires"),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Informations supplémentaires pour les organisateurs...")
        })
    )
    
    class Meta:
        model = CompetitionRegistration
        fields = [
            'is_technical_judge', 
            'is_combat_referee', 
            'roles', 
            'notes'
        ]
        widgets = {
            'roles': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.competition = kwargs.pop('competition', None)
        self.practitioner = kwargs.pop('practitioner', None)
        
        super().__init__(*args, **kwargs)
        
        # Pré-remplir les informations personnelles
        if self.practitioner:
            self.fields['first_name'].initial = self.practitioner.first_name
            self.fields['last_name'].initial = self.practitioner.last_name
            self.fields['birth_date'].initial = self.practitioner.birth_date
            self.fields['grade'].initial = self.practitioner.grade
            
            # Calculer l'âge du pratiquant (si birth_date est disponible)
            from django.utils import timezone
            import datetime
            
            if self.practitioner.birth_date:
                today = timezone.now().date()
                born = self.practitioner.birth_date
                age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
                self.fields['age'].initial = age
        
        # Pré-remplir les autres champs si une inscription existe déjà
        if self.instance and self.instance.pk:
            self.fields['is_competitor'].initial = self.instance.is_competitor
            self.fields['is_coach'].initial = self.instance.is_coach
            self.fields['is_technical_judge'].initial = self.instance.is_technical_judge
            self.fields['is_combat_referee'].initial = self.instance.is_combat_referee
            
            # Si des données supplémentaires sont stockées ailleurs (comme dans un JSON ou un autre modèle)
            # on pourrait les récupérer ici
            
        if self.competition:
            # Filtrer les rôles disponibles pour cet événement
            try:
                self.fields['roles'].queryset = CompetitionRole.objects.filter(competition=self.competition)
            except Exception:
                # Si CompetitionRole n'est pas disponible ou une erreur survient
                if 'roles' in self.fields:
                    self.fields['roles'].queryset = CompetitionRole.objects.none()
            
            # Générer des champs dynamiques pour chaque type de compétition
            for comp_type in self.competition.competition_types.all():
                type_field_name = f'type_{comp_type.id}'
                
                # Champ pour sélectionner le type de compétition
                self.fields[type_field_name] = forms.BooleanField(
                    label=comp_type.name,
                    required=False,
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-check-input competition-type-checkbox',
                        'data-type-id': comp_type.id
                    })
                )
                
                # Pré-sélectionner si déjà inscrit à ce type de compétition
                if self.instance and self.instance.pk and hasattr(self.instance, 'competition_types'):
                    self.fields[type_field_name].initial = comp_type in self.instance.competition_types.all()
                
                # Récupérer les catégories disponibles pour ce type
                categories = self.competition.categories.filter(competition_type=comp_type)
                
                if categories.exists():
                    category_field_name = f'category_for_type_{comp_type.id}'
                    
                    # Créer les choix pour le champ de catégorie
                    choices = [(str(cat.id), cat.name) for cat in categories]
                    
                    self.fields[category_field_name] = forms.ChoiceField(
                        label=_("Catégorie"),
                        choices=choices,
                        required=False,
                        widget=forms.RadioSelect(attrs={
                            'class': 'category-radio',
                            'data-type-id': comp_type.id
                        })
                    )
                    
                    # Si l'utilisateur est déjà inscrit, pré-sélectionner sa catégorie
                    if self.instance and self.instance.pk:
                        selected_categories = self.instance.categories.filter(competition_type=comp_type).first()
                        if selected_categories:
                            self.fields[category_field_name].initial = str(selected_categories.id)
    
    def clean(self):
        """
        Validation globale du formulaire.
        Vérifie la cohérence des données et les contraintes métier.
        """
        cleaned_data = super().clean()
        
        # Si pas de compétition, pas de validation supplémentaire
        if not self.competition:
            return cleaned_data
        
        # Vérifier la cohérence des rôles d'arbitrage
        is_technical_judge = cleaned_data.get('is_technical_judge', False)
        is_combat_referee = cleaned_data.get('is_combat_referee', False)
        
        # Les niveaux de qualification sont définis par les administrateurs
        # Pas besoin de vérifier ici, on les définit comme "pending" par défaut
        
        # Vérifier que pour chaque type sélectionné, une catégorie est choisie
        is_competitor = cleaned_data.get('is_competitor', False)
        
        # Si l'utilisateur est compétiteur, au moins un type doit être sélectionné
        if is_competitor:
            has_selected_type = False
            
            for comp_type in self.competition.competition_types.all():
                type_field_name = f'type_{comp_type.id}'
                category_field_name = f'category_for_type_{comp_type.id}'
                
                if type_field_name in cleaned_data and cleaned_data.get(type_field_name):
                    has_selected_type = True
                    
                    # Si le type est sélectionné, une catégorie doit être choisie
                    if (category_field_name in self.fields and 
                        (category_field_name not in cleaned_data or not cleaned_data.get(category_field_name))):
                        self.add_error(
                            category_field_name,
                            _("Vous devez sélectionner une catégorie pour ce type de compétition.")
                        )
            
            if not has_selected_type:
                self.add_error(
                    None,
                    _("En tant que compétiteur, vous devez sélectionner au moins un type de compétition.")
                )
        
        # Vérifier que l'utilisateur a sélectionné au moins un rôle
        if not (is_competitor or is_technical_judge or is_combat_referee or 
                cleaned_data.get('is_coach', False) or cleaned_data.get('is_volunteer', False)):
            self.add_error(
                None,
                _("Vous devez sélectionner au moins un rôle pour cette compétition.")
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        """
        Sauvegarde l'inscription et gère les champs personnalisés et les relations.
        """
        # Mettre à jour les informations du pratiquant
        if self.practitioner:
            self.practitioner.first_name = self.cleaned_data['first_name']
            self.practitioner.last_name = self.cleaned_data['last_name']
            self.practitioner.birth_date = self.cleaned_data['birth_date']
            self.practitioner.grade = self.cleaned_data['grade']
            if commit:
                self.practitioner.save()
        
        # Créer ou mettre à jour l'inscription
        instance = super().save(commit=False)
        
        # Assigner le pratiquant et la compétition
        instance.practitioner = self.practitioner
        if self.competition and not instance.competition:
            instance.competition = self.competition
        
        # Assigner les rôles supplémentaires
        instance.is_competitor = self.cleaned_data.get('is_competitor', False)
        instance.is_coach = self.cleaned_data.get('is_coach', False)
        instance.is_volunteer = self.cleaned_data.get('is_volunteer', False)
        instance.is_technical_judge = self.cleaned_data.get('is_technical_judge', False)
        instance.is_combat_referee = self.cleaned_data.get('is_combat_referee', False)
        
        # Définir les niveaux de qualification à "pending" si juge ou arbitre
        if instance.is_technical_judge and hasattr(instance, 'technical_judge_level'):
            instance.technical_judge_level = 'pending'
        
        if instance.is_combat_referee and hasattr(instance, 'combat_referee_level'):
            instance.combat_referee_level = 'pending'
        
        # Assigner les notes
        instance.notes = self.cleaned_data.get('notes', '')
        
        if commit:
            instance.save()
            self.save_m2m()
            
            # Traiter les types de compétition sélectionnés
            selected_types = []
            selected_categories = []
            
            for comp_type in self.competition.competition_types.all():
                type_field_name = f'type_{comp_type.id}'
                category_field_name = f'category_for_type_{comp_type.id}'
                
                if self.cleaned_data.get(type_field_name):
                    selected_types.append(comp_type)
                    
                    # Ajouter la catégorie sélectionnée
                    category_id = self.cleaned_data.get(category_field_name)
                    if category_id:
                        try:
                            category = CompetitionCategory.objects.get(id=category_id)
                            selected_categories.append(category)
                        except CompetitionCategory.DoesNotExist:
                            pass
            
            # Mettre à jour les types de compétition
            instance.competition_types.set(selected_types)
            
            # Mettre à jour les catégories si le modèle a cette relation
            if hasattr(instance, 'categories'):
                instance.categories.set(selected_categories)
        
        return instance
    

class BulkRegistrationApprovalForm(forms.Form):
    """
    Formulaire pour approuver ou rejeter plusieurs inscriptions en une seule opération.
    """
    registrations = forms.ModelMultipleChoiceField(
        queryset=CompetitionRegistration.objects.none(),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
        label=_("Sélectionner les inscriptions")
    )
    
    action = forms.ChoiceField(
        choices=[
            ('approve', _("Approuver")),
            ('reject', _("Rejeter")),
            ('delete', _("Supprimer"))
        ],
        widget=forms.RadioSelect(),
        required=True,
        label=_("Action à effectuer")
    )
    
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label=_("Motif de rejet"),
        help_text=_("Obligatoire si l'action est 'Rejeter'")
    )
    
    notify_participants = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Notifier les participants")
    )
    
    def __init__(self, *args, competition=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if competition:
            # Filtrer les inscriptions pour cette compétition
            self.fields['registrations'].queryset = CompetitionRegistration.objects.filter(
                competition=competition,
                status='pending'
            ).select_related('practitioner', 'practitioner__club')
    
    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get('action')
        rejection_reason = cleaned_data.get('rejection_reason')
        registrations = cleaned_data.get('registrations')
        
        if not registrations or registrations.count() == 0:
            raise forms.ValidationError(_("Vous devez sélectionner au moins une inscription."))
        
        if action == 'reject' and not rejection_reason:
            self.add_error('rejection_reason', _("Vous devez fournir un motif de rejet."))
        
        return cleaned_data
    
    def process_registrations(self):
        """
        Traite les inscriptions selon l'action choisie.
        Retourne un tuple (nombre_modifiés, nombre_notifiés)
        """
        action = self.cleaned_data['action']
        registrations = self.cleaned_data['registrations']
        rejection_reason = self.cleaned_data.get('rejection_reason', '')
        notify = self.cleaned_data.get('notify_participants', False)
        
        modified_count = 0
        notified_count = 0
        
        for registration in registrations:
            if action == 'approve':
                registration.status = 'approved'
                registration.save()
                modified_count += 1
                
                # Notifications
                if notify:
                    try:
                        # Insérez ici votre logique de notification
                        # Par exemple, en utilisant le système de notifications Django
                        # ou en envoyant un email
                        notified_count += 1
                    except Exception as e:
                        # Gérer les erreurs de notification mais continuer le traitement
                        pass
                        
            elif action == 'reject':
                registration.status = 'rejected'
                registration.notes = f"{registration.notes}\n\nMotif de rejet: {rejection_reason}" if registration.notes else f"Motif de rejet: {rejection_reason}"
                registration.save()
                modified_count += 1
                
                # Notifications
                if notify:
                    try:
                        # Insérez ici votre logique de notification
                        notified_count += 1
                    except Exception as e:
                        # Gérer les erreurs de notification
                        pass
                        
            elif action == 'delete':
                registration.delete()
                modified_count += 1
        
        return (modified_count, notified_count)
    

class CategoryAssignmentForm(forms.Form):
    """
    Formulaire pour assigner des participants à des catégories de compétition.
    """
    practitioner = forms.ModelChoiceField(
        queryset=Practitioner.objects.none(),
        required=True,
        label=_("Participant"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    categories = forms.ModelMultipleChoiceField(
        queryset=CompetitionCategory.objects.none(),
        required=True,
        label=_("Catégories"),
        widget=forms.CheckboxSelectMultiple(),
        help_text=_("Sélectionnez les catégories auxquelles assigner ce participant")
    )
    
    def __init__(self, *args, competition=None, practitioner=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if competition:
            # Filtrer les catégories pour cette compétition
            self.fields['categories'].queryset = CompetitionCategory.objects.filter(
                competition=competition
            ).order_by('name')
            
            # Filtrer les participants pour cette compétition
            if practitioner:
                # Si un participant spécifique est fourni, le préselectionner
                self.fields['practitioner'].queryset = Practitioner.objects.filter(id=practitioner.id)
                self.fields['practitioner'].initial = practitioner
                self.fields['practitioner'].widget.attrs['disabled'] = 'disabled'
            else:
                # Sinon, afficher tous les participants inscrits
                self.fields['practitioner'].queryset = Practitioner.objects.filter(
                    registrations__competition=competition,
                    registrations__status='approved',
                    registrations__is_competitor=True
                ).distinct().order_by('last_name', 'first_name')
        
    def save(self):
        """
        Enregistre les assignations des catégories pour le participant sélectionné.
        Retourne un tuple (participant, liste_categories_ajoutées, liste_categories_retirées)
        """
        practitioner = self.cleaned_data['practitioner']
        selected_categories = self.cleaned_data['categories']
        
        # Récupérer les inscriptions actuelles
        from competitions.models import CompetitionRegistration
        
        registration = CompetitionRegistration.objects.filter(
            practitioner=practitioner,
            competition=selected_categories.first().competition  # Toutes les catégories sont de la même compétition
        ).first()
        
        if not registration:
            # Si l'inscription n'existe pas, en créer une nouvelle
            registration = CompetitionRegistration.objects.create(
                practitioner=practitioner,
                competition=selected_categories.first().competition,
                status='approved',
                is_competitor=True
            )
        
        # Récupérer les catégories actuelles
        current_categories = list(registration.categories.all())
        
        # Mettre à jour les catégories
        registration.categories.set(selected_categories)
        
        # Identifier les catégories ajoutées et retirées pour le rapport
        added_categories = [cat for cat in selected_categories if cat not in current_categories]
        removed_categories = [cat for cat in current_categories if cat not in selected_categories]
        
        return (practitioner, added_categories, removed_categories)