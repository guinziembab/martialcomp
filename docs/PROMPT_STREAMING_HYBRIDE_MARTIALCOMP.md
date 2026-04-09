# 🎬 PROMPT : Implémentation Streaming Hybride MartialComp

## 📋 Contexte du Projet

**Application** : MartialComp - Plateforme SaaS de gestion d'arts martiaux  
**Stack technique** : Django 5.1, PostgreSQL 15, Redis, WebSocket, Celery  
**Fonctionnalité** : Intégration de streaming externe (YouTube, Twitch, Vimeo, Facebook Live) synchronisé avec les scores en temps réel  

---

## 🎯 Objectif

Implémenter une solution de streaming hybride permettant aux organisateurs de compétitions de :
1. Diffuser leurs événements via des plateformes externes (YouTube, Twitch, etc.)
2. Intégrer automatiquement le flux vidéo dans la page de compétition MartialComp
3. Synchroniser l'affichage du stream avec les scores en temps réel
4. Offrir une expérience unifiée aux spectateurs sans quitter MartialComp

---

## 🏗️ Architecture de la Solution

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ARCHITECTURE STREAMING HYBRIDE                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ORGANISATEUR                           SPECTATEUR                             │
│   ────────────                           ──────────                              │
│                                                                                 │
│   ┌─────────┐      ┌─────────────┐      ┌─────────────────────────────────┐    │
│   │ Caméra  │─────►│   OBS /     │─────►│     YouTube / Twitch / Vimeo   │    │
│   │         │      │   Mobile    │      │         (Stream Host)           │    │
│   └─────────┘      └─────────────┘      └───────────────┬─────────────────┘    │
│                                                         │                       │
│                                                         │ iframe embed          │
│                                                         ▼                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                         MARTIALCOMP                                     │  │
│   │  ┌───────────────────────────────┬─────────────────────────────────┐   │  │
│   │  │                               │                                 │   │  │
│   │  │     📺 VIDEO STREAM           │      📊 SCORES TEMPS RÉEL      │   │  │
│   │  │     (iframe externe)          │      (WebSocket natif)         │   │  │
│   │  │                               │                                 │   │  │
│   │  │  ┌─────────────────────────┐  │   Combat #12 - Finale          │   │  │
│   │  │  │                         │  │   ───────────────────          │   │  │
│   │  │  │    YOUTUBE PLAYER       │  │   🔴 NGUYEN Van    3 pts       │   │  │
│   │  │  │    ou TWITCH PLAYER     │  │   🔵 MARTIN Paul   2 pts       │   │  │
│   │  │  │                         │  │                                 │   │  │
│   │  │  └─────────────────────────┘  │   ⏱️ Temps: 01:45 / 03:00      │   │  │
│   │  │                               │   🏆 Catégorie: -70kg Seniors  │   │  │
│   │  └───────────────────────────────┴─────────────────────────────────┘   │  │
│   │                                                                         │  │
│   │  ┌─────────────────────────────────────────────────────────────────┐   │  │
│   │  │ 📋 BRACKET │ 📊 RÉSULTATS │ 👥 PARTICIPANTS │ 🏆 PODIUM │ 💬 CHAT │   │  │
│   │  └─────────────────────────────────────────────────────────────────┘   │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Fichiers à Créer/Modifier

### 1. Modèle de Données

**Fichier** : `competitions/models/competition.py`

```python
# Ajouter les champs suivants au modèle Competition existant

class StreamPlatform(models.TextChoices):
    YOUTUBE = 'youtube', 'YouTube'
    TWITCH = 'twitch', 'Twitch'
    FACEBOOK = 'facebook', 'Facebook Live'
    VIMEO = 'vimeo', 'Vimeo'
    DAILYMOTION = 'dailymotion', 'Dailymotion'
    CUSTOM = 'custom', 'URL personnalisée'


class Competition(models.Model):
    # ... champs existants ...
    
    # ===== NOUVEAUX CHAMPS STREAMING =====
    
    # Configuration du stream
    stream_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Streaming activé"),
        help_text=_("Activer l'intégration du streaming pour cette compétition")
    )
    
    stream_platform = models.CharField(
        max_length=20,
        choices=StreamPlatform.choices,
        null=True,
        blank=True,
        verbose_name=_("Plateforme de streaming"),
        help_text=_("Sélectionner la plateforme utilisée pour le streaming")
    )
    
    stream_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL du stream"),
        help_text=_("URL complète du stream (ex: https://youtube.com/watch?v=xxxxx)")
    )
    
    stream_embed_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL d'intégration"),
        help_text=_("URL d'embed générée automatiquement")
    )
    
    stream_chat_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Chat du stream activé"),
        help_text=_("Afficher le chat de la plateforme à côté du stream")
    )
    
    stream_chat_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL du chat"),
        help_text=_("URL d'intégration du chat (optionnel)")
    )
    
    # État du stream
    is_live = models.BooleanField(
        default=False,
        verbose_name=_("En direct"),
        help_text=_("Indique si le stream est actuellement en direct")
    )
    
    stream_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Début du stream")
    )
    
    stream_ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Fin du stream")
    )
    
    stream_viewer_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Nombre de spectateurs")
    )
    
    # Archive/Replay
    stream_replay_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name=_("URL du replay"),
        help_text=_("URL de la vidéo enregistrée après la fin du stream")
    )
    
    stream_replay_available = models.BooleanField(
        default=False,
        verbose_name=_("Replay disponible")
    )
    
    # ===== MÉTHODES =====
    
    def save(self, *args, **kwargs):
        # Générer automatiquement l'URL d'embed
        if self.stream_url and not self.stream_embed_url:
            self.stream_embed_url = self.generate_embed_url()
        super().save(*args, **kwargs)
    
    def generate_embed_url(self):
        """
        Convertit l'URL du stream en URL d'intégration iframe
        """
        if not self.stream_url:
            return None
        
        url = self.stream_url.strip()
        
        # YouTube
        if 'youtube.com/watch' in url:
            try:
                video_id = url.split('v=')[1].split('&')[0]
                return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
            except IndexError:
                return None
        
        if 'youtu.be/' in url:
            try:
                video_id = url.split('youtu.be/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
            except IndexError:
                return None
        
        if 'youtube.com/live/' in url:
            try:
                video_id = url.split('/live/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
            except IndexError:
                return None
        
        # Twitch
        if 'twitch.tv/' in url:
            try:
                channel = url.split('twitch.tv/')[1].split('/')[0].split('?')[0]
                parent_domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'martialcomp.com'
                return f"https://player.twitch.tv/?channel={channel}&parent={parent_domain}&autoplay=true"
            except IndexError:
                return None
        
        # Vimeo
        if 'vimeo.com/' in url:
            try:
                video_id = url.split('vimeo.com/')[1].split('/')[0].split('?')[0]
                return f"https://player.vimeo.com/video/{video_id}?autoplay=1"
            except IndexError:
                return None
        
        # Facebook Live
        if 'facebook.com/' in url and '/videos/' in url:
            encoded_url = quote(url, safe='')
            return f"https://www.facebook.com/plugins/video.php?href={encoded_url}&autoplay=true"
        
        # Dailymotion
        if 'dailymotion.com/video/' in url:
            try:
                video_id = url.split('/video/')[1].split('_')[0]
                return f"https://www.dailymotion.com/embed/video/{video_id}?autoplay=1"
            except IndexError:
                return None
        
        # URL personnalisée - retourner telle quelle
        return url
    
    def generate_chat_url(self):
        """
        Génère l'URL du chat pour la plateforme
        """
        if not self.stream_url or not self.stream_chat_enabled:
            return None
        
        # YouTube Live Chat
        if 'youtube.com' in self.stream_url or 'youtu.be' in self.stream_url:
            # YouTube n'a pas d'embed chat simple, utiliser URL standard
            return None
        
        # Twitch Chat
        if 'twitch.tv/' in self.stream_url:
            try:
                channel = self.stream_url.split('twitch.tv/')[1].split('/')[0]
                parent_domain = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'martialcomp.com'
                return f"https://www.twitch.tv/embed/{channel}/chat?parent={parent_domain}&darkpopout"
            except IndexError:
                return None
        
        return None
    
    def start_stream(self):
        """Marquer le stream comme démarré"""
        self.is_live = True
        self.stream_started_at = timezone.now()
        self.stream_ended_at = None
        self.save(update_fields=['is_live', 'stream_started_at', 'stream_ended_at'])
    
    def end_stream(self):
        """Marquer le stream comme terminé"""
        self.is_live = False
        self.stream_ended_at = timezone.now()
        self.save(update_fields=['is_live', 'stream_ended_at'])
    
    def update_viewer_count(self, count):
        """Mettre à jour le nombre de spectateurs"""
        self.stream_viewer_count = count
        self.save(update_fields=['stream_viewer_count'])
    
    @property
    def stream_duration(self):
        """Durée du stream en cours ou terminé"""
        if not self.stream_started_at:
            return None
        end_time = self.stream_ended_at or timezone.now()
        return end_time - self.stream_started_at
    
    class Meta:
        # ... meta existant ...
        pass
```

---

### 2. Formulaire Admin/Organisateur

**Fichier** : `competitions/forms/streaming.py`

```python
from django import forms
from django.utils.translation import gettext_lazy as _
from competitions.models import Competition


class CompetitionStreamingForm(forms.ModelForm):
    """
    Formulaire de configuration du streaming pour une compétition
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
                'data-toggle': 'streaming-options'
            }),
            'stream_platform': forms.Select(attrs={
                'class': 'form-select'
            }),
            'stream_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/watch?v=... ou https://twitch.tv/...'
            }),
            'stream_chat_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_live': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'data-live-toggle': 'true'
            }),
            'stream_replay_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'URL de la vidéo enregistrée'
            }),
            'stream_replay_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_stream_url(self):
        url = self.cleaned_data.get('stream_url')
        platform = self.cleaned_data.get('stream_platform')
        
        if not url:
            return url
        
        # Validation basique par plateforme
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
                    _("L'URL ne correspond pas à la plateforme sélectionnée (%(platform)s)"),
                    params={'platform': platform}
                )
        
        return url
    
    def clean(self):
        cleaned_data = super().clean()
        stream_enabled = cleaned_data.get('stream_enabled')
        stream_url = cleaned_data.get('stream_url')
        stream_platform = cleaned_data.get('stream_platform')
        
        if stream_enabled:
            if not stream_url:
                self.add_error('stream_url', _("L'URL du stream est requise si le streaming est activé"))
            if not stream_platform:
                self.add_error('stream_platform', _("Veuillez sélectionner une plateforme"))
        
        return cleaned_data
```

---

### 3. Vue API pour le Streaming

**Fichier** : `competitions/views/streaming.py`

```python
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.utils import timezone

from competitions.models import Competition
from competitions.forms import CompetitionStreamingForm


class CompetitionStreamingAPIView(View):
    """
    API pour gérer le streaming d'une compétition
    """
    
    @method_decorator(login_required)
    def get(self, request, competition_id):
        """Récupérer les informations de streaming"""
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Vérifier les permissions
        if not request.user.can_view_competition(competition):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        return JsonResponse({
            'stream_enabled': competition.stream_enabled,
            'stream_platform': competition.stream_platform,
            'stream_url': competition.stream_url,
            'stream_embed_url': competition.stream_embed_url,
            'stream_chat_url': competition.generate_chat_url(),
            'stream_chat_enabled': competition.stream_chat_enabled,
            'is_live': competition.is_live,
            'stream_started_at': competition.stream_started_at.isoformat() if competition.stream_started_at else None,
            'stream_viewer_count': competition.stream_viewer_count,
            'stream_replay_url': competition.stream_replay_url,
            'stream_replay_available': competition.stream_replay_available,
        })
    
    @method_decorator(login_required)
    def post(self, request, competition_id):
        """Mettre à jour la configuration du streaming"""
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Vérifier les permissions (organisateur uniquement)
        if not request.user.can_manage_competition(competition):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        form = CompetitionStreamingForm(request.POST, instance=competition)
        
        if form.is_valid():
            competition = form.save()
            return JsonResponse({
                'success': True,
                'stream_embed_url': competition.stream_embed_url,
                'message': 'Configuration du streaming mise à jour'
            })
        
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


class StreamStatusAPIView(View):
    """
    API pour gérer le statut live du stream
    """
    
    @method_decorator(login_required)
    def post(self, request, competition_id, action):
        """Démarrer ou arrêter le stream"""
        competition = get_object_or_404(Competition, id=competition_id)
        
        if not request.user.can_manage_competition(competition):
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        if action == 'start':
            competition.start_stream()
            return JsonResponse({
                'success': True,
                'is_live': True,
                'started_at': competition.stream_started_at.isoformat()
            })
        
        elif action == 'stop':
            competition.end_stream()
            return JsonResponse({
                'success': True,
                'is_live': False,
                'ended_at': competition.stream_ended_at.isoformat()
            })
        
        return JsonResponse({'error': 'Invalid action'}, status=400)


class PublicStreamView(View):
    """
    Vue publique pour les spectateurs
    """
    
    def get(self, request, competition_id):
        """Page de streaming public"""
        competition = get_object_or_404(
            Competition.objects.select_related('organization'),
            id=competition_id,
            stream_enabled=True
        )
        
        # Incrémenter le compteur de vues (optionnel)
        # competition.increment_view_count()
        
        return JsonResponse({
            'competition': {
                'id': competition.id,
                'name': competition.name,
                'organization': competition.organization.name,
                'date': competition.date.isoformat(),
            },
            'streaming': {
                'platform': competition.stream_platform,
                'embed_url': competition.stream_embed_url,
                'chat_url': competition.generate_chat_url() if competition.stream_chat_enabled else None,
                'is_live': competition.is_live,
                'replay_url': competition.stream_replay_url if competition.stream_replay_available else None,
            }
        })
```

---

### 4. URLs

**Fichier** : `competitions/urls.py` (ajouter)

```python
from django.urls import path
from competitions.views.streaming import (
    CompetitionStreamingAPIView,
    StreamStatusAPIView,
    PublicStreamView,
)

urlpatterns = [
    # ... URLs existantes ...
    
    # Streaming APIs
    path(
        'api/competitions/<int:competition_id>/streaming/',
        CompetitionStreamingAPIView.as_view(),
        name='competition_streaming_api'
    ),
    path(
        'api/competitions/<int:competition_id>/streaming/<str:action>/',
        StreamStatusAPIView.as_view(),
        name='stream_status_api'
    ),
    path(
        'api/competitions/<int:competition_id>/stream/public/',
        PublicStreamView.as_view(),
        name='public_stream_api'
    ),
]
```

---

### 5. Template Page Live

**Fichier** : `templates/competitions/live.html`

```html
{% extends "base.html" %}
{% load i18n static %}

{% block title %}{{ competition.name }} - Live Stream{% endblock %}

{% block extra_css %}
<style>
    .live-container {
        background: #0a0a0a;
        min-height: 100vh;
        padding: 20px;
    }
    
    .live-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #333;
    }
    
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: #c41e3a;
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    .live-badge .pulse {
        width: 10px;
        height: 10px;
        background: white;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.8); }
    }
    
    .stream-wrapper {
        background: #141414;
        border-radius: 12px;
        overflow: hidden;
        position: relative;
    }
    
    .video-container {
        position: relative;
        padding-bottom: 56.25%; /* 16:9 */
        height: 0;
        overflow: hidden;
    }
    
    .video-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: none;
    }
    
    .scores-panel {
        background: #141414;
        border-radius: 12px;
        padding: 20px;
        height: 100%;
    }
    
    .current-combat {
        background: #1a1a1a;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 4px solid #d4af37;
    }
    
    .combat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    
    .combat-number {
        font-size: 0.875rem;
        color: #999;
    }
    
    .combat-category {
        font-size: 0.75rem;
        background: #333;
        padding: 4px 10px;
        border-radius: 12px;
        color: #d4af37;
    }
    
    .fighter {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    
    .fighter.red {
        background: rgba(196, 30, 58, 0.2);
        border: 1px solid rgba(196, 30, 58, 0.5);
    }
    
    .fighter.blue {
        background: rgba(52, 152, 219, 0.2);
        border: 1px solid rgba(52, 152, 219, 0.5);
    }
    
    .fighter-info {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .fighter-color {
        width: 12px;
        height: 12px;
        border-radius: 50%;
    }
    
    .fighter.red .fighter-color { background: #c41e3a; }
    .fighter.blue .fighter-color { background: #3498db; }
    
    .fighter-name {
        font-weight: 600;
        color: #fff;
    }
    
    .fighter-club {
        font-size: 0.75rem;
        color: #999;
    }
    
    .fighter-score {
        font-size: 2rem;
        font-weight: 700;
        color: #fff;
    }
    
    .combat-timer {
        text-align: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.5rem;
        font-weight: 700;
        color: #d4af37;
        padding: 15px;
        background: #1a1a1a;
        border-radius: 8px;
    }
    
    .upcoming-combats {
        margin-top: 20px;
    }
    
    .upcoming-combats h4 {
        font-size: 0.875rem;
        color: #999;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .upcoming-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        background: #1a1a1a;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 0.9rem;
    }
    
    .upcoming-fighters {
        color: #fff;
    }
    
    .upcoming-category {
        font-size: 0.75rem;
        color: #999;
    }
    
    .viewers-count {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #999;
        font-size: 0.875rem;
    }
    
    .viewers-count i {
        color: #c41e3a;
    }
    
    .offline-message {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 400px;
        background: #141414;
        border-radius: 12px;
        text-align: center;
    }
    
    .offline-message i {
        font-size: 4rem;
        color: #333;
        margin-bottom: 20px;
    }
    
    .offline-message h3 {
        color: #999;
        margin-bottom: 10px;
    }
    
    .offline-message p {
        color: #666;
    }
    
    .chat-panel {
        background: #141414;
        border-radius: 12px;
        overflow: hidden;
        height: 400px;
        margin-top: 20px;
    }
    
    .chat-panel iframe {
        width: 100%;
        height: 100%;
        border: none;
    }
</style>
{% endblock %}

{% block content %}
<div class="live-container">
    <div class="container-fluid">
        <!-- Header -->
        <div class="live-header">
            <div>
                <h1 class="text-white mb-1">{{ competition.name }}</h1>
                <p class="text-muted mb-0">{{ competition.organization.name }} • {{ competition.date|date:"d F Y" }}</p>
            </div>
            <div class="d-flex align-items-center gap-3">
                {% if competition.is_live %}
                <div class="live-badge">
                    <span class="pulse"></span>
                    {% trans "EN DIRECT" %}
                </div>
                {% endif %}
                <div class="viewers-count">
                    <i class="fas fa-eye"></i>
                    <span id="viewer-count">{{ competition.stream_viewer_count }}</span> {% trans "spectateurs" %}
                </div>
            </div>
        </div>
        
        <div class="row">
            <!-- Video Stream -->
            <div class="col-lg-8">
                <div class="stream-wrapper">
                    {% if competition.is_live and competition.stream_embed_url %}
                    <div class="video-container">
                        <iframe 
                            id="stream-player"
                            src="{{ competition.stream_embed_url }}"
                            allowfullscreen
                            allow="autoplay; encrypted-media; picture-in-picture"
                            loading="lazy">
                        </iframe>
                    </div>
                    {% elif competition.stream_replay_available and competition.stream_replay_url %}
                    <div class="video-container">
                        <iframe 
                            src="{{ competition.stream_replay_url }}"
                            allowfullscreen
                            allow="encrypted-media; picture-in-picture"
                            loading="lazy">
                        </iframe>
                    </div>
                    <div class="p-3 bg-dark text-center">
                        <span class="text-muted">
                            <i class="fas fa-video"></i> {% trans "Replay de la compétition" %}
                        </span>
                    </div>
                    {% else %}
                    <div class="offline-message">
                        <i class="fas fa-satellite-dish"></i>
                        <h3>{% trans "Stream non disponible" %}</h3>
                        <p>{% trans "Le direct n'a pas encore commencé ou est terminé." %}</p>
                        {% if competition.date > now %}
                        <p class="text-warning">
                            <i class="fas fa-calendar"></i>
                            {% trans "Rendez-vous le" %} {{ competition.date|date:"d F Y" }}
                        </p>
                        {% endif %}
                    </div>
                    {% endif %}
                </div>
                
                {% if competition.stream_chat_enabled and competition.is_live %}
                <div class="chat-panel">
                    <iframe 
                        src="{{ competition.generate_chat_url }}"
                        loading="lazy">
                    </iframe>
                </div>
                {% endif %}
            </div>
            
            <!-- Scores Panel -->
            <div class="col-lg-4">
                <div class="scores-panel">
                    <h3 class="text-white mb-3">
                        <i class="fas fa-fist-raised text-warning me-2"></i>
                        {% trans "Combat en cours" %}
                    </h3>
                    
                    <div class="current-combat" id="current-combat">
                        <div class="combat-header">
                            <span class="combat-number">#<span id="combat-number">--</span></span>
                            <span class="combat-category" id="combat-category">--</span>
                        </div>
                        
                        <div class="fighter red">
                            <div class="fighter-info">
                                <span class="fighter-color"></span>
                                <div>
                                    <div class="fighter-name" id="red-name">--</div>
                                    <div class="fighter-club" id="red-club">--</div>
                                </div>
                            </div>
                            <div class="fighter-score" id="red-score">0</div>
                        </div>
                        
                        <div class="fighter blue">
                            <div class="fighter-info">
                                <span class="fighter-color"></span>
                                <div>
                                    <div class="fighter-name" id="blue-name">--</div>
                                    <div class="fighter-club" id="blue-club">--</div>
                                </div>
                            </div>
                            <div class="fighter-score" id="blue-score">0</div>
                        </div>
                        
                        <div class="combat-timer" id="combat-timer">
                            00:00
                        </div>
                    </div>
                    
                    <div class="upcoming-combats">
                        <h4>
                            <i class="fas fa-list me-2"></i>
                            {% trans "Prochains combats" %}
                        </h4>
                        <div id="upcoming-list">
                            <!-- Populated via WebSocket -->
                            <div class="upcoming-item">
                                <div>
                                    <div class="upcoming-fighters">{% trans "Chargement..." %}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Links -->
                    <div class="mt-4 pt-3 border-top border-secondary">
                        <a href="{% url 'competition_bracket' competition.id %}" class="btn btn-outline-warning btn-sm w-100 mb-2">
                            <i class="fas fa-sitemap me-2"></i> {% trans "Voir le tableau" %}
                        </a>
                        <a href="{% url 'competition_results' competition.id %}" class="btn btn-outline-secondary btn-sm w-100">
                            <i class="fas fa-trophy me-2"></i> {% trans "Résultats" %}
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // WebSocket connection for real-time scores
    const competitionId = {{ competition.id }};
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/competition/${competitionId}/live/`;
    
    let socket = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    function connectWebSocket() {
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log('WebSocket connected');
            reconnectAttempts = 0;
        };
        
        socket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            handleWebSocketMessage(data);
        };
        
        socket.onclose = function(e) {
            console.log('WebSocket closed');
            if (reconnectAttempts < maxReconnectAttempts) {
                reconnectAttempts++;
                setTimeout(connectWebSocket, 3000);
            }
        };
        
        socket.onerror = function(e) {
            console.error('WebSocket error:', e);
        };
    }
    
    function handleWebSocketMessage(data) {
        switch(data.type) {
            case 'combat_update':
                updateCurrentCombat(data.combat);
                break;
            case 'score_update':
                updateScores(data.scores);
                break;
            case 'timer_update':
                updateTimer(data.time);
                break;
            case 'upcoming_update':
                updateUpcomingCombats(data.upcoming);
                break;
            case 'viewer_count':
                document.getElementById('viewer-count').textContent = data.count;
                break;
        }
    }
    
    function updateCurrentCombat(combat) {
        document.getElementById('combat-number').textContent = combat.number;
        document.getElementById('combat-category').textContent = combat.category;
        document.getElementById('red-name').textContent = combat.red.name;
        document.getElementById('red-club').textContent = combat.red.club;
        document.getElementById('blue-name').textContent = combat.blue.name;
        document.getElementById('blue-club').textContent = combat.blue.club;
        document.getElementById('red-score').textContent = combat.red.score;
        document.getElementById('blue-score').textContent = combat.blue.score;
    }
    
    function updateScores(scores) {
        document.getElementById('red-score').textContent = scores.red;
        document.getElementById('blue-score').textContent = scores.blue;
    }
    
    function updateTimer(time) {
        const minutes = Math.floor(time / 60).toString().padStart(2, '0');
        const seconds = (time % 60).toString().padStart(2, '0');
        document.getElementById('combat-timer').textContent = `${minutes}:${seconds}`;
    }
    
    function updateUpcomingCombats(upcoming) {
        const list = document.getElementById('upcoming-list');
        list.innerHTML = upcoming.map(combat => `
            <div class="upcoming-item">
                <div>
                    <div class="upcoming-fighters">${combat.red} vs ${combat.blue}</div>
                    <div class="upcoming-category">${combat.category}</div>
                </div>
            </div>
        `).join('');
    }
    
    // Initialize WebSocket connection
    {% if competition.is_live %}
    connectWebSocket();
    {% endif %}
</script>
{% endblock %}
```

---

### 6. Migration de Base de Données

**Fichier** : `competitions/migrations/XXXX_add_streaming_fields.py`

```python
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', 'XXXX_previous_migration'),  # Remplacer par la dernière migration
    ]

    operations = [
        migrations.AddField(
            model_name='competition',
            name='stream_enabled',
            field=models.BooleanField(default=False, verbose_name='Streaming activé'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_platform',
            field=models.CharField(
                blank=True,
                choices=[
                    ('youtube', 'YouTube'),
                    ('twitch', 'Twitch'),
                    ('facebook', 'Facebook Live'),
                    ('vimeo', 'Vimeo'),
                    ('dailymotion', 'Dailymotion'),
                    ('custom', 'URL personnalisée'),
                ],
                max_length=20,
                null=True,
                verbose_name='Plateforme de streaming',
            ),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='URL du stream'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_embed_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name="URL d'intégration"),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_chat_enabled',
            field=models.BooleanField(default=False, verbose_name='Chat du stream activé'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_chat_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='URL du chat'),
        ),
        migrations.AddField(
            model_name='competition',
            name='is_live',
            field=models.BooleanField(default=False, verbose_name='En direct'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_started_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Début du stream'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_ended_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fin du stream'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_viewer_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Nombre de spectateurs'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_replay_url',
            field=models.URLField(blank=True, max_length=500, null=True, verbose_name='URL du replay'),
        ),
        migrations.AddField(
            model_name='competition',
            name='stream_replay_available',
            field=models.BooleanField(default=False, verbose_name='Replay disponible'),
        ),
    ]
```

---

## 📋 Checklist d'Implémentation

### Phase 1 : Backend (Jour 1-2)

- [ ] Créer la migration avec les nouveaux champs
- [ ] Ajouter les méthodes au modèle Competition
- [ ] Créer le formulaire CompetitionStreamingForm
- [ ] Créer les vues API (GET/POST streaming config)
- [ ] Ajouter les URLs
- [ ] Tester la génération d'URL embed pour chaque plateforme
- [ ] Écrire les tests unitaires

### Phase 2 : Frontend (Jour 3-4)

- [ ] Créer le template `live.html`
- [ ] Intégrer le CSS responsive
- [ ] Connecter le WebSocket pour les scores
- [ ] Tester l'affichage iframe sur mobile
- [ ] Ajouter les traductions i18n

### Phase 3 : Admin/Organisateur (Jour 5)

- [ ] Ajouter les champs au formulaire de compétition
- [ ] Créer l'interface de configuration streaming
- [ ] Ajouter le toggle "Go Live" / "End Stream"
- [ ] Documenter le processus pour les organisateurs

### Phase 4 : Tests & Déploiement (Jour 6-7)

- [ ] Tests avec YouTube Live
- [ ] Tests avec Twitch
- [ ] Tests avec Vimeo
- [ ] Tests responsive (mobile, tablette)
- [ ] Tests de charge WebSocket
- [ ] Déploiement staging
- [ ] Validation utilisateur
- [ ] Déploiement production

---

## 🔧 Configuration Requise

### Settings Django

```python
# settings.py

# Domaines autorisés pour les embeds Twitch
ALLOWED_HOSTS = ['martialcomp.com', 'www.martialcomp.com', 'localhost']

# Content Security Policy pour autoriser les iframes
CSP_FRAME_SRC = [
    "'self'",
    "https://www.youtube.com",
    "https://player.twitch.tv",
    "https://www.twitch.tv",
    "https://player.vimeo.com",
    "https://www.facebook.com",
    "https://www.dailymotion.com",
]
```

---

## 📚 Documentation Utilisateur

### Guide Organisateur : Configuration du Streaming

1. **Préparer le stream sur YouTube/Twitch**
   - Créer un événement live sur la plateforme choisie
   - Configurer OBS ou l'application mobile
   - Obtenir l'URL du stream

2. **Configurer dans MartialComp**
   - Aller dans Compétition > Modifier > Streaming
   - Activer "Streaming activé"
   - Sélectionner la plateforme
   - Coller l'URL du stream
   - Sauvegarder

3. **Démarrer le direct**
   - Lancer le stream sur YouTube/Twitch
   - Activer "En direct" dans MartialComp
   - Les spectateurs verront le stream synchronisé avec les scores

4. **Après la compétition**
   - Désactiver "En direct"
   - Ajouter l'URL du replay si disponible
   - Activer "Replay disponible"

---

## ⚠️ Points d'Attention

1. **Latence** : Les streams externes ont 10-30 secondes de délai. Les scores temps réel seront en avance sur la vidéo.

2. **CORS/CSP** : Configurer correctement les headers pour autoriser les iframes externes.

3. **Mobile** : Tester l'autoplay qui peut être bloqué sur mobile.

4. **Twitch** : Le paramètre `parent` est obligatoire et doit correspondre au domaine.

5. **Quotas API** : YouTube limite les requêtes API. Utiliser le cache Redis.

---

## 🎯 Résultat Attendu

Une page de compétition live qui affiche :
- Le stream vidéo externe (YouTube/Twitch/Vimeo)
- Les scores en temps réel synchronisés via WebSocket
- La liste des prochains combats
- Le chat de la plateforme (optionnel)
- Un design professionnel et responsive

**Effort estimé** : 5-7 jours de développement
