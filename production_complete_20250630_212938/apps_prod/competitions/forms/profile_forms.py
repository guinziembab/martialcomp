from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from ..models import UserProfile, Practitioner
import re

class PractitionerProfileForm(forms.ModelForm):
    """Formulaire pour la modification du profil pratiquant (utilise le modèle Practitioner)."""
    
    # Champs utilisateur
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Prénom"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre prénom")
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Nom"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre nom de famille")
        })
    )
    
    email = forms.EmailField(
        required=True,
        label=_("Adresse e-mail"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("votre@email.com")
        })
    )
    
    # Champs du pratiquant
    phone = forms.CharField(
        max_length=20,
        required=False,
        label=_("Téléphone"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre numéro de téléphone")
        })
    )
    
    address = forms.CharField(
        required=False,
        label=_("Adresse"),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Votre adresse complète")
        })
    )
    
    photo = forms.ImageField(
        required=False,
        label=_("Photo de profil"),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    class Meta:
        model = Practitioner
        fields = ['phone', 'address', 'photo']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir les champs utilisateur si un utilisateur est fourni
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def clean_email(self):
        """Validation de l'email pour éviter les doublons."""
        email = self.cleaned_data.get('email')
        if email:
            # Vérifier si l'email existe déjà pour un autre utilisateur
            if User.objects.filter(email=email).exclude(pk=self.user.pk if self.user else None).exists():
                raise ValidationError(_("Cette adresse e-mail est déjà utilisée par un autre compte."))
        return email
    
    def clean_phone(self):
        """Validation du numéro de téléphone."""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Supprimer tous les espaces, tirets et parenthèses
            cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone)
            # Vérifier que le numéro contient uniquement des chiffres et éventuellement un + au début
            if not re.match(r'^\+?[0-9]+$', cleaned_phone):
                raise ValidationError(_("Le numéro de téléphone doit contenir uniquement des chiffres."))
            # Vérifier la longueur (entre 8 et 15 chiffres)
            digits_only = re.sub(r'[^\d]', '', cleaned_phone)
            if len(digits_only) < 8 or len(digits_only) > 15:
                raise ValidationError(_("Le numéro de téléphone doit contenir entre 8 et 15 chiffres."))
        return phone
    
    def clean_photo(self):
        """Validation de la photo."""
        photo = self.cleaned_data.get('photo')
        if photo:
            # Vérifier la taille du fichier (5 MB max)
            if photo.size > 5 * 1024 * 1024:  # 5 MB
                raise ValidationError(_("La taille de l'image ne doit pas dépasser 5 MB."))
            
            # Vérifier le type de fichier
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if photo.content_type not in allowed_types:
                raise ValidationError(_("Format d'image non supporté. Utilisez JPG, PNG, GIF ou WebP."))
        
        return photo
    
    def save(self, commit=True):
        """Sauvegarde du profil pratiquant et des données utilisateur."""
        practitioner = super().save(commit=False)
        
        # Mettre à jour les informations de l'utilisateur
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            
            if commit:
                self.user.save()
        
        if commit:
            practitioner.save()
        
        return practitioner


# Conserver les anciens formulaires pour compatibilité
class UserProfileForm(forms.ModelForm):
    """Formulaire pour la modification du profil utilisateur (deprecated - utiliser PractitionerProfileForm)."""
    
    # Champs utilisateur
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Prénom"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre prénom")
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Nom"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _("Votre nom de famille")
        })
    )
    
    email = forms.EmailField(
        required=True,
        label=_("Adresse e-mail"),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _("votre@email.com")
        })
    )
    
    class Meta:
        model = UserProfile
        fields = []  # Pas de champs du profil car ils n'existent pas
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Pré-remplir les champs utilisateur si un utilisateur est fourni
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def save(self, commit=True):
        """Sauvegarde des données utilisateur uniquement."""
        profile = super().save(commit=False)
        
        # Mettre à jour les informations de l'utilisateur
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        
        return profile


class UserProfileQuickEditForm(forms.ModelForm):
    """Formulaire simplifié pour la modification rapide du profil."""
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Prénom"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label=_("Nom"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    email = forms.EmailField(
        required=True,
        label=_("E-mail"),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = UserProfile
        fields = []  # Pas de champs du profil car ils n'existent pas
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name
            self.fields['email'].initial = self.user.email
    
    def save(self, commit=True):
        """Sauvegarde simplifiée."""
        profile = super().save(commit=False)
        
        if self.user:
            self.user.first_name = self.cleaned_data.get('first_name', '')
            self.user.last_name = self.cleaned_data.get('last_name', '')
            self.user.email = self.cleaned_data.get('email', '')
            
            if commit:
                self.user.save()
        
        if commit:
            profile.save()
        
        return profile


class AvatarUploadForm(forms.Form):
    """Formulaire pour l'upload d'avatar uniquement."""
    
    avatar = forms.ImageField(
        label=_("Photo de profil"),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    def clean_avatar(self):
        """Validation de l'avatar."""
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Vérifier la taille du fichier (2 MB max pour l'upload simple)
            if avatar.size > 2 * 1024 * 1024:  # 2 MB
                raise ValidationError(_("La taille de l'image ne doit pas dépasser 2 MB."))
            
            # Vérifier le type de fichier
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if avatar.content_type not in allowed_types:
                raise ValidationError(_("Format d'image non supporté. Utilisez JPG, PNG ou GIF."))
            
            # Vérifier les dimensions minimales
            try:
                from PIL import Image
                image = Image.open(avatar)
                width, height = image.size
                
                # Dimensions minimales recommandées
                if width < 100 or height < 100:
                    raise ValidationError(_("L'image doit faire au moins 100x100 pixels."))
                
                # Dimensions maximales
                if width > 2000 or height > 2000:
                    raise ValidationError(_("L'image ne doit pas dépasser 2000x2000 pixels."))
                    
            except ImportError:
                # PIL n'est pas installé, on passe la validation des dimensions
                pass
            except Exception:
                raise ValidationError(_("Impossible de traiter cette image."))
        
        return avatar
