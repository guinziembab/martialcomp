"""
Service de calendrier familial consolidé pour MartialComp.
Centralise tous les événements familiaux, compétitions, entraînements, etc.
"""

from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, date
from collections import defaultdict
import calendar

from .models import Family, FamilyEvent, FamilyMember
from competitions.models import Competition, Event, Practitioner

# Import conditionnel pour éviter les erreurs si les modèles n'existent pas
try:
    from competitions.models.schedule import CompetitionSchedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

try:
    from competitions.models.training import TrainingSession
    TRAINING_AVAILABLE = True
except ImportError:
    TRAINING_AVAILABLE = False


class FamilyCalendarService:
    """Service principal pour gérer le calendrier familial consolidé."""
    
    def __init__(self, family):
        self.family = family
        self.cache_timeout = 300  # 5 minutes
    
    def get_consolidated_calendar(self, start_date=None, end_date=None, member_filters=None):
        """
        Récupère un calendrier consolidé avec tous les événements familiaux.
        
        Args:
            start_date (date): Date de début (défaut: aujourd'hui)
            end_date (date): Date de fin (défaut: +30 jours)
            member_filters (list): IDs des membres à inclure (défaut: tous)
            
        Returns:
            dict: Calendrier consolidé avec événements par date
        """
        if not start_date:
            start_date = timezone.now().date()
        if not end_date:
            end_date = start_date + timedelta(days=30)
        
        # Récupérer tous les événements
        family_events = self._get_family_events(start_date, end_date, member_filters)
        competition_events = self._get_competition_events(start_date, end_date, member_filters)
        training_events = self._get_training_events(start_date, end_date, member_filters)
        organization_events = self._get_organization_events(start_date, end_date)
        
        # Consolider tous les événements
        consolidated_events = self._consolidate_events(
            family_events, competition_events, training_events, organization_events
        )
        
        # Organiser par date
        calendar_data = self._organize_by_date(consolidated_events, start_date, end_date)
        
        # Ajouter des métadonnées
        calendar_data['metadata'] = {
            'start_date': start_date,
            'end_date': end_date,
            'family_id': str(self.family.id),
            'family_name': self.family.family_name,
            'total_events': sum(len(events) for events in calendar_data['events_by_date'].values()),
            'active_members': self.family.get_active_members().count(),
            'filtered_members': len(member_filters) if member_filters else 'all'
        }
        
        return calendar_data
    
    def _get_family_events(self, start_date, end_date, member_filters=None):
        """Récupère les événements familiaux privés."""
        events = FamilyEvent.objects.filter(
            family=self.family,
            start_date__date__range=(start_date, end_date)
        ).select_related('created_by', 'family').prefetch_related('concerned_members')
        
        if member_filters:
            events = events.filter(concerned_members__id__in=member_filters)
        
        family_events = []
        for event in events:
            family_events.append({
                'id': f"family_{event.id}",
                'title': event.title,
                'description': event.description,
                'start_date': event.start_date.date(),
                'start_time': event.start_date.time(),
                'end_date': event.end_date.date() if event.end_date else event.start_date.date(),
                'end_time': event.end_date.time() if event.end_date else None,
                'location': event.location,
                'type': 'family_event',
                'is_private': event.is_private,
                'created_by': event.created_by.get_full_name(),
                'concerned_members': [member.user.get_full_name() for member in event.concerned_members.all()],
                'color': '#FF6B6B',  # Rouge pour événements familiaux
                'icon': 'fas fa-home',
                'can_edit': True
            })
        
        return family_events
    
    def _get_competition_events(self, start_date, end_date, member_filters=None):
        """Récupère les compétitions des membres de la famille."""
        # Récupérer les pratiquants de la famille
        family_practitioners = []
        members = self.family.get_active_members()
        if member_filters:
            members = members.filter(id__in=member_filters)
        
        for member in members:
            if member.practitioner:
                family_practitioners.append(member.practitioner)
        
        if not family_practitioners:
            return []
        
        # Récupérer les compétitions
        competitions = Competition.objects.filter(
            Q(start_date__range=(start_date, end_date)) &
            Q(registrations__practitioner__in=family_practitioners)
        ).distinct().select_related('organizing_organization')
        
        competition_events = []
        for competition in competitions:
            # Vérifier quels membres de la famille participent
            participating_members = []
            for practitioner in family_practitioners:
                if competition.registrations.filter(practitioner=practitioner).exists():
                    participating_members.append(practitioner.user.get_full_name())
            
            competition_events.append({
                'id': f"competition_{competition.id}",
                'title': competition.title,
                'description': competition.description or _("Compétition"),
                'start_date': competition.start_date,
                'start_time': competition.start_time,
                'end_date': competition.end_date or competition.start_date,
                'end_time': competition.end_time,
                'location': competition.venue_name or competition.address,
                'type': 'competition',
                'is_private': False,
                'organization': competition.organizing_organization.name if competition.organizing_organization else '',
                'participating_members': participating_members,
                'color': '#4ECDC4',  # Turquoise pour compétitions
                'icon': 'fas fa-trophy',
                'can_edit': False,
                'registration_deadline': competition.registration_deadline
            })
        
        return competition_events
    
    def _get_training_events(self, start_date, end_date, member_filters=None):
        """Récupère les entraînements des membres de la famille."""
        if not TRAINING_AVAILABLE:
            return []
        
        # Cette implémentation dépend de l'existence du modèle TrainingSession
        # À adapter selon la structure réelle des entraînements dans MartialComp
        training_events = []
        
        # Logique de récupération des entraînements à implémenter
        # selon les modèles disponibles
        
        return training_events
    
    def _get_organization_events(self, start_date, end_date):
        """Récupère les événements de l'organisation."""
        if not self.family.organization:
            return []
        
        org_events = Event.objects.filter(
            organization=self.family.organization,
            start_date__range=(start_date, end_date),
            visibility__in=['public', 'members']
        ).select_related('organization')
        
        organization_events = []
        for event in org_events:
            organization_events.append({
                'id': f"org_{event.id}",
                'title': event.title,
                'description': event.description,
                'start_date': event.start_date,
                'start_time': event.start_time,
                'end_date': event.end_date,
                'end_time': event.end_time,
                'location': getattr(event, 'location', ''),
                'type': f"org_{event.event_type}",
                'is_private': event.visibility == 'private',
                'organization': event.organization.name,
                'color': '#95E1D3',  # Vert clair pour événements d'organisation
                'icon': 'fas fa-building',
                'can_edit': False
            })
        
        return organization_events
    
    def _consolidate_events(self, *event_lists):
        """Consolide tous les types d'événements en une seule liste."""
        all_events = []
        for event_list in event_lists:
            all_events.extend(event_list)
        
        # Trier par date et heure
        all_events.sort(key=lambda x: (x['start_date'], x['start_time'] or timezone.now().time()))
        
        return all_events
    
    def _organize_by_date(self, events, start_date, end_date):
        """Organise les événements par date pour le calendrier."""
        events_by_date = defaultdict(list)
        date_info = {}
        
        # Créer la structure du calendrier
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            events_by_date[date_key] = []
            date_info[date_key] = {
                'date': current_date,
                'day_name': current_date.strftime('%A'),
                'is_today': current_date == timezone.now().date(),
                'is_weekend': current_date.weekday() >= 5,
                'event_count': 0
            }
            current_date += timedelta(days=1)
        
        # Ajouter les événements
        for event in events:
            event_date = event['start_date']
            if isinstance(event_date, datetime):
                event_date = event_date.date()
            
            date_key = event_date.strftime('%Y-%m-%d')
            if date_key in events_by_date:
                events_by_date[date_key].append(event)
                date_info[date_key]['event_count'] += 1
        
        return {
            'events_by_date': dict(events_by_date),
            'date_info': date_info,
            'month_view': self._generate_month_view(start_date, events_by_date)
        }
    
    def _generate_month_view(self, start_date, events_by_date):
        """Génère une vue mensuelle du calendrier."""
        month_data = {}
        
        # Générer les données pour chaque mois dans la période
        current_date = start_date.replace(day=1)  # Premier jour du mois
        
        while True:
            month_key = current_date.strftime('%Y-%m')
            
            if month_key not in month_data:
                # Générer le calendrier du mois
                cal = calendar.monthcalendar(current_date.year, current_date.month)
                month_data[month_key] = {
                    'year': current_date.year,
                    'month': current_date.month,
                    'month_name': current_date.strftime('%B'),
                    'weeks': []
                }
                
                for week in cal:
                    week_data = []
                    for day in week:
                        if day == 0:
                            week_data.append({'day': 0, 'events': [], 'other_month': True})
                        else:
                            day_date = date(current_date.year, current_date.month, day)
                            date_key = day_date.strftime('%Y-%m-%d')
                            day_events = events_by_date.get(date_key, [])
                            
                            week_data.append({
                                'day': day,
                                'date': day_date,
                                'events': day_events,
                                'event_count': len(day_events),
                                'other_month': False,
                                'is_today': day_date == timezone.now().date()
                            })
                    
                    month_data[month_key]['weeks'].append(week_data)
            
            # Passer au mois suivant
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
            
            # Arrêter si on a dépassé la période demandée
            if current_date > start_date + timedelta(days=60):  # Limite raisonnable
                break
        
        return month_data
    
    def get_upcoming_events(self, days_ahead=7, member_filters=None):
        """Récupère les événements à venir pour la famille."""
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=days_ahead)
        
        calendar_data = self.get_consolidated_calendar(start_date, end_date, member_filters)
        
        upcoming_events = []
        for date_key, events in calendar_data['events_by_date'].items():
            for event in events:
                if event['start_date'] >= start_date:
                    event['days_until'] = (event['start_date'] - start_date).days
                    upcoming_events.append(event)
        
        return sorted(upcoming_events, key=lambda x: (x['start_date'], x['start_time'] or timezone.now().time()))
    
    def get_member_availability(self, target_date, member_id=None):
        """Vérifie la disponibilité des membres pour une date donnée."""
        if member_id:
            members = self.family.get_active_members().filter(id=member_id)
        else:
            members = self.family.get_active_members()
        
        availability = {}
        
        for member in members:
            member_events = self.get_consolidated_calendar(
                start_date=target_date,
                end_date=target_date,
                member_filters=[member.id]
            )
            
            date_key = target_date.strftime('%Y-%m-%d')
            day_events = member_events['events_by_date'].get(date_key, [])
            
            availability[member.id] = {
                'member_name': member.user.get_full_name(),
                'is_available': len(day_events) == 0,
                'events_count': len(day_events),
                'events': day_events,
                'conflict_periods': self._calculate_conflict_periods(day_events)
            }
        
        return availability
    
    def _calculate_conflict_periods(self, events):
        """Calcule les périodes de conflit dans la journée."""
        periods = []
        for event in events:
            start_time = event.get('start_time')
            end_time = event.get('end_time')
            
            if start_time:
                period = {
                    'start': start_time,
                    'end': end_time or start_time,
                    'event_title': event['title']
                }
                periods.append(period)
        
        # Trier par heure de début
        periods.sort(key=lambda x: x['start'])
        return periods
    
    def suggest_optimal_time(self, target_date, duration_minutes=60, preferred_time=None):
        """Suggère le meilleur créneau pour un événement familial."""
        availability = self.get_member_availability(target_date)
        
        # Analyser les créneaux libres communs
        free_periods = self._find_common_free_periods(availability, duration_minutes)
        
        # Scorer les créneaux selon les préférences
        scored_periods = self._score_time_periods(free_periods, preferred_time)
        
        return {
            'target_date': target_date,
            'suggested_times': scored_periods[:3],  # Top 3 suggestions
            'member_availability': availability,
            'optimal_duration': duration_minutes
        }
    
    def _find_common_free_periods(self, availability, duration_minutes):
        """Trouve les créneaux libres communs à tous les membres."""
        # Implémentation simplifiée - à améliorer selon les besoins
        business_hours = [
            (9, 0),   # 9h00
            (12, 0),  # 12h00
            (14, 0),  # 14h00
            (18, 0),  # 18h00
            (20, 0)   # 20h00
        ]
        
        free_periods = []
        for hour, minute in business_hours:
            # Vérifier si ce créneau est libre pour tous
            is_free_for_all = True
            for member_data in availability.values():
                for conflict in member_data['conflict_periods']:
                    conflict_start = conflict['start']
                    conflict_end = conflict['end']
                    
                    suggested_time = timezone.now().replace(hour=hour, minute=minute).time()
                    if conflict_start <= suggested_time <= conflict_end:
                        is_free_for_all = False
                        break
            
            if is_free_for_all:
                free_periods.append({
                    'start_time': f"{hour:02d}:{minute:02d}",
                    'duration': duration_minutes,
                    'conflicts': 0
                })
        
        return free_periods
    
    def _score_time_periods(self, periods, preferred_time=None):
        """Score les créneaux selon différents critères."""
        for period in periods:
            score = 100  # Score de base
            
            # Bonus si proche de l'heure préférée
            if preferred_time:
                # Logic de comparaison des heures
                score += 20
            
            # Bonus pour les heures 'normales'
            hour = int(period['start_time'].split(':')[0])
            if 10 <= hour <= 17:  # Heures de bureau
                score += 15
            elif 18 <= hour <= 20:  # Soirée
                score += 10
            
            period['score'] = score
        
        return sorted(periods, key=lambda x: x['score'], reverse=True)