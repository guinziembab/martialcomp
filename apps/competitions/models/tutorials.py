"""
Modeles pour le Centre de Tutoriels MartialComp
"""
import json
import re
from urllib.parse import urlparse, parse_qs

from django.db import models
from django.utils.translation import gettext_lazy as _


class TutorialSection(models.Model):
    """Section regroupant plusieurs tutoriels (ex: Inscription, Gestion Club, etc.)"""
    title = models.CharField(_("Titre"), max_length=200)
    icon = models.CharField(_("Icone FontAwesome"), max_length=50, default="fa-book",
                            help_text=_("Classe FontAwesome, ex: fa-user-plus"))
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)

    class Meta:
        ordering = ['order']
        verbose_name = _("Section de tutoriel")
        verbose_name_plural = _("Sections de tutoriels")

    def __str__(self):
        return self.title


class Tutorial(models.Model):
    """Un tutoriel avec etapes, audience cible, et lien video optionnel"""
    AUDIENCE_CHOICES = [
        ('all', _('Tous')),
        ('admin', _('Administrateur')),
        ('club', _('Club')),
        ('federation', _('Federation')),
        ('practitioner', _('Pratiquant')),
        ('judge', _('Juge')),
        ('coach', _('Entraineur')),
    ]
    FORMAT_CHOICES = [
        ('video', _('Video')),
        ('guide', _('Guide pas a pas')),
        ('interactive', _('Interactif')),
    ]

    section = models.ForeignKey(
        TutorialSection,
        on_delete=models.CASCADE,
        related_name='tutorials',
        verbose_name=_("Section")
    )
    number = models.PositiveIntegerField(_("Numero"))
    title = models.CharField(_("Titre"), max_length=300)
    audience = models.CharField(_("Public cible"), max_length=20, choices=AUDIENCE_CHOICES, default='all')
    format = models.CharField(_("Format"), max_length=20, choices=FORMAT_CHOICES, default='guide')
    duration = models.CharField(_("Duree"), max_length=20, blank=True, default="3 min")
    steps = models.TextField(_("Etapes (JSON)"), blank=True,
                             help_text=_('Liste JSON: ["Etape 1", "Etape 2", ...]'))
    tip = models.TextField(_("Astuce"), blank=True)
    youtube_url = models.URLField(_("Lien YouTube"), blank=True,
                                  help_text=_("URL YouTube (ex: https://youtube.com/watch?v=...)"))
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    is_active = models.BooleanField(_("Actif"), default=True)

    class Meta:
        ordering = ['section__order', 'order', 'number']
        verbose_name = _("Tutoriel")
        verbose_name_plural = _("Tutoriels")
        unique_together = [('section', 'number')]

    def __str__(self):
        return f"{self.section.title} - {self.number}. {self.title}"

    def get_steps_list(self):
        """Parse la chaine JSON steps en liste Python"""
        try:
            return json.loads(self.steps) if self.steps else []
        except (json.JSONDecodeError, TypeError):
            return []

    def get_youtube_embed_url(self):
        """Convertit une URL YouTube en URL d'embed"""
        if not self.youtube_url:
            return ''
        url = self.youtube_url.strip()
        # Format: youtu.be/VIDEO_ID
        match = re.match(r'https?://youtu\.be/([a-zA-Z0-9_-]+)', url)
        if match:
            return f'https://www.youtube.com/embed/{match.group(1)}'
        # Format: youtube.com/watch?v=VIDEO_ID
        parsed = urlparse(url)
        if 'youtube.com' in parsed.netloc:
            qs = parse_qs(parsed.query)
            video_id = qs.get('v', [None])[0]
            if video_id:
                return f'https://www.youtube.com/embed/{video_id}'
        return ''

    @property
    def has_video(self):
        return bool(self.youtube_url)
