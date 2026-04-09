"""
Formulaires pour la configuration du streaming des compétitions.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.competitions.models import Competition


class CompetitionStreamingForm(forms.ModelForm):
    """
    Formulaire de configuration du streaming pour une compétition.
    Permet aux organisateurs de configurer l'intégration de streaming externe.
    """

    class Meta:
        model = Competition
        fields = [
            'stream_enabled',
            'stream_platform',
            'stream_url',
            'stream_chat_enabled',
            'is_live',
            'stream_replay_url',
            'stream_replay_available',
        ]
        widgets = {
            'stream_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-toggle': 'streaming-options',
                'id': 'stream_enabled'
            }),
            'stream_platform': forms.Select(attrs={
                'class': 'form-select',
                'id': 'stream_platform'
            }),
            'stream_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=... ou https://twitch.tv/...',
                'id': 'stream_url'
            }),
            'stream_chat_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'stream_chat_enabled'
            }),
            'is_live': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-live-toggle': 'true',
                'id': 'is_live'
            }),
            'stream_replay_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL de la vidéo enregistrée',
                'id': 'stream_replay_url'
            }),
            'stream_replay_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'stream_replay_available'
            }),
        }

    def clean_stream_url(self):
        """Valide que l'URL correspond à la plateforme sélectionnée."""
        url = self.cleaned_data.get('stream_url')
        platform = self.cleaned_data.get('stream_platform')

        if not url:
            return url

        # Validation par plateforme
        platform_domains = {
            'youtube': ['youtube.com', 'youtu.be'],
            'twitch': ['twitch.tv'],
            'vimeo': ['vimeo.com'],
            'facebook': ['facebook.com'],
            'dailymotion': ['dailymotion.com'],
        }

        if platform and platform != 'custom':
            valid_domains = platform_domains.get(platform, [])
            if not any(domain in url.lower() for domain in valid_domains):
                raise forms.ValidationError(
                    _("L'URL ne correspond pas à la plateforme "
                      "sélectionnée (%(platform)s)"),
                    params={'platform': platform}
                )

        return url

    def clean(self):
        """Validation globale du formulaire."""
        cleaned_data = super().clean()
        stream_enabled = cleaned_data.get('stream_enabled')
        stream_url = cleaned_data.get('stream_url')
        stream_platform = cleaned_data.get('stream_platform')

        if stream_enabled:
            if not stream_url:
                self.add_error(
                    'stream_url',
                    _("L'URL du stream est requise si le streaming est activé")
                )
            if not stream_platform:
                self.add_error(
                    'stream_platform',
                    _("Veuillez sélectionner une plateforme")
                )

        return cleaned_data


class StreamStatusForm(forms.Form):
    """
    Formulaire simple pour démarrer/arrêter le stream.
    """
    action = forms.ChoiceField(
        choices=[
            ('start', _('Démarrer le stream')),
            ('stop', _('Arrêter le stream')),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
