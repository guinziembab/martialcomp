from django.db import models
from django.core.validators import URLValidator
from . import Organization
import json

class OrganizationTemplate(models.Model):
    """Template paramétrable pour les sites d'organisation"""
    
    THEME_CHOICES = [
        ('modern', 'Moderne'),
        ('classic', 'Classique'),
        ('sport', 'Sport'),
        ('elegant', 'Ã‰légant'),
        ('minimal', 'Minimaliste'),
        ('corporate', 'Corporate'),
    ]
    
    LAYOUT_CHOICES = [
        ('standard', 'Standard'),
        ('centered', 'Centré'),
        ('sidebar', 'Avec sidebar'),
        ('fullwidth', 'Pleine largeur'),
        ('grid', 'Grille'),
    ]
    
    TEMPLATE_CHOICES = [
        ('default', 'Template par défaut'),
        ('landing', 'Landing page'),
        ('portfolio', 'Portfolio'),
        ('blog', 'Blog'),
        ('ecommerce', 'E-commerce'),
        ('event', 'Ã‰vénement'),
        ('team', 'Ã‰quipe'),
        ('services', 'Services'),
    ]
    
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='template')
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='modern')
    layout = models.CharField(max_length=20, choices=LAYOUT_CHOICES, default='standard')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='default')
    
    # Couleurs du thème
    primary_color = models.CharField(max_length=7, default='#007bff', help_text='Couleur principale (format hex)')
    secondary_color = models.CharField(max_length=7, default='#6c757d', help_text='Couleur secondaire (format hex)')
    accent_color = models.CharField(max_length=7, default='#28a745', help_text='Couleur d\'accent (format hex)')
    background_color = models.CharField(max_length=7, default='#ffffff', help_text='Couleur de fond (format hex)')
    text_color = models.CharField(max_length=7, default='#333333', help_text='Couleur du texte (format hex)')
    
    # Zones de contenu
    hero_title = models.CharField(max_length=200, blank=True, help_text='Titre principal de la page d\'accueil')
    hero_subtitle = models.TextField(blank=True, help_text='Sous-titre de la page d\'accueil')
    about_title = models.CharField(max_length=200, default='Ã€ propos', help_text='Titre de la section Ã€ propos')
    about_content = models.TextField(blank=True, help_text='Contenu de la section Ã€ propos')
    
    # Sections personnalisables
    custom_sections = models.JSONField(default=dict, blank=True, help_text='Sections personnalisées (JSON)')
    
    # Widgets spécialisés
    widgets = models.JSONField(default=dict, blank=True, help_text='Widgets spécialisés (JSON)')
    
    # Liens et vidéos
    website_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Site web officiel')
    facebook_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Page Facebook')
    instagram_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Compte Instagram')
    youtube_url = models.URLField(blank=True, validators=[URLValidator()], help_text='ChaÃ®ne YouTube')
    linkedin_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Profil LinkedIn')
    twitter_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Compte Twitter')
    
    # Vidéos
    video_1_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Vidéo 1 (YouTube/Vimeo)')
    video_1_title = models.CharField(max_length=200, blank=True, help_text='Titre de la vidéo 1')
    video_1_description = models.TextField(blank=True, help_text='Description de la vidéo 1')
    video_2_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Vidéo 2 (YouTube/Vimeo)')
    video_2_title = models.CharField(max_length=200, blank=True, help_text='Titre de la vidéo 2')
    video_2_description = models.TextField(blank=True, help_text='Description de la vidéo 2')
    video_3_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Vidéo 3 (YouTube/Vimeo)')
    video_3_title = models.CharField(max_length=200, blank=True, help_text='Titre de la vidéo 3')
    video_3_description = models.TextField(blank=True, help_text='Description de la vidéo 3')
    
    # Images avec galerie avancée
    image_1_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Image 1 (URL externe)')
    image_1_alt = models.CharField(max_length=200, blank=True, help_text='Texte alternatif image 1')
    image_1_caption = models.CharField(max_length=200, blank=True, help_text='Légende image 1')
    image_2_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Image 2 (URL externe)')
    image_2_alt = models.CharField(max_length=200, blank=True, help_text='Texte alternatif image 2')
    image_2_caption = models.CharField(max_length=200, blank=True, help_text='Légende image 2')
    image_3_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Image 3 (URL externe)')
    image_3_alt = models.CharField(max_length=200, blank=True, help_text='Texte alternatif image 3')
    image_3_caption = models.CharField(max_length=200, blank=True, help_text='Légende image 3')
    image_4_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Image 4 (URL externe)')
    image_4_alt = models.CharField(max_length=200, blank=True, help_text='Texte alternatif image 4')
    image_4_caption = models.CharField(max_length=200, blank=True, help_text='Légende image 4')
    image_5_url = models.URLField(blank=True, validators=[URLValidator()], help_text='Image 5 (URL externe)')
    image_5_alt = models.CharField(max_length=200, blank=True, help_text='Texte alternatif image 5')
    image_5_caption = models.CharField(max_length=200, blank=True, help_text='Légende image 5')
    
    # Paramètres d'affichage
    show_social_links = models.BooleanField(default=True, help_text='Afficher les liens sociaux')
    show_videos = models.BooleanField(default=True, help_text='Afficher la section vidéos')
    show_gallery = models.BooleanField(default=True, help_text='Afficher la galerie d\'images')
    show_lightbox = models.BooleanField(default=True, help_text='Activer la lightbox pour les images')
    show_hero_button = models.BooleanField(default=True, help_text='Afficher le bouton dans la section hero')
    hero_button_text = models.CharField(max_length=50, default='En savoir plus', help_text='Texte du bouton hero')
    hero_button_url = models.CharField(max_length=200, default='#about', help_text='URL du bouton hero')
    
    # Paramètres avancés
    enable_animations = models.BooleanField(default=True, help_text='Activer les animations CSS')
    enable_parallax = models.BooleanField(default=False, help_text='Activer l\'effet parallax')
    enable_dark_mode = models.BooleanField(default=False, help_text='Activer le mode sombre')
    
    # Options d'export
    enable_export = models.BooleanField(default=True, help_text='Activer l\'export du template')
    export_format = models.CharField(max_length=20, choices=[
        ('html', 'HTML statique'),
        ('pdf', 'PDF'),
        ('zip', 'Archive ZIP'),
    ], default='html', help_text='Format d\'export')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'competitions'
        verbose_name = 'Template d\'organisation'
        verbose_name_plural = 'Templates d\'organisations'
    
    def __str__(self):
        return f"Template de {self.organization.name}"
    
    def get_theme_colors(self):
        """Retourne les couleurs du thème actuel"""
        return {
            'primary': self.primary_color,
            'secondary': self.secondary_color,
            'accent': self.accent_color,
            'background': self.background_color,
            'text': self.text_color,
        }
    
    def get_videos(self):
        """Retourne les vidéos configurées avec descriptions"""
        videos = []
        for i in range(1, 4):
            url = getattr(self, f'video_{i}_url')
            title = getattr(self, f'video_{i}_title')
            description = getattr(self, f'video_{i}_description')
            if url:
                videos.append({
                    'url': url, 
                    'title': title, 
                    'description': description
                })
        return videos
    
    def get_images(self):
        """Retourne les images configurées avec légendes"""
        images = []
        for i in range(1, 6):
            url = getattr(self, f'image_{i}_url')
            alt = getattr(self, f'image_{i}_alt')
            caption = getattr(self, f'image_{i}_caption')
            if url:
                images.append({
                    'url': url, 
                    'alt': alt, 
                    'caption': caption
                })
        return images
    
    def get_social_links(self):
        """Retourne les liens sociaux configurés"""
        links = {}
        social_fields = ['website_url', 'facebook_url', 'instagram_url', 'youtube_url', 'linkedin_url', 'twitter_url']
        for field in social_fields:
            url = getattr(self, field)
            if url:
                links[field.replace('_url', '')] = url
        return links
    
    def get_custom_sections(self):
        """Retourne les sections personnalisées"""
        if isinstance(self.custom_sections, str):
            try:
                return json.loads(self.custom_sections)
            except json.JSONDecodeError:
                return {}
        return self.custom_sections or {}
    
    def get_widgets(self):
        """Retourne les widgets configurés"""
        if isinstance(self.widgets, str):
            try:
                return json.loads(self.widgets)
            except json.JSONDecodeError:
                return {}
        return self.widgets or {}
    
    def add_custom_section(self, title, content, section_type='text', order=0):
        """Ajoute une section personnalisée"""
        sections = self.get_custom_sections()
        section_id = f"section_{len(sections) + 1}"
        sections[section_id] = {
            'title': title,
            'content': content,
            'type': section_type,
            'order': order
        }
        self.custom_sections = sections
        self.save()
    
    def add_widget(self, widget_type, config):
        """Ajoute un widget spécialisé"""
        widgets = self.get_widgets()
        widget_id = f"widget_{len(widgets) + 1}"
        widgets[widget_id] = {
            'type': widget_type,
            'config': config
        }
        self.widgets = widgets
        self.save()
    
    @classmethod
    def get_predefined_themes(cls):
        """Retourne les thèmes prédéfinis avec leurs couleurs"""
        return {
            'modern': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'accent': '#28a745',
                'background': '#ffffff',
                'text': '#333333'
            },
            'classic': {
                'primary': '#343a40',
                'secondary': '#495057',
                'accent': '#dc3545',
                'background': '#f8f9fa',
                'text': '#212529'
            },
            'sport': {
                'primary': '#ff6b35',
                'secondary': '#2c3e50',
                'accent': '#e74c3c',
                'background': '#ecf0f1',
                'text': '#2c3e50'
            },
            'elegant': {
                'primary': '#8e44ad',
                'secondary': '#34495e',
                'accent': '#e67e22',
                'background': '#ffffff',
                'text': '#2c3e50'
            },
            'minimal': {
                'primary': '#000000',
                'secondary': '#666666',
                'accent': '#333333',
                'background': '#ffffff',
                'text': '#000000'
            },
            'corporate': {
                'primary': '#1e3a8a',
                'secondary': '#374151',
                'accent': '#059669',
                'background': '#f9fafb',
                'text': '#111827'
            }
        }
    
    @classmethod
    def get_template_presets(cls):
        """Retourne les presets de templates prédéfinis"""
        return {
            'landing': {
                'sections': ['hero', 'features', 'testimonials', 'cta'],
                'widgets': ['contact_form', 'newsletter'],
                'layout': 'fullwidth'
            },
            'portfolio': {
                'sections': ['hero', 'portfolio', 'about', 'contact'],
                'widgets': ['portfolio_filter', 'lightbox'],
                'layout': 'grid'
            },
            'blog': {
                'sections': ['hero', 'blog_posts', 'sidebar'],
                'widgets': ['search', 'categories', 'recent_posts'],
                'layout': 'sidebar'
            },
            'ecommerce': {
                'sections': ['hero', 'products', 'categories', 'cart'],
                'widgets': ['product_filter', 'shopping_cart'],
                'layout': 'grid'
            },
            'event': {
                'sections': ['hero', 'event_details', 'schedule', 'registration'],
                'widgets': ['countdown', 'registration_form'],
                'layout': 'centered'
            },
            'team': {
                'sections': ['hero', 'team_members', 'about', 'contact'],
                'widgets': ['team_filter', 'contact_form'],
                'layout': 'grid'
            },
            'services': {
                'sections': ['hero', 'services', 'pricing', 'contact'],
                'widgets': ['service_selector', 'quote_calculator'],
                'layout': 'standard'
            }
        }
    
    def export_template(self, format='html'):
        """Exporte le template dans le format spécifié"""
        if format == 'html':
            return self._export_html()
        elif format == 'pdf':
            return self._export_pdf()
        elif format == 'zip':
            return self._export_zip()
        return None
    
    def _export_html(self):
        """Exporte en HTML statique"""
        # Logique d'export HTML
        return f"<html>...</html>"
    
    def _export_pdf(self):
        """Exporte en PDF"""
        # Logique d'export PDF
        return "PDF content"
    
    def _export_zip(self):
        """Exporte en archive ZIP"""
        # Logique d'export ZIP
        return "ZIP archive" 


