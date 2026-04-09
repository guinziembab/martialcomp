from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.competitions.models import Competition, CompetitionCategory, Match

# Importez d'autres modèles selon les besoins de votre application


class ScheduleForm(forms.Form):
    """
    Formulaire de base pour la planification des horaires de compétition.
    """
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(
            is_published=True,
            end_date__gte=timezone.now().date()
        ).exclude(status='cancelled'),
        label=_("Compétition"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        competition = self.initial.get('competition')
        if competition:
            # Date par défaut = date de début de la compétition
            self.fields['date'].initial = competition.start_date


class CompetitionScheduleForm(forms.ModelForm):
    """
    Formulaire pour la planification globale d'une compétition.
    Tous les paramètres sont configurables : tatamis, durées, horaires, etc.
    """
    class Meta:
        from apps.competitions.models.schedule import CompetitionSchedule
        model = CompetitionSchedule
        fields = [
            'start_time', 'end_time',
            'break_start', 'break_end',
            'weigh_in_start', 'weigh_in_end',
            'briefing_time', 'awards_ceremony_time',
            'tatami_count',
            'match_duration', 'break_between_matches',
            'notes'
        ]
        widgets = {
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'break_start': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'weigh_in_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'weigh_in_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'briefing_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'awards_ceremony_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'tatami_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': 1
            }),
            'match_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 60,
                'step': 1
            }),
            'break_between_matches': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 30,
                'step': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_time'].help_text = _("Heure de début de la compétition (ex: 09:00)")
        self.fields['end_time'].help_text = _("Heure de fin de la compétition (ex: 18:00)")
        self.fields['break_start'].help_text = _("Heure de début de la pause déjeuner (optionnel)")
        self.fields['break_end'].help_text = _("Heure de fin de la pause déjeuner (optionnel)")
        self.fields['tatami_count'].help_text = _("Nombre de tatamis disponibles (1-10)")
        self.fields['match_duration'].help_text = _("Durée par défaut d'un match en minutes (ex: 3 pour 3 minutes)")
        self.fields['break_between_matches'].help_text = _("Temps de pause entre deux matchs en minutes (ex: 1)")
        self.fields['weigh_in_start'].help_text = _("Date et heure de début de la pesée (optionnel)")
        self.fields['weigh_in_end'].help_text = _("Date et heure de fin de la pesée (optionnel)")
        self.fields['briefing_time'].help_text = _("Heure du briefing des juges (optionnel)")
        self.fields['awards_ceremony_time'].help_text = _("Heure de la cérémonie de remise des prix (optionnel)")


class CategoryScheduleForm(forms.ModelForm):
    """
    Formulaire pour la planification des horaires par catégorie.
    """
    class Meta:
        from apps.competitions.models.schedule import CategorySchedule
        model = CategorySchedule
        fields = ['category', 'tatami', 'estimated_start_time', 'estimated_end_time', 'priority', 'order']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'tatami': forms.Select(attrs={'class': 'form-select'}),
            'estimated_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'estimated_end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Initialise le formulaire avec support pour l'argument 'schedule'.
        """
        schedule = kwargs.pop('schedule', None)
        super().__init__(*args, **kwargs)

        # Rendre les champs non affichés dans le template optionnels
        self.fields['priority'].required = False
        self.fields['estimated_end_time'].required = False
        self.fields['order'].required = False
        self.fields['tatami'].required = False

        # Si un schedule est fourni, pré-remplir les champs avec ses valeurs
        if schedule:
            if not self.initial:
                self.initial = {}

            if schedule.start_time and not self.initial.get('estimated_start_time'):
                self.initial['estimated_start_time'] = schedule.start_time
            if schedule.end_time and not self.initial.get('estimated_end_time'):
                self.initial['estimated_end_time'] = schedule.end_time

            # Filtrer les catégories par compétition si le schedule a une compétition
            if schedule.competition:
                self.fields['category'].queryset = CompetitionCategory.objects.filter(
                    competition=schedule.competition
                )

            # Filtrer les tatamis par le schedule
            from apps.competitions.models.schedule import TatamiSchedule
            self.fields['tatami'].queryset = TatamiSchedule.objects.filter(
                competition_schedule=schedule
            )

    def clean_priority(self):
        return self.cleaned_data.get('priority') or 'normal'

    def clean_order(self):
        return self.cleaned_data.get('order') or 0


class TatamiScheduleForm(forms.Form):
    """
    Formulaire pour la gestion des plannings par tatami.
    """
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(
            is_published=True,
            end_date__gte=timezone.now().date()
        ).exclude(status='cancelled'),
        label=_("Compétition"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    tatami_number = forms.IntegerField(
        label=_("Numéro de tatami"),
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    date = forms.DateField(
        label=_("Date"),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    end_time = forms.TimeField(
        label=_("Heure de fin"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )


class MatchTimeSlotForm(forms.ModelForm):
    """
    Formulaire pour la gestion des créneaux horaires des matchs.
    """
    class Meta:
        model = Match
        fields = ['date_match', 'start_time', 'end_time']
        widgets = {
            'date_match': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
        }

    category = forms.ModelChoiceField(
        queryset=CompetitionCategory.objects.all(),
        label=_("Catégorie"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    tatami = forms.IntegerField(
        label=_("Tatami"),
        required=True,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class BulkCategoryScheduleForm(forms.Form):
    """
    Formulaire pour la planification en masse des catégories de compétition.
    Synchronisé avec le template bulk_category_scheduling.html.
    """
    categories = forms.ModelMultipleChoiceField(
        queryset=CompetitionCategory.objects.all(),
        label=_("Catégories"),
        widget=forms.CheckboxSelectMultiple()
    )

    tatami = forms.ModelChoiceField(
        queryset=None,  # Défini dynamiquement dans __init__
        label=_("Tatami"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    start_time = forms.TimeField(
        label=_("Heure de début"),
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    duration_per_match = forms.IntegerField(
        label=_("Durée par match (minutes)"),
        min_value=1,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 60})
    )

    interval_minutes = forms.IntegerField(
        label=_("Intervalle entre catégories (minutes)"),
        min_value=0,
        initial=15,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )

    break_between_categories = forms.IntegerField(
        label=_("Pause entre catégories (minutes)"),
        min_value=0,
        initial=5,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
    )

    avoid_conflicts = forms.BooleanField(
        label=_("Éviter les conflits de participants/juges"),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, **kwargs):
        schedule = kwargs.pop('schedule', None)
        competition = kwargs.pop('competition', None)

        super().__init__(*args, **kwargs)

        from apps.competitions.models.schedule import TatamiSchedule

        if schedule:
            competition = schedule.competition
            if not self.initial:
                self.initial = {}
            if not self.initial.get('start_time') and schedule.start_time:
                self.initial['start_time'] = schedule.start_time
            if schedule.match_duration:
                self.initial.setdefault('duration_per_match', schedule.match_duration)
            # Filtrer les tatamis par le schedule
            self.fields['tatami'].queryset = TatamiSchedule.objects.filter(
                competition_schedule=schedule
            )
        else:
            self.fields['tatami'].queryset = TatamiSchedule.objects.none()

        if competition:
            self.fields['categories'].queryset = CompetitionCategory.objects.filter(
                competition=competition
            )
