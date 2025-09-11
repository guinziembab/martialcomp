from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import Board, Task, Column, TaskComment, BoardType

User = get_user_model()


class BoardForm(forms.ModelForm):
    """Form for creating and editing boards"""
    
    class Meta:
        model = Board
        fields = [
            'name', 'description', 'board_type', 'organization',
            'related_competition', 'is_public', 'allowed_roles',
            'color_theme', 'enable_time_tracking', 'enable_comments',
            'enable_attachments'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom du tableau')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description du tableau (optionnel)')
            }),
            'board_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'organization': forms.Select(attrs={
                'class': 'form-control'
            }),
            'related_competition': forms.Select(attrs={
                'class': 'form-control'
            }),
            'color_theme': forms.Select(attrs={
                'class': 'form-control'
            }),
            'allowed_roles': forms.SelectMultiple(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter organizations based on user memberships
            try:
                from apps.organizations.models import OrganizationMember
                user_orgs = OrganizationMember.objects.filter(
                    user=user,
                    is_active=True,
                    role__in=['owner', 'admin']
                ).values_list('organization', flat=True)
                
                self.fields['organization'].queryset = self.fields['organization'].queryset.filter(
                    id__in=user_orgs
                )
            except ImportError:
                pass
        
        # Color theme choices
        self.fields['color_theme'] = forms.ChoiceField(
            choices=[
                ('blue', _('Bleu')),
                ('green', _('Vert')),
                ('purple', _('Violet')),
                ('orange', _('Orange')),
                ('red', _('Rouge')),
                ('teal', _('Sarcelle')),
            ],
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        # Role choices for allowed_roles
        role_choices = [
            ('owner', _('Propriétaire')),
            ('admin', _('Administrateur')),
            ('manager', _('Gestionnaire')),
            ('member', _('Membre')),
            ('viewer', _('Observateur')),
        ]
        self.fields['allowed_roles'] = forms.MultipleChoiceField(
            choices=role_choices,
            required=False,
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
        )
    
    def clean(self):
        cleaned_data = super().clean()
        board_type = cleaned_data.get('board_type')
        related_competition = cleaned_data.get('related_competition')
        
        # Validate competition relation for competition boards
        if board_type == BoardType.COMPETITION and not related_competition:
            raise forms.ValidationError(
                _("Une compétition doit être sélectionnée pour ce type de tableau.")
            )
        
        return cleaned_data


class TaskForm(forms.ModelForm):
    """Form for creating and editing tasks"""
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'column', 'priority', 'status',
            'due_date', 'start_date', 'estimated_hours', 'labels',
            'parent_task'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Titre de la tâche')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Description détaillée (optionnel)')
            }),
            'column': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'start_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
                'min': '0'
            }),
            'parent_task': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, board=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if board:
            # Filter columns to current board
            self.fields['column'].queryset = board.columns.all()
            
            # Filter parent tasks to current board
            self.fields['parent_task'].queryset = board.tasks.filter(
                parent_task__isnull=True
            ).exclude(id=self.instance.id if self.instance.id else None)
        
        # Labels as a text field (will be converted to JSON)
        self.fields['labels_text'] = forms.CharField(
            label=_('Étiquettes'),
            required=False,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Séparez les étiquettes par des virgules')
            }),
            help_text=_('Exemple: urgent, important, bug')
        )
        
        # Remove labels from the form (handled by labels_text)
        if 'labels' in self.fields:
            del self.fields['labels']
        
        # Set initial value for labels_text
        if self.instance and self.instance.labels:
            self.fields['labels_text'].initial = ', '.join(self.instance.labels)
    
    def clean_labels_text(self):
        """Convert labels text to list"""
        labels_text = self.cleaned_data.get('labels_text', '')
        if labels_text:
            labels = [label.strip() for label in labels_text.split(',') if label.strip()]
            return labels
        return []
    
    def save(self, commit=True):
        """Save task with labels"""
        task = super().save(commit=False)
        
        # Handle labels
        labels_text = self.cleaned_data.get('labels_text', [])
        if isinstance(labels_text, list):
            task.labels = labels_text
        
        if commit:
            task.save()
        
        return task


class ColumnForm(forms.ModelForm):
    """Form for creating and editing columns"""
    
    class Meta:
        model = Column
        fields = ['name', 'color', 'wip_limit', 'is_done_column']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nom de la colonne')
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'wip_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
        }


class TaskCommentForm(forms.ModelForm):
    """Form for task comments"""
    
    class Meta:
        model = TaskComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Ajouter un commentaire...')
            })
        }


class QuickTaskForm(forms.Form):
    """Quick form for adding tasks from kanban view"""
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Titre de la tâche'),
            'required': True
        })
    )
    column_id = forms.IntegerField(widget=forms.HiddenInput())
    
    def __init__(self, *args, board=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.board = board
    
    def clean_column_id(self):
        """Validate column belongs to board"""
        column_id = self.cleaned_data.get('column_id')
        if self.board and column_id:
            try:
                column = self.board.columns.get(id=column_id)
                return column_id
            except Column.DoesNotExist:
                raise forms.ValidationError(_('Colonne invalide'))
        return column_id


class BoardFilterForm(forms.Form):
    """Form for filtering boards"""
    board_type = forms.ChoiceField(
        choices=[('', _('Tous les types'))] + list(BoardType.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    organization = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label=_('Toutes les organisations'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_archived = forms.BooleanField(
        required=False,
        label=_('Inclure les tableaux archivés')
    )
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if user:
            try:
                from apps.organizations.models import Organization, OrganizationMember
                user_orgs = OrganizationMember.objects.filter(
                    user=user,
                    is_active=True
                ).values_list('organization', flat=True)
                
                self.fields['organization'].queryset = Organization.objects.filter(
                    id__in=user_orgs
                )
            except ImportError:
                self.fields['organization'].queryset = Board.objects.none()


class TaskAssignmentForm(forms.Form):
    """Form for assigning users to tasks"""
    assignees = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label=_('Assigner à')
    )
    
    def __init__(self, *args, board=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if board and board.organization:
            try:
                from apps.organizations.models import OrganizationMember
                # Get organization members
                member_users = OrganizationMember.objects.filter(
                    organization=board.organization,
                    is_active=True
                ).values_list('user', flat=True)
                
                self.fields['assignees'].queryset = User.objects.filter(
                    id__in=member_users
                ).order_by('first_name', 'last_name')
            except ImportError:
                pass