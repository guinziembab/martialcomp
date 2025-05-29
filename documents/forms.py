from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .models import (
    DocumentFolder, DocumentTag, Document, DocumentShare, DocumentComment,
    TechnicalDocumentMetadata, GradeDocumentMetadata, CompetitionDocumentMetadata
)


class DocumentFolderForm(forms.ModelForm):
    """Formulaire pour la création et modification de dossiers"""
    class Meta:
        model = DocumentFolder
        fields = ['name', 'description', 'parent', 'is_public', 
                 'visible_to_admins', 'visible_to_federations', 'visible_to_clubs', 
                 'visible_to_practitioners', 'visible_to_judges']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les options de dossier parent aux dossiers accessibles par l'utilisateur
        if self.user and not self.user.is_superuser:
            # Logique pour filtrer les dossiers selon les permissions de l'utilisateur
            self.fields['parent'].queryset = DocumentFolder.objects.filter(
                # Dossiers publics ou dossiers dont l'utilisateur est propriétaire
                models.Q(is_public=True) | models.Q(owner=self.user)
            )
    
    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get('parent')
        name = cleaned_data.get('name')
        
        # Éviter les boucles de dossiers parents
        instance = getattr(self, 'instance', None)
        if instance and instance.pk and parent:
            parent_id = parent.pk
            while parent_id:
                if parent_id == instance.pk:
                    raise ValidationError(_("Un dossier ne peut pas être son propre parent ou ancêtre."))
                parent = DocumentFolder.objects.filter(pk=parent_id).first()
                parent_id = parent.parent_id if parent else None
        
        return cleaned_data


class DocumentTagForm(forms.ModelForm):
    """Formulaire pour la création et modification de tags"""
    class Meta:
        model = DocumentTag
        fields = ['name', 'color']
        widgets = {
            'color': forms.TextInput(attrs={'type': 'color'}),
        }


class DocumentUploadForm(forms.ModelForm):
    """Formulaire pour l'upload de documents"""
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'folder', 'tags', 
                 'document_type', 'is_public', 'is_template', 'expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les options de dossier aux dossiers accessibles par l'utilisateur
        if self.user and not self.user.is_superuser:
            # Logique pour filtrer les dossiers selon les permissions
            self.fields['folder'].queryset = DocumentFolder.objects.filter(
                # Dossiers publics ou dossiers dont l'utilisateur est propriétaire
                models.Q(is_public=True) | models.Q(owner=self.user)
            )
            
            # Limiter les tags accessibles
            self.fields['tags'].queryset = DocumentTag.objects.all()  # À adapter selon les besoins
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.created_by = self.user
            instance.modified_by = self.user
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class DocumentEditForm(forms.ModelForm):
    """Formulaire pour la modification de documents existants"""
    class Meta:
        model = Document
        fields = ['title', 'description', 'folder', 'tags', 
                 'document_type', 'is_public', 'is_template', 'expiry_date']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'expiry_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les options comme dans le formulaire d'upload
        if self.user and not self.user.is_superuser:
            self.fields['folder'].queryset = DocumentFolder.objects.filter(
                models.Q(is_public=True) | models.Q(owner=self.user)
            )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.user:
            instance.modified_by = self.user
        
        if commit:
            instance.save()
            self.save_m2m()
        
        return instance


class DocumentVersionForm(forms.ModelForm):
    """Formulaire pour l'upload d'une nouvelle version d'un document"""
    class Meta:
        model = Document
        fields = ['file']
    
    def __init__(self, *args, **kwargs):
        self.parent_document = kwargs.pop('parent_document', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = Document(
            title=self.parent_document.title,
            description=self.parent_document.description,
            folder=self.parent_document.folder,
            document_type=self.parent_document.document_type,
            is_public=self.parent_document.is_public,
            is_template=self.parent_document.is_template,
            parent=self.parent_document,
            is_latest_version=True,
            created_by=self.user,
            modified_by=self.user,
            file=self.cleaned_data['file']
        )
        
        if commit:
            instance.save()
            
            # Copie des tags
            if self.parent_document.tags.exists():
                instance.tags.set(self.parent_document.tags.all())
            
            # Copie des métadonnées spécifiques si elles existent
            self._copy_technical_metadata(instance)
            self._copy_grade_metadata(instance)
            self._copy_competition_metadata(instance)
        
        return instance
    
    def _copy_technical_metadata(self, instance):
        """Copie les métadonnées techniques du document parent vers la nouvelle version"""
        try:
            tech_metadata = self.parent_document.technical_metadata
            TechnicalDocumentMetadata.objects.create(
                document=instance,
                discipline=tech_metadata.discipline,
                level=tech_metadata.level,
                content_type=tech_metadata.content_type,
                requirements=tech_metadata.requirements,
                keywords=tech_metadata.keywords
            )
        except:
            pass
    
    def _copy_grade_metadata(self, instance):
        """Copie les métadonnées de grade du document parent vers la nouvelle version"""
        try:
            grade_metadata = self.parent_document.grade_metadata
            GradeDocumentMetadata.objects.create(
                document=instance,
                grade=grade_metadata.grade,
                document_type=grade_metadata.document_type,
                valid_from=grade_metadata.valid_from,
                valid_until=grade_metadata.valid_until,
                issuing_authority=grade_metadata.issuing_authority,
                authorized_by=grade_metadata.authorized_by
            )
        except:
            pass
    
    def _copy_competition_metadata(self, instance):
        """Copie les métadonnées de compétition du document parent vers la nouvelle version"""
        try:
            comp_metadata = self.parent_document.competition_metadata
            CompetitionDocumentMetadata.objects.create(
                document=instance,
                competition=comp_metadata.competition,
                document_type=comp_metadata.document_type,
                category=comp_metadata.category,
                event_date=comp_metadata.event_date
            )
        except:
            pass


class DocumentShareForm(forms.ModelForm):
    """Formulaire pour le partage de documents"""
    # Champs pour faciliter la sélection du type d'entité avec qui partager
    SHARE_TYPE_USER = 'user'
    SHARE_TYPE_CLUB = 'club'
    SHARE_TYPE_FEDERATION = 'federation'
    SHARE_TYPE_GROUP = 'group'
    
    SHARE_TYPE_CHOICES = [
        (SHARE_TYPE_USER, _("Utilisateur")),
        (SHARE_TYPE_CLUB, _("Club")),
        (SHARE_TYPE_FEDERATION, _("Fédération")),
        (SHARE_TYPE_GROUP, _("Groupe")),
    ]
    
    share_type = forms.ChoiceField(
        label=_("Type de partage"),
        choices=SHARE_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial=SHARE_TYPE_USER
    )
    
    # ID de l'entité sélectionnée (selon le type)
    entity_id = forms.CharField(
        label=_("ID de l'entité"),
        required=False,
        widget=forms.HiddenInput()
    )
    
    class Meta:
        model = DocumentShare
        fields = ['access_level', 'expires_at', 'notify_on_access']
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('document', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        share_type = cleaned_data.get('share_type')
        entity_id = cleaned_data.get('entity_id')
        
        if not entity_id:
            raise ValidationError(_("Vous devez sélectionner une entité avec qui partager le document."))
        
        # Vérifier que l'entité sélectionnée existe
        try:
            if share_type == self.SHARE_TYPE_USER:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                self.entity = User.objects.get(pk=entity_id)
            elif share_type == self.SHARE_TYPE_CLUB:
                from competitions.models import Club
                self.entity = Club.objects.get(pk=entity_id)
                self.content_type = ContentType.objects.get_for_model(Club)
            elif share_type == self.SHARE_TYPE_FEDERATION:
                from competitions.models import Federation
                self.entity = Federation.objects.get(pk=entity_id)
                self.content_type = ContentType.objects.get_for_model(Federation)
            elif share_type == self.SHARE_TYPE_GROUP:
                from django.contrib.auth.models import Group
                self.entity = Group.objects.get(pk=entity_id)
                self.content_type = ContentType.objects.get_for_model(Group)
            else:
                raise ValidationError(_("Type de partage non valide."))
        except Exception as e:
            raise ValidationError(_("L'entité sélectionnée n'existe pas ou est invalide."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        instance.document = self.document
        instance.created_by = self.user
        
        share_type = self.cleaned_data['share_type']
        
        if share_type == self.SHARE_TYPE_USER:
            instance.user = self.entity
        else:
            instance.group_content_type = self.content_type
            instance.group_object_id = self.entity.pk
        
        if commit:
            instance.save()
        
        return instance


class DocumentCommentForm(forms.ModelForm):
    """Formulaire pour les commentaires sur les documents"""
    class Meta:
        model = DocumentComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': _("Ajouter un commentaire...")}),
        }
    
    def __init__(self, *args, **kwargs):
        self.document = kwargs.pop('document', None)
        self.user = kwargs.pop('user', None)
        self.parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        instance.document = self.document
        instance.author = self.user
        instance.parent = self.parent
        
        if commit:
            instance.save()
        
        return instance