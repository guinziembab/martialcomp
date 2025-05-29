# permissions_manager/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.apps import apps

from .models import Permission, Role, UserRoleAssignment

class RoleForm(forms.ModelForm):
    """Formulaire pour la création et modification de rôles"""
    class Meta:
        model = Role
        fields = ['name', 'description', 'context_type', 'permissions', 'is_system_role']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'permissions': forms.CheckboxSelectMultiple(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Grouper les permissions par catégorie
        permissions = Permission.objects.all().order_by('category', 'name')
        
        # Créer un choix de groupe pour chaque catégorie
        choices = []
        current_category = None
        category_choices = []
        
        for permission in permissions:
            if permission.category != current_category:
                if current_category is not None:
                    choices.append([current_category, category_choices])
                current_category = permission.category
                category_choices = []
            
            category_choices.append((permission.id, permission.name))
        
        # Ajouter la dernière catégorie
        if current_category is not None:
            choices.append([current_category, category_choices])
        
        self.fields['permissions'].choices = choices
        
        # Seuls les superutilisateurs peuvent créer des rôles système
        if not kwargs.get('instance') and not self.initial.get('is_system_role'):
            self.fields['is_system_role'].widget = forms.HiddenInput()
            self.fields['is_system_role'].initial = False

class UserRoleAssignmentForm(forms.ModelForm):
    """Formulaire pour l'attribution de rôles aux utilisateurs"""
    context_type = forms.ChoiceField(
        choices=[('', '-- Sélectionnez un type --')],
        required=False,
        label=_("Type de contexte"),
        help_text=_("Laissez vide pour un rôle global")
    )
    
    context_id = forms.IntegerField(
        required=False,
        label=_("ID du contexte"),
        widget=forms.Select(choices=[('', '-- Sélectionnez une entité --')])
    )
    
    class Meta:
        model = UserRoleAssignment
        fields = ['user', 'role', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Récupérer les types de modèles disponibles
        content_types = ContentType.objects.filter(
            app_label__in=['competitions', 'grades', 'permissions_manager']
        ).exclude(model__in=['permission', 'role', 'userroleassignment'])
        
        # Préparer les choix pour context_type
        context_type_choices = [('', '-- Sélectionnez un type --')]
        for ct in content_types:
            context_type_choices.append((ct.id, f"{ct.app_label}.{ct.model}"))
        
        self.fields['context_type'].choices = context_type_choices
        
        # Si nous modifions une attribution existante
        instance = kwargs.get('instance')
        if instance and instance.content_type:
            self.fields['context_type'].initial = instance.content_type.id
            
            # Charger les choix pour cette entité
            model_class = instance.content_type.model_class()
            choices = [(obj.id, str(obj)) for obj in model_class.objects.all()]
            self.fields['context_id'].widget.choices = [('', '-- Sélectionnez une entité --')] + choices
            self.fields['context_id'].initial = instance.object_id
    
    def clean(self):
        cleaned_data = super().clean()
        context_type_id = cleaned_data.get('context_type')
        context_id = cleaned_data.get('context_id')
        
        # Si un type de contexte est spécifié, l'ID de contexte est requis
        if context_type_id and not context_id:
            self.add_error('context_id', _("Ce champ est requis lorsqu'un type de contexte est spécifié."))
        
        # Si les deux sont spécifiés, vérifier que l'entité existe
        if context_type_id and context_id:
            try:
                content_type = ContentType.objects.get(id=context_type_id)
                model_class = content_type.model_class()
                model_class.objects.get(id=context_id)
            except Exception as e:
                self.add_error('context_id', _("Entité introuvable: %(error)s") % {'error': str(e)})
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Définir content_type et object_id
        context_type_id = self.cleaned_data.get('context_type')
        context_id = self.cleaned_data.get('context_id')
        
        if context_type_id and context_id:
            instance.content_type = ContentType.objects.get(id=context_type_id)
            instance.object_id = context_id
        else:
            instance.content_type = None
            instance.object_id = None
        
        if commit:
            instance.save()
        
        return instance