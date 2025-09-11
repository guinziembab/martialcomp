from django import forms
from apps.competitions.models.organization_templates import OrganizationTemplate
import re
import json

class OrganizationTemplateForm(forms.ModelForm):
    """Formulaire pour éditer les templates d'organisation"""
    
    class Meta:
        model = OrganizationTemplate
        fields = '__all__'
        exclude = ['organization', 'created_at', 'updated_at']
        widgets = {
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'background_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'text_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'hero_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre principal'}),
            'hero_subtitle': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Sous-titre'}),
            'about_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre Ã€ propos'}),
            'about_content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Contenu Ã€ propos'}),
            'website_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
            'instagram_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://instagram.com/...'}),
            'youtube_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/...'}),
            'twitter_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/...'}),
            'hero_button_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'En savoir plus'}),
            'hero_button_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '#about'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter des classes CSS pour les champs de description et légende
        for field_name in self.fields:
            if 'description' in field_name or 'caption' in field_name:
                self.fields[field_name].widget.attrs.update({'class': 'form-control', 'rows': 2})
    
    def clean_primary_color(self):
        color = self.cleaned_data['primary_color']
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError('Format de couleur invalide (ex: #FF0000)')
        return color
    
    def clean_secondary_color(self):
        color = self.cleaned_data['secondary_color']
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError('Format de couleur invalide (ex: #FF0000)')
        return color
    
    def clean_accent_color(self):
        color = self.cleaned_data['accent_color']
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError('Format de couleur invalide (ex: #FF0000)')
        return color
    
    def clean_background_color(self):
        color = self.cleaned_data['background_color']
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError('Format de couleur invalide (ex: #FF0000)')
        return color
    
    def clean_text_color(self):
        color = self.cleaned_data['text_color']
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError('Format de couleur invalide (ex: #FF0000)')
        return color
    
    def clean_video_1_url(self):
        url = self.cleaned_data.get('video_1_url')
        if url and not self._is_valid_video_url(url):
            raise forms.ValidationError('URL de vidéo invalide (YouTube/Vimeo uniquement)')
        return url
    
    def clean_video_2_url(self):
        url = self.cleaned_data.get('video_2_url')
        if url and not self._is_valid_video_url(url):
            raise forms.ValidationError('URL de vidéo invalide (YouTube/Vimeo uniquement)')
        return url
    
    def clean_video_3_url(self):
        url = self.cleaned_data.get('video_3_url')
        if url and not self._is_valid_video_url(url):
            raise forms.ValidationError('URL de vidéo invalide (YouTube/Vimeo uniquement)')
        return url
    
    def clean_custom_sections(self):
        """Valide le JSON des sections personnalisées"""
        custom_sections = self.cleaned_data.get('custom_sections')
        if custom_sections:
            if isinstance(custom_sections, str):
                try:
                    json.loads(custom_sections)
                except json.JSONDecodeError:
                    raise forms.ValidationError('Format JSON invalide pour les sections personnalisées')
        return custom_sections
    
    def _is_valid_video_url(self, url):
        """Vérifie si l'URL est une vidéo YouTube ou Vimeo valide"""
        youtube_pattern = r'(youtube\.com|youtu\.be)'
        vimeo_pattern = r'vimeo\.com'
        return bool(re.search(youtube_pattern, url) or re.search(vimeo_pattern, url))
    
    def apply_theme_colors(self, theme_name):
        """Applique automatiquement les couleurs d'un thème prédéfini"""
        themes = OrganizationTemplate.get_predefined_themes()
        if theme_name in themes:
            theme_colors = themes[theme_name]
            self.cleaned_data['primary_color'] = theme_colors['primary']
            self.cleaned_data['secondary_color'] = theme_colors['secondary']
            self.cleaned_data['accent_color'] = theme_colors['accent']
            self.cleaned_data['background_color'] = theme_colors['background']
            self.cleaned_data['text_color'] = theme_colors['text']

class CustomSectionForm(forms.Form):
    """Formulaire pour ajouter des sections personnalisées"""
    title = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4}))
    section_type = forms.ChoiceField(
        choices=[
            ('text', 'Texte simple'),
            ('html', 'HTML'),
            ('image', 'Image'),
            ('video', 'Vidéo'),
            ('gallery', 'Galerie'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    order = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=False
    ) 

