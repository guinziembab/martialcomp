"""
Service de calendrier unifié pour le pratiquant (Prompt 4).

Agrège les événements de différentes sources :
- Compétitions (discipline du pratiquant)
- Examens de grade (grade cible)
- Événements du club
- Deadlines d'inscription
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from django.core.cache import cache
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """Représente un événement du calendrier."""
    id: str  # Format: "type_id" (e.g., "competition_123")
    type: str  # competition, exam, club, deadline, registered
    title: str
    start: datetime
    end: Optional[datetime] = None
    all_day: bool = False
    color: str = "#3498db"
    url: str = ""
    location: str = ""
    discipline: str = ""
    is_registered: bool = False
    registration_open: bool = True
    registration_deadline: Optional[date] = None
    spots_remaining: Optional[int] = None
    spots_total: Optional[int] = None
    fee: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Conversion pour FullCalendar."""
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'start': self.start.isoformat() if isinstance(self.start, datetime) else self.start,
            'end': self.end.isoformat() if self.end and isinstance(self.end, datetime) else self.end,
            'allDay': self.all_day,
            'color': self.color,
            'url': self.url,
            'extendedProps': {
                'location': self.location,
                'discipline': self.discipline,
                'is_registered': self.is_registered,
                'registration_open': self.registration_open,
                'registration_deadline': self.registration_deadline.isoformat() if self.registration_deadline else None,
                'spots_remaining': self.spots_remaining,
                'spots_total': self.spots_total,
                'fee': self.fee,
                'event_type': self.type,
                **self.metadata,
            }
        }


class CalendarService:
    """
    Service de calendrier unifié pour le pratiquant.

    Usage:
        service = CalendarService(practitioner)
        events = service.get_events(
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31),
            types=['competition', 'exam', 'club']
        )
    """

    # Couleurs par type d'événement
    EVENT_COLORS = {
        'competition': '#3498db',   # Bleu
        'exam': '#f1c40f',          # Jaune
        'club': '#2ecc71',          # Vert
        'deadline': '#e74c3c',      # Rouge
        'registered': '#9b59b6',    # Violet
    }

    CACHE_PREFIX = 'calendar_events'
    CACHE_TTL = 3600  # 1 heure

    def __init__(self, practitioner):
        """
        Initialise le service pour un pratiquant.

        Args:
            practitioner: Instance du pratiquant
        """
        self.practitioner = practitioner
        self._cache_key_base = f"{self.CACHE_PREFIX}:{practitioner.id}"

    def get_events(
        self,
        start_date: date,
        end_date: date,
        types: Optional[List[str]] = None,
        discipline_ids: Optional[List[int]] = None,
        include_registered_only: bool = False,
        use_cache: bool = True
    ) -> List[CalendarEvent]:
        """
        Récupère tous les événements pour une période.

        Args:
            start_date: Date de début
            end_date: Date de fin
            types: Types d'événements à inclure (default: tous)
            discipline_ids: IDs des disciplines (default: celles du pratiquant)
            include_registered_only: Uniquement les événements où inscrit
            use_cache: Utiliser le cache

        Returns:
            Liste d'événements triés par date
        """
        if types is None:
            types = ['competition', 'exam', 'club', 'deadline']

        events = []

        # Récupérer les disciplines du pratiquant si non spécifiées
        if discipline_ids is None:
            discipline_ids = self._get_practitioner_disciplines()

        # Agrégation des événements par type
        if 'competition' in types:
            events.extend(self._get_competitions(start_date, end_date, discipline_ids, include_registered_only))

        if 'exam' in types:
            events.extend(self._get_exams(start_date, end_date, discipline_ids, include_registered_only))

        if 'club' in types:
            events.extend(self._get_club_events(start_date, end_date))

        if 'deadline' in types:
            events.extend(self._get_deadlines(start_date, end_date, discipline_ids))

        # Trier par date de début
        events.sort(key=lambda e: e.start)

        return events

    def _get_practitioner_disciplines(self) -> List[int]:
        """Récupère les IDs des disciplines du pratiquant."""
        discipline_ids = []

        try:
            # Via PractitionerDiscipline
            from apps.grades.models import PractitionerDiscipline
            practitioner_disciplines = PractitionerDiscipline.objects.filter(
                practitioner=self.practitioner
            ).values_list('discipline_id', flat=True)
            discipline_ids.extend(list(practitioner_disciplines))
        except Exception:
            pass

        # Via grades obtenus
        try:
            from apps.grades.models import PractitionerGrade
            grade_disciplines = PractitionerGrade.objects.filter(
                practitioner=self.practitioner
            ).values_list('grade__discipline_id', flat=True).distinct()
            discipline_ids.extend([d for d in grade_disciplines if d not in discipline_ids])
        except Exception:
            pass

        # Via club
        try:
            if self.practitioner.club and self.practitioner.club.discipline:
                if self.practitioner.club.discipline_id not in discipline_ids:
                    discipline_ids.append(self.practitioner.club.discipline_id)
        except Exception:
            pass

        return list(set(discipline_ids))

    def _get_competitions(
        self,
        start_date: date,
        end_date: date,
        discipline_ids: List[int],
        registered_only: bool = False
    ) -> List[CalendarEvent]:
        """Récupère les compétitions."""
        events = []

        try:
            from apps.competitions.models import Competition, CompetitionRegistration

            # Query de base
            filters = Q(
                start_date__gte=start_date,
                start_date__lte=end_date,
                status__in=['published', 'open', 'registration_open']
            )

            # Filtrer par discipline si spécifié
            if discipline_ids:
                filters &= Q(discipline_id__in=discipline_ids)

            competitions = Competition.objects.filter(filters).select_related('discipline')

            # Récupérer les inscriptions du pratiquant
            registered_competition_ids = set()
            if self.practitioner:
                registered_competition_ids = set(
                    CompetitionRegistration.objects.filter(
                        practitioner=self.practitioner,
                        status__in=['confirmed', 'pending']
                    ).values_list('competition_id', flat=True)
                )

            if registered_only:
                competitions = competitions.filter(id__in=registered_competition_ids)

            for comp in competitions:
                is_registered = comp.id in registered_competition_ids
                event_type = 'registered' if is_registered else 'competition'

                # Calculer les places restantes
                spots_remaining = None
                spots_total = None
                if hasattr(comp, 'max_participants') and comp.max_participants:
                    spots_total = comp.max_participants
                    registered_count = Registration.objects.filter(
                        competition=comp,
                        status__in=['confirmed', 'pending']
                    ).count()
                    spots_remaining = max(0, spots_total - registered_count)

                # Vérifier si inscriptions ouvertes
                registration_open = True
                if hasattr(comp, 'registration_deadline') and comp.registration_deadline:
                    registration_open = comp.registration_deadline >= timezone.now().date()

                events.append(CalendarEvent(
                    id=f"competition_{comp.id}",
                    type=event_type,
                    title=comp.title,
                    start=datetime.combine(comp.start_date, comp.start_time or datetime.min.time()),
                    end=datetime.combine(comp.end_date or comp.start_date, comp.end_time or datetime.max.time()) if hasattr(comp, 'end_date') else None,
                    all_day=not comp.start_time if hasattr(comp, 'start_time') else True,
                    color=self.EVENT_COLORS.get(event_type, '#3498db'),
                    url=f"/competitions/competitions/{comp.id}/",
                    location=comp.location if hasattr(comp, 'location') else '',
                    discipline=comp.discipline.name if comp.discipline else '',
                    is_registered=is_registered,
                    registration_open=registration_open,
                    registration_deadline=comp.registration_deadline if hasattr(comp, 'registration_deadline') else None,
                    spots_remaining=spots_remaining,
                    spots_total=spots_total,
                    fee=str(comp.registration_fee) if hasattr(comp, 'registration_fee') and comp.registration_fee else None,
                    metadata={
                        'categories': list(comp.categories.values_list('name', flat=True)) if hasattr(comp, 'categories') else [],
                        'competition_type': comp.competition_type if hasattr(comp, 'competition_type') else '',
                    }
                ))

        except Exception as e:
            logger.error(f"Erreur récupération compétitions: {e}")

        return events

    def _get_exams(
        self,
        start_date: date,
        end_date: date,
        discipline_ids: List[int],
        registered_only: bool = False
    ) -> List[CalendarEvent]:
        """Récupère les examens de grade."""
        events = []

        try:
            from apps.grades.models import GradeExam, GradeExamRegistration

            # Query de base
            filters = Q(
                date__gte=start_date,
                date__lte=end_date,
                status='scheduled'
            )

            if discipline_ids:
                filters &= Q(discipline_id__in=discipline_ids)

            exams = GradeExam.objects.filter(filters).select_related('discipline')

            # Récupérer les inscriptions
            registered_exam_ids = set()
            if self.practitioner:
                try:
                    registered_exam_ids = set(
                        GradeExamRegistration.objects.filter(
                            practitioner=self.practitioner,
                            status__in=['registered', 'confirmed']
                        ).values_list('exam_id', flat=True)
                    )
                except Exception:
                    pass

            if registered_only:
                exams = exams.filter(id__in=registered_exam_ids)

            for exam in exams:
                is_registered = exam.id in registered_exam_ids
                event_type = 'registered' if is_registered else 'exam'

                # Vérifier si inscriptions ouvertes
                registration_open = True
                if exam.registration_deadline:
                    registration_open = exam.registration_deadline >= timezone.now().date()

                # Récupérer les grades disponibles
                available_grades = []
                if hasattr(exam, 'available_grades'):
                    available_grades = list(exam.available_grades.values_list('name', flat=True))

                events.append(CalendarEvent(
                    id=f"exam_{exam.id}",
                    type=event_type,
                    title=exam.title,
                    start=datetime.combine(exam.date, exam.start_time if hasattr(exam, 'start_time') and exam.start_time else datetime.min.time()),
                    end=datetime.combine(exam.date, exam.end_time) if hasattr(exam, 'end_time') and exam.end_time else None,
                    all_day=not (hasattr(exam, 'start_time') and exam.start_time),
                    color=self.EVENT_COLORS.get(event_type, '#f1c40f'),
                    url=reverse('grades:exam_detail', kwargs={'pk': exam.id}),
                    location=exam.location if hasattr(exam, 'location') else '',
                    discipline=exam.discipline.name if exam.discipline else '',
                    is_registered=is_registered,
                    registration_open=registration_open,
                    registration_deadline=exam.registration_deadline,
                    fee=str(exam.fee) if hasattr(exam, 'fee') and exam.fee else None,
                    metadata={
                        'available_grades': available_grades,
                        'examiner': exam.examiner if hasattr(exam, 'examiner') else '',
                    }
                ))

        except Exception as e:
            logger.error(f"Erreur récupération examens: {e}")

        return events

    def _get_club_events(
        self,
        start_date: date,
        end_date: date
    ) -> List[CalendarEvent]:
        """Récupère les événements du club/organisation du pratiquant."""
        events = []

        try:
            from apps.competitions.models import Event

            # Récupérer l'organisation du pratiquant via son club
            organization = None
            if self.practitioner.club:
                organization = self.practitioner.club.organization

            if not organization:
                # Essayer de récupérer via les memberships du user
                try:
                    from apps.organizations.models import OrganizationMember
                    membership = OrganizationMember.objects.filter(
                        user=self.practitioner.user,
                        is_active=True
                    ).first()
                    if membership:
                        organization = membership.organization
                except Exception:
                    pass

            if not organization:
                return events

            # Filtrer les événements de l'organisation
            # - Non annulés
            # - Visibles (public ou membres)
            # - Dans la plage de dates
            club_events = Event.objects.filter(
                organization=organization,
                start_date__lte=end_date,
                end_date__gte=start_date,
                is_cancelled=False,
                is_archived=False
            ).filter(
                Q(visibility='public') |
                Q(visibility='members') |
                Q(is_public=True)
            ).order_by('start_date', 'start_time')

            for event in club_events:
                event_start = datetime.combine(
                    event.start_date,
                    event.start_time if event.start_time else datetime.min.time()
                )
                event_end = None
                if event.end_date:
                    event_end = datetime.combine(
                        event.end_date,
                        event.end_time if event.end_time else datetime.max.time()
                    )

                events.append(CalendarEvent(
                    id=f"club_{event.id}",
                    type='club',
                    title=event.title,
                    start=event_start,
                    end=event_end,
                    all_day=event.all_day if hasattr(event, 'all_day') else not event.start_time,
                    color=self.EVENT_COLORS['club'],
                    url=f"/competitions/events/{event.id}/",
                    location=event.location or '',
                    metadata={
                        'event_type': event.event_type or '',
                        'description': event.description or '',
                        'organization': organization.name if organization else '',
                    }
                ))

        except Exception as e:
            logger.error(f"Erreur récupération événements club: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return events

    def _get_deadlines(
        self,
        start_date: date,
        end_date: date,
        discipline_ids: List[int]
    ) -> List[CalendarEvent]:
        """Récupère les deadlines d'inscription."""
        events = []

        try:
            from apps.competitions.models import Competition
            from apps.grades.models import GradeExam

            # Deadlines compétitions
            competitions = Competition.objects.filter(
                registration_deadline__gte=start_date,
                registration_deadline__lte=end_date,
                status__in=['published', 'open', 'registration_open']
            )

            if discipline_ids:
                competitions = competitions.filter(discipline_id__in=discipline_ids)

            for comp in competitions:
                if comp.registration_deadline:
                    events.append(CalendarEvent(
                        id=f"deadline_comp_{comp.id}",
                        type='deadline',
                        title=f"Deadline: {comp.title}",
                        start=datetime.combine(comp.registration_deadline, datetime.max.time().replace(hour=23, minute=59)),
                        all_day=True,
                        color=self.EVENT_COLORS['deadline'],
                        url=f"/competitions/competitions/{comp.id}/",
                        metadata={
                            'parent_type': 'competition',
                            'parent_id': comp.id,
                        }
                    ))

            # Deadlines examens
            exams = GradeExam.objects.filter(
                registration_deadline__gte=start_date,
                registration_deadline__lte=end_date,
                status='scheduled'
            )

            if discipline_ids:
                exams = exams.filter(discipline_id__in=discipline_ids)

            for exam in exams:
                if exam.registration_deadline:
                    events.append(CalendarEvent(
                        id=f"deadline_exam_{exam.id}",
                        type='deadline',
                        title=f"Deadline: {exam.title}",
                        start=datetime.combine(exam.registration_deadline, datetime.max.time().replace(hour=23, minute=59)),
                        all_day=True,
                        color=self.EVENT_COLORS['deadline'],
                        url=reverse('grades:exam_detail', kwargs={'pk': exam.id}),
                        metadata={
                            'parent_type': 'exam',
                            'parent_id': exam.id,
                        }
                    ))

        except Exception as e:
            logger.error(f"Erreur récupération deadlines: {e}")

        return events

    def generate_ics(
        self,
        events: List[CalendarEvent],
        calendar_name: str = "MartialComp - Mon Calendrier"
    ) -> str:
        """
        Génère un fichier ICS pour export.

        Args:
            events: Liste d'événements
            calendar_name: Nom du calendrier

        Returns:
            Contenu du fichier ICS
        """
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//MartialComp//Calendar//FR",
            f"X-WR-CALNAME:{calendar_name}",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
        ]

        for event in events:
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:{event.id}@martialcomp.com")

            # Format dates
            if event.all_day:
                start_str = event.start.strftime("%Y%m%d") if isinstance(event.start, (date, datetime)) else event.start
                lines.append(f"DTSTART;VALUE=DATE:{start_str}")
                if event.end:
                    end_str = event.end.strftime("%Y%m%d") if isinstance(event.end, (date, datetime)) else event.end
                    lines.append(f"DTEND;VALUE=DATE:{end_str}")
            else:
                start_str = event.start.strftime("%Y%m%dT%H%M%S") if isinstance(event.start, datetime) else event.start
                lines.append(f"DTSTART:{start_str}")
                if event.end:
                    end_str = event.end.strftime("%Y%m%dT%H%M%S") if isinstance(event.end, datetime) else event.end
                    lines.append(f"DTEND:{end_str}")

            lines.append(f"SUMMARY:{event.title}")

            if event.location:
                lines.append(f"LOCATION:{event.location}")

            if event.url:
                lines.append(f"URL:{event.url}")

            # Description
            description_parts = []
            if event.discipline:
                description_parts.append(f"Discipline: {event.discipline}")
            if event.registration_deadline:
                description_parts.append(f"Deadline inscription: {event.registration_deadline}")
            if event.fee:
                description_parts.append(f"Frais: {event.fee}")

            if description_parts:
                lines.append(f"DESCRIPTION:{' | '.join(description_parts)}")

            # Catégorie
            category_map = {
                'competition': 'COMPETITION',
                'exam': 'EXAMEN',
                'club': 'CLUB',
                'deadline': 'DEADLINE',
                'registered': 'INSCRIT',
            }
            lines.append(f"CATEGORIES:{category_map.get(event.type, 'OTHER')}")

            lines.append("END:VEVENT")

        lines.append("END:VCALENDAR")

        return "\r\n".join(lines)

    @staticmethod
    def get_event_type_label(event_type: str) -> str:
        """Retourne le label traduit pour un type d'événement."""
        labels = {
            'competition': _('Compétition'),
            'exam': _('Examen de grade'),
            'club': _('Événement club'),
            'deadline': _('Date limite'),
            'registered': _('Inscrit'),
        }
        return labels.get(event_type, event_type)
