# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.utils import timezone
import csv
import io
import datetime
from dateutil.parser import parse as parse_date

from apps.competitions.models.event import Event
from apps.organizations.models import Organization


class EventImportForm(forms.Form):
    """
    Formulaire pour importer des événements depuis un fichier CSV.
    """
    csv_file = forms.FileField(
        label=_("Fichier CSV"),
        help_text=_("Veuillez télécharger un fichier CSV avec les colonnes suivantes: "
                   "titre, description, type_evenement, date_debut, date_fin, "
                   "heure_debut (optionnel), heure_fin (optionnel), lieu, ville, etc."),
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label=_("Organisation"),
        help_text=_("Tous les événements importés seront associés Ã  cette organisation."),
        required=True
    )
    
    default_event_type = forms.ChoiceField(
        label=_("Type d'événement par défaut"),
        choices=Event.TYPE_CHOICES,
        help_text=_("Type utilisé si non spécifié dans le CSV."),
        initial='other'
    )
    
    default_visibility = forms.ChoiceField(
        label=_("Visibilité par défaut"),
        choices=Event.VISIBILITY_CHOICES,
        help_text=_("Visibilité utilisée si non spécifiée dans le CSV."),
        initial='members'
    )
    
    create_reminders = forms.BooleanField(
        label=_("Créer des rappels automatiques"),
        required=False,
        initial=True,
        help_text=_("Créer automatiquement des rappels 24h avant chaque événement.")
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limiter les organisations accessibles pour les non-superutilisateurs
        if self.user and not self.user.is_superuser:
            from django.db.models import Q
            self.fields['organization'].queryset = Organization.objects.filter(
                members__user=self.user,
                members__is_active=True
            ).distinct()
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        
        if not csv_file:
            return None
        
        # Valider le contenu du CSV
        try:
            csv_file.seek(0)
            reader = csv.reader(io.StringIO(csv_file.read().decode('utf-8-sig')))
            
            # Lire l'en-tÃªte
            header = next(reader, None)
            
            # Vérifier les colonnes minimales requises
            required_columns = ['titre', 'date_debut']
            missing_columns = [col for col in required_columns if col not in header]
            
            if missing_columns:
                raise forms.ValidationError(
                    _("Colonnes requises manquantes: %(columns)s"),
                    params={'columns': ', '.join(missing_columns)}
                )
            
            # Vérifier que les dates peuvent Ãªtre analysées
            rows = []
            line_number = 1
            for row in reader:
                line_number += 1
                if len(row) < 2:  # Au moins titre et date_debut
                    continue
                
                # Créer un dictionnaire avec les valeurs de la ligne
                row_dict = dict(zip(header, row))
                
                # Valider les dates
                try:
                    date_debut = row_dict.get('date_debut', '').strip()
                    if date_debut:
                        parse_date(date_debut)
                    
                    date_fin = row_dict.get('date_fin', '').strip()
                    if date_fin:
                        parse_date(date_fin)
                except ValueError:
                    raise forms.ValidationError(
                        _("Erreur Ã  la ligne %(line)s: format de date invalide"),
                        params={'line': line_number}
                    )
                
                rows.append(row_dict)
            
            # S'assurer qu'il y a au moins un événement Ã  importer
            if not rows:
                raise forms.ValidationError(_("Le fichier CSV ne contient aucun événement valide."))
            
            # Stocker les lignes analysées pour traitement ultérieur
            self.cleaned_data['parsed_rows'] = rows
            
        except Exception as e:
            raise forms.ValidationError(_("Erreur lors de l'analyse du fichier CSV: %(error)s"), 
                                       params={'error': str(e)})
            
        return csv_file
    
    def import_events(self):
        """
        Importe les événements du fichier CSV validé.
        Retourne un tuple (imported_count, errors).
        """
        if not hasattr(self, 'cleaned_data') or 'parsed_rows' not in self.cleaned_data:
            return 0, ["Données CSV invalides"]
        
        organization = self.cleaned_data['organization']
        default_event_type = self.cleaned_data['default_event_type']
        default_visibility = self.cleaned_data['default_visibility']
        create_reminders = self.cleaned_data.get('create_reminders', False)
        
        imported_count = 0
        errors = []
        
        for row in self.cleaned_data['parsed_rows']:
            try:
                # Traiter les dates et heures
                date_debut = parse_date(row.get('date_debut')).date()
                
                if 'date_fin' in row and row['date_fin'].strip():
                    date_fin = parse_date(row.get('date_fin')).date()
                else:
                    date_fin = date_debut
                
                # Traiter les heures
                start_time = None
                if 'heure_debut' in row and row['heure_debut'].strip():
                    try:
                        # Essayons plusieurs formats d'heure
                        for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p']:
                            try:
                                start_time = datetime.datetime.strptime(
                                    row['heure_debut'].strip(), fmt
                                ).time()
                                break
                            except ValueError:
                                continue
                        if not start_time:
                            time_parts = row['heure_debut'].split(':')
                            if len(time_parts) >= 2:
                                start_time = datetime.time(
                                    int(time_parts[0]), int(time_parts[1])
                                )
                    except (ValueError, IndexError):
                        start_time = None
                
                end_time = None
                if 'heure_fin' in row and row['heure_fin'].strip():
                    try:
                        for fmt in ['%H:%M', '%H:%M:%S', '%I:%M %p']:
                            try:
                                end_time = datetime.datetime.strptime(
                                    row['heure_fin'].strip(), fmt
                                ).time()
                                break
                            except ValueError:
                                continue
                        if not end_time:
                            time_parts = row['heure_fin'].split(':')
                            if len(time_parts) >= 2:
                                end_time = datetime.time(
                                    int(time_parts[0]), int(time_parts[1])
                                )
                    except (ValueError, IndexError):
                        end_time = None
                
                # Créer l'événement
                event = Event(
                    title=row.get('titre', '').strip(),
                    description=row.get('description', '').strip(),
                    event_type=row.get('type_evenement', default_event_type).strip(),
                    organization=organization,
                    start_date=date_debut,
                    end_date=date_fin,
                    start_time=start_time,
                    end_time=end_time,
                    all_day=row.get('journee_entiere', '').lower() in ['true', 'oui', 'yes', '1'],
                    location=row.get('lieu', '').strip(),
                    address=row.get('adresse', '').strip(),
                    city=row.get('ville', '').strip(),
                    postal_code=row.get('code_postal', '').strip(),
                    visibility=row.get('visibilite', default_visibility).strip(),
                    is_public=row.get('public', '').lower() in ['true', 'oui', 'yes', '1'],
                    registration_required=row.get('inscription_requise', '').lower() in ['true', 'oui', 'yes', '1'],
                    created_by=self.user
                )
                
                # Traiter les champs numériques
                if 'max_participants' in row and row['max_participants'].strip():
                    try:
                        event.max_participants = int(row['max_participants'])
                    except ValueError:
                        pass
                
                if 'prix' in row and row['prix'].strip():
                    try:
                        event.price = float(row['prix'].replace(',', '.'))
                    except ValueError:
                        pass
                
                # Traiter la date limite d'inscription
                if 'date_limite_inscription' in row and row['date_limite_inscription'].strip():
                    try:
                        event.registration_deadline = parse_date(row['date_limite_inscription'])
                    except ValueError:
                        pass
                
                # Enregistrer l'événement
                event.save()
                imported_count += 1
                
                # Créer un rappel si demandé
                if create_reminders:
                    from datetime import timedelta
                    from apps.competitions.models.event_planning import EventReminder
                    
                    reminder = EventReminder(
                        event=event,
                        title=_("Rappel: {title}").format(title=event.title),
                        message=_("Rappel: l'événement {title} aura lieu demain Ã  {location}.").format(
                            title=event.title,
                            location=event.location
                        ),
                        reminder_type='all',
                        time_before_event=timedelta(days=1),
                        is_enabled=True,
                        created_by=self.user
                    )
                    reminder.save()
                
            except Exception as e:
                errors.append(f"{row.get('titre', 'Ligne inconnue')}: {str(e)}")
        
        return imported_count, errors


class EventExportForm(forms.Form):
    """
    Formulaire pour exporter des événements au format CSV ou iCalendar.
    """
    EXPORT_FORMAT_CHOICES = [
        ('csv', _('CSV')),
        ('ical', _('iCalendar (ICS)')),
    ]
    
    export_format = forms.ChoiceField(
        label=_("Format d'exportation"),
        choices=EXPORT_FORMAT_CHOICES,
        initial='csv'
    )
    
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label=_("Organisation"),
        required=False,
        help_text=_("Filtrer par organisation. Laissez vide pour exporter tous les événements accessibles.")
    )
    
    start_date = forms.DateField(
        label=_("Date de début"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_("Exporter les événements Ã  partir de cette date. Laissez vide pour inclure tous les événements passés.")
    )
    
    end_date = forms.DateField(
        label=_("Date de fin"),
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text=_("Exporter les événements jusqu'Ã  cette date. Laissez vide pour inclure tous les événements futurs.")
    )
    
    event_types = forms.MultipleChoiceField(
        label=_("Types d'événements"),
        choices=Event.TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=_("Filtrer par types d'événements. Laissez vide pour inclure tous les types.")
    )
    
    include_details = forms.BooleanField(
        label=_("Inclure tous les détails"),
        required=False,
        initial=True,
        help_text=_("Inclure toutes les informations détaillées sur les événements.")
    )
    
    include_participants = forms.BooleanField(
        label=_("Inclure la liste des participants"),
        required=False,
        initial=False,
        help_text=_("Inclure la liste des participants pour chaque événement (CSV uniquement).")
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Définir la date de début par défaut Ã  aujourd'hui
        self.fields['start_date'].initial = timezone.now().date()
        
        # Limiter les organisations accessibles pour les non-superutilisateurs
        if self.user and not self.user.is_superuser:
            from django.db.models import Q
            self.fields['organization'].queryset = Organization.objects.filter(
                members__user=self.user,
                members__is_active=True
            ).distinct()
    
    def get_events_queryset(self):
        """
        Renvoie le queryset des événements Ã  exporter selon les filtres appliqués.
        """
        # Commencer avec tous les événements
        events = Event.objects.all()
        
        # Appliquer les filtres
        organization = self.cleaned_data.get('organization')
        if organization:
            events = events.filter(organization=organization)
        
        start_date = self.cleaned_data.get('start_date')
        if start_date:
            events = events.filter(start_date__gte=start_date)
        
        end_date = self.cleaned_data.get('end_date')
        if end_date:
            events = events.filter(end_date__lte=end_date)
        
        event_types = self.cleaned_data.get('event_types')
        if event_types:
            events = events.filter(event_type__in=event_types)
        
        # Si l'utilisateur n'est pas superuser, limiter aux événements auxquels il a accès
        if self.user and not self.user.is_superuser:
            from django.db.models import Q
            user_orgs = Organization.objects.filter(
                members__user=self.user,
                members__is_active=True
            )
            events = events.filter(organization__in=user_orgs)
        
        return events.order_by('start_date', 'start_time')

