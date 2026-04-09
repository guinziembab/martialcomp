# API module for competitions app
from django.urls import path
from django.db import models

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from apps.competitions.models.competitions import Competition
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset


class CompetitionListView(APIView):
    """Liste des compétitions pour utilisateurs authentifiés."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def _serialize_competition(self, c):
        return {
            'id': c.id,
            'name': c.title or '',
            'title': c.title or '',
            'start_date': c.start_date.isoformat() if c.start_date else None,
            'end_date': c.end_date.isoformat() if c.end_date else None,
            'start_time': c.start_time.isoformat() if c.start_time else None,
            'end_time': c.end_time.isoformat() if c.end_time else None,
            'location': ', '.join(filter(None, [c.venue_name, c.city])) or '',
            'venue': c.venue_name or '',
            'address': c.address or '',
            'city': c.city or '',
            'description': c.description or '',
            'status': c.status or 'draft',
            'discipline': c.discipline.name if c.discipline else '',
            'discipline_id': c.discipline_id,
            'is_published': c.is_published,
            'max_participants': c.max_participants,
            'registration_deadline': c.registration_deadline.isoformat() if c.registration_deadline else None,
            'organizing_organization': c.organizing_organization.name if c.organizing_organization else '',
            'organizing_organization_id': c.organizing_organization_id,
        }

    def get(self, request):
        import logging
        logger = logging.getLogger(__name__)

        user = request.user
        qs = Competition.objects.select_related('discipline', 'organizing_organization')

        # Filtrage par query params
        my_registrations = request.query_params.get('my_registrations')
        is_public = request.query_params.get('isPublic')
        is_international = request.query_params.get('isInternational')
        query = request.query_params.get('query', '').strip()

        from django.db.models import Q

        # Déterminer l'organisation et les disciplines de l'utilisateur
        user_org = None
        user_discipline_ids = []
        try:
            from apps.competitions.models.users import UserProfile
            profile = UserProfile.objects.select_related('organization').get(user=user)
            user_org = profile.organization
        except Exception:
            pass

        # Récupérer les disciplines du club/organisation de l'utilisateur
        try:
            from apps.competitions.models import Club
            user_club = Club.objects.filter(owner=user).first()
            if user_club:
                user_discipline_ids = list(user_club.disciplines.values_list('id', flat=True))
            if not user_discipline_ids and user_org:
                user_discipline_ids = list(user_org.disciplines.values_list('id', flat=True))
        except Exception:
            pass

        if my_registrations:
            # "My comp." = compétitions où l'utilisateur est inscrit OU qu'il a organisées
            from apps.competitions.models.registrations import CompetitionRegistration
            reg_comp_ids = list(CompetitionRegistration.objects.filter(
                practitioner__user=user
            ).values_list('competition_id', flat=True))
            my_filter = Q(id__in=reg_comp_ids)
            # Aussi inclure les compétitions organisées par l'utilisateur ou son organisation
            if user_org:
                my_filter |= Q(organizing_organization=user_org)
            from apps.competitions.models import Club
            user_club = Club.objects.filter(owner=user).first()
            if user_club and user_club.organization:
                my_filter |= Q(organizing_organization=user_club.organization)
            qs = qs.filter(my_filter)
        else:
            # Par défaut: compétitions publiées ou de l'organisation de l'utilisateur
            org_filter = Q(is_published=True) | Q(status='published')
            if user_org:
                org_filter |= Q(organizing_organization=user_org)
            if user.is_superuser or user.is_staff:
                pass  # Pas de filtre pour les admins
            else:
                qs = qs.filter(org_filter)
                # Filtrage par discipline : ne montrer que les compétitions
                # correspondant aux disciplines du club de l'utilisateur
                if user_discipline_ids:
                    qs = qs.filter(
                        Q(discipline_id__in=user_discipline_ids) |
                        Q(discipline__isnull=True)
                    )

        # Filtre "upcoming" : uniquement les compétitions futures
        is_upcoming = request.query_params.get('upcoming') or request.path.rstrip('/').endswith('upcoming')
        if is_upcoming:
            qs = qs.filter(start_date__gte=timezone.now().date())

        if is_public:
            qs = qs.filter(is_published=True)

        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

        # Dédupliquage
        qs = qs.distinct()

        # Tri : à venir d'abord par date croissante si upcoming, sinon date décroissante
        if is_upcoming:
            qs = qs.order_by('start_date')
        else:
            qs = qs.order_by('-start_date')

        # Pagination
        page = int(request.query_params.get('page', 1))
        limit = min(int(request.query_params.get('limit', 20)), 100)
        total = qs.count()
        start = (page - 1) * limit
        competitions = [self._serialize_competition(c) for c in qs[start:start + limit]]

        response_data = {
            'results': competitions,
            'competitions': competitions,
            'upcoming_competitions': competitions,
            'count': total,
            'total': total,
            'page': page,
            'limit': limit,
            'has_next': (start + limit) < total,
            'has_previous': page > 1,
        }
        return Response(response_data)


class PublicEventsView(APIView):
    """Liste des événements publics (compétitions, entraînements, examens, séminaires, réunions, etc.) - sans authentification."""
    permission_classes = [AllowAny]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from datetime import timedelta
        import logging
        logger = logging.getLogger(__name__)

        now = timezone.now()
        events = []

        # DEBUG: Log authentication status
        logger.info(f"PublicEventsView: user={request.user}, authenticated={request.user.is_authenticated}")

        # Récupérer l'organisation du pratiquant si authentifié
        user_organization = None
        if request.user.is_authenticated:
            try:
                from apps.competitions.models import Practitioner
                # Use only 'organization' in select_related - 'club' may not exist in production
                practitioner = Practitioner.objects.filter(user=request.user).select_related(
                    'organization'
                ).first()
                logger.info(f"PublicEventsView: practitioner={practitioner}")
                if practitioner:
                    # Try to access club if it exists
                    if hasattr(practitioner, 'club') and practitioner.club:
                        user_organization = getattr(practitioner.club, 'organization', None)
                        logger.info(f"PublicEventsView: club={practitioner.club}, club.org={user_organization}")
                    if not user_organization:
                        user_organization = practitioner.organization
                        logger.info(f"PublicEventsView: practitioner.organization={user_organization}")
                    # Si pas trouvé, essayer via OrganizationMember
                    if not user_organization:
                        try:
                            from apps.organizations.models import OrganizationMember
                            membership = OrganizationMember.objects.filter(
                                user=request.user,
                                is_active=True
                            ).first()
                            if membership:
                                user_organization = membership.organization
                                logger.info(f"PublicEventsView: via OrganizationMember={user_organization}")
                        except Exception:
                            pass
                logger.info(f"PublicEventsView: FINAL user_organization={user_organization} (id={user_organization.id if user_organization else None})")
            except Exception as e:
                logger.error(f"PublicEventsView: Error getting user organization: {e}")

        # Récupérer les disciplines de l'utilisateur pour le filtrage
        user_discipline_ids = []
        if request.user.is_authenticated:
            try:
                from apps.competitions.models import Club
                user_club = Club.objects.filter(owner=request.user).first()
                if user_club:
                    user_discipline_ids = list(user_club.disciplines.values_list('id', flat=True))
                if not user_discipline_ids and user_organization:
                    user_discipline_ids = list(user_organization.disciplines.values_list('id', flat=True))
            except Exception:
                pass

        # Get events from the Event model (training, seminar, exam, meeting, social, etc.)
        try:
            from apps.competitions.models.event import Event
            past_limit = now - timedelta(days=30)

            # DEBUG: Log all events in database for this period
            all_events_debug = Event.objects.filter(
                start_date__gte=past_limit.date(),
                is_cancelled=False,
                is_archived=False
            ).order_by('start_date')[:50]
            for evt in all_events_debug:
                logger.info(f"PublicEventsView DEBUG: Event id={evt.id}, title='{evt.title}', org_id={evt.organization_id}, visibility={evt.visibility}, is_public={getattr(evt, 'is_public', 'N/A')}")

            # Build query: events from user's organization or matching disciplines
            if user_organization:
                # Events de l'organisation de l'utilisateur (membres + publics)
                event_query = models.Q(
                    organization=user_organization,
                    visibility__in=['members', 'public']
                )
            else:
                event_query = models.Q()

            # Ajouter les events publics d'organisations partageant une discipline
            if user_discipline_ids:
                event_query = event_query | models.Q(
                    organization__disciplines__id__in=user_discipline_ids,
                    is_public=True
                )
            elif not user_organization:
                # Pas de discipline ni d'organisation : montrer les events publics
                event_query = models.Q(is_public=True) | models.Q(visibility='public')

            event_qs = Event.objects.filter(
                start_date__gte=past_limit.date(),
                is_cancelled=False,
                is_archived=False
            ).filter(event_query).distinct().order_by('start_date')[:30]

            logger.info(f"PublicEventsView: Query returned {event_qs.count()} events")

            for event in event_qs:
                event_status = 'upcoming'
                if event.start_date < now.date():
                    event_status = 'completed'
                elif event.start_date == now.date():
                    event_status = 'ongoing'

                events.append({
                    'id': f'event_{event.id}',
                    'type': event.event_type,  # competition, training, seminar, exam, meeting, social
                    'name': event.title,
                    'start_date': event.start_date.isoformat() if event.start_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'location': event.location or event.city or 'Non spécifié',
                    'description': event.description or '',
                    'status': event_status,
                    'organization': event.organization.name if event.organization else None,
                    'price': str(event.price) if event.price else '0',
                    'max_participants': event.max_participants,
                    'registration_required': event.registration_required,
                })
        except Exception as e:
            print(f"PublicEventsView: Error loading events: {e}")

        # Get competitions (include recent past for better UX)
        try:
            past_limit = (now - timedelta(days=90)).date()  # 90 days back for past events
            qs = Competition.objects.all()

            # Filter by date range (recent past + future)
            if hasattr(Competition, 'start_date'):
                qs = qs.filter(start_date__gte=past_limit).order_by('start_date')

            # Filtrage par discipline de l'utilisateur
            if user_discipline_ids:
                qs = qs.filter(
                    models.Q(discipline_id__in=user_discipline_ids) |
                    models.Q(discipline__isnull=True)
                )

            for c in qs[:30]:
                # Determine status based on dates
                # Competition.start_date is a DateField, not DateTimeField
                comp_status = 'upcoming'
                if c.start_date:
                    comp_date = c.start_date
                    today = now.date()
                    if comp_date < today:
                        comp_status = 'completed'
                    elif comp_date == today:
                        comp_status = 'ongoing'

                # Use title (not name) and venue_name (not location)
                events.append({
                    'id': f'comp_{c.id}',
                    'type': 'competition',
                    'name': getattr(c, 'title', getattr(c, 'name', '')),
                    'start_date': c.start_date.isoformat() if c.start_date else None,
                    'end_date': c.end_date.isoformat() if hasattr(c, 'end_date') and c.end_date else None,
                    'location': getattr(c, 'venue_name', getattr(c, 'location', 'Non spécifié')),
                    'description': getattr(c, 'description', ''),
                    'status': comp_status,
                })
        except Exception as e:
            logger.error(f"PublicEventsView: Error loading competitions: {e}")

        # Get grade exams (include recent past)
        try:
            from apps.grades.models import GradeExam
            past_date = (now - timedelta(days=30)).date()
            exam_qs = GradeExam.objects.filter(exam_date__gte=past_date)
            if user_discipline_ids:
                exam_qs = exam_qs.filter(
                    models.Q(discipline_id__in=user_discipline_ids) |
                    models.Q(discipline__isnull=True)
                )
            exams = exam_qs.order_by('exam_date')[:10]
            for exam in exams:
                exam_status = 'upcoming'
                if exam.exam_date:
                    if exam.exam_date < now.date():
                        exam_status = 'completed'
                    elif exam.exam_date == now.date():
                        exam_status = 'ongoing'

                events.append({
                    'id': f'exam_{exam.id}',
                    'type': 'exam',
                    'name': getattr(exam, 'name', 'Examen de grade'),
                    'start_date': exam.exam_date.isoformat() if exam.exam_date else None,
                    'end_date': exam.exam_date.isoformat() if exam.exam_date else None,
                    'location': getattr(exam, 'location', 'Non spécifié'),
                    'description': getattr(exam, 'description', ''),
                    'status': exam_status,
                })
        except Exception as e:
            print(f"PublicEventsView: Error loading exams: {e}")

        # Get training sessions (upcoming)
        try:
            from apps.competitions.models.training import TrainingSession, TrainingSlot
            past_date = (now - timedelta(days=7)).date()
            future_limit = (now + timedelta(days=30)).date()

            train_qs = TrainingSession.objects.filter(
                date__gte=past_date,
                date__lte=future_limit,
                is_cancelled=False
            ).select_related('training_slot', 'training_slot__club', 'training_slot__discipline')
            if user_discipline_ids:
                train_qs = train_qs.filter(
                    models.Q(training_slot__discipline_id__in=user_discipline_ids) |
                    models.Q(training_slot__discipline__isnull=True)
                )
            sessions = train_qs[:15]

            for session in sessions:
                session_status = 'upcoming'
                if session.date < now.date():
                    session_status = 'completed'
                elif session.date == now.date():
                    session_status = 'ongoing'

                events.append({
                    'id': f'training_{session.id}',
                    'type': 'training',
                    'name': session.training_slot.name if session.training_slot else 'Entraînement',
                    'start_date': session.date.isoformat() if session.date else None,
                    'end_date': session.date.isoformat() if session.date else None,
                    'location': session.location or 'Non spécifié',
                    'description': session.training_slot.description if session.training_slot else '',
                    'status': session_status,
                })
        except Exception as e:
            print(f"PublicEventsView: Error loading training sessions: {e}")

        # Remove duplicates based on id
        seen_ids = set()
        unique_events = []
        for event in events:
            if event['id'] not in seen_ids:
                seen_ids.add(event['id'])
                unique_events.append(event)

        # Sort all events by date
        unique_events.sort(key=lambda x: x.get('start_date') or '9999-12-31')

        return Response({
            'events': unique_events,
            'count': len(unique_events),
        })


# Import license API
from apps.competitions.views.api import generate_license_number

# Import calendar API views (Prompt 4)
from .calendar import (
    calendar_events_api,
    export_calendar_ics,
    event_detail_api,
)


class EventDetailAPIView(APIView):
    """
    API REST pour le détail d'un événement - Compatible JWT.
    GET /api/competitions/event-detail/<type>/<id>/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    @staticmethod
    def _check_can_edit(user, organization, created_by=None):
        """Check if user can edit an event. Creator or club manager."""
        if created_by and user == created_by:
            return True
        return False

    @staticmethod
    def _check_is_owner(user, created_by=None):
        """Check if user is the owner/creator of the event."""
        if created_by and user == created_by:
            return True
        return False

    def get(self, request, event_type, event_id):
        try:
            data = {}
            user = request.user

            if event_type == 'competition' or event_type == 'comp':
                from apps.competitions.models import Competition
                from apps.competitions.models.registrations import CompetitionRegistration

                comp = Competition.objects.select_related('discipline').get(id=event_id)
                is_registered = False
                try:
                    is_registered = CompetitionRegistration.objects.filter(
                        practitioner__user=user,
                        competition=comp,
                    ).exclude(status='rejected').exists()
                except Exception:
                    pass

                # Récupérer les inscrits du club de l'utilisateur
                club_participants_data = []
                is_club_manager = False
                try:
                    from apps.competitions.utils.permission_helpers import get_user_club
                    user_club = get_user_club(request)
                    if user_club:
                        is_club_manager = True
                        club_org = user_club.organization or getattr(user_club, 'as_organization', None)
                        if club_org:
                            club_regs = CompetitionRegistration.objects.filter(
                                competition=comp,
                                practitioner__organization=club_org
                            ).exclude(status='rejected').select_related('practitioner')
                            for reg in club_regs:
                                club_participants_data.append({
                                    'id': reg.id,
                                    'practitioner_id': reg.practitioner_id,
                                    'name': reg.practitioner.full_name if reg.practitioner else '',
                                    'status': reg.status,
                                    'status_display': reg.get_status_display(),
                                    'role': 'competitor' if reg.is_competitor else ('coach' if reg.is_coach else 'other'),
                                    'registered_at': str(reg.created_at) if hasattr(reg, 'created_at') else None,
                                })
                except Exception:
                    pass

                data = {
                    'id': comp.id,
                    'type': 'competition',
                    'title': getattr(comp, 'title', getattr(comp, 'name', '')),
                    'name': getattr(comp, 'name', getattr(comp, 'title', '')),
                    'date': comp.start_date.isoformat() if comp.start_date else None,
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if hasattr(comp, 'end_date') and comp.end_date else None,
                    'start_time': comp.start_time.isoformat() if hasattr(comp, 'start_time') and comp.start_time else None,
                    'end_time': comp.end_time.isoformat() if hasattr(comp, 'end_time') and comp.end_time else None,
                    'location': comp.venue_name or ', '.join(filter(None, [comp.address, comp.city])) or 'Non spécifié',
                    'address': comp.address or '',
                    'full_address': ', '.join(filter(None, [comp.address, comp.city])) or '',
                    'discipline': comp.discipline.name if comp.discipline else '',
                    'description': getattr(comp, 'description', ''),
                    'registration_deadline': comp.registration_deadline.isoformat() if hasattr(comp, 'registration_deadline') and comp.registration_deadline else None,
                    'registration_fee': str(comp.registration_fee) if hasattr(comp, 'registration_fee') and comp.registration_fee else '0',
                    'price': float(comp.registration_fee) if hasattr(comp, 'registration_fee') and comp.registration_fee else 0,
                    'is_registered': is_registered,
                    'registration_open': comp.registration_deadline >= timezone.now().date() if hasattr(comp, 'registration_deadline') and comp.registration_deadline else True,
                    'categories': list(comp.categories.values_list('name', flat=True)) if hasattr(comp, 'categories') else [],
                    'participants_count': CompetitionRegistration.objects.filter(competition=comp).exclude(status='rejected').count(),
                    'max_participants': getattr(comp, 'max_participants', None),
                    'status': getattr(comp, 'status', 'upcoming'),
                    'is_club_manager': is_club_manager,
                    'can_edit': self._check_can_edit(user, comp.organization if hasattr(comp, 'organization') else None, getattr(comp, 'created_by', None)),
                    'is_owner': self._check_is_owner(user, getattr(comp, 'created_by', None)),
                    'club_participants': club_participants_data,
                    'club_participants_count': len(club_participants_data),
                }

            elif event_type == 'exam':
                from apps.grades.models import GradeExam, GradeExamRegistration

                exam = GradeExam.objects.select_related('discipline').get(id=event_id)
                is_registered = False
                try:
                    is_registered = GradeExamRegistration.objects.filter(
                        practitioner__user=user,
                        exam=exam,
                        status__in=['registered', 'confirmed', 'pending']
                    ).exists()
                except Exception:
                    pass

                exam_date = getattr(exam, 'exam_date', getattr(exam, 'date', None))
                data = {
                    'id': exam.id,
                    'type': 'exam',
                    'title': getattr(exam, 'title', getattr(exam, 'name', 'Examen de grade')),
                    'name': getattr(exam, 'name', getattr(exam, 'title', 'Examen de grade')),
                    'date': exam_date.isoformat() if exam_date else None,
                    'start_date': exam_date.isoformat() if exam_date else None,
                    'start_time': exam.start_time.isoformat() if hasattr(exam, 'start_time') and exam.start_time else None,
                    'end_time': exam.end_time.isoformat() if hasattr(exam, 'end_time') and exam.end_time else None,
                    'location': getattr(exam, 'location', 'Non spécifié'),
                    'discipline': exam.discipline.name if exam.discipline else '',
                    'description': getattr(exam, 'description', ''),
                    'registration_deadline': exam.registration_deadline.isoformat() if hasattr(exam, 'registration_deadline') and exam.registration_deadline else None,
                    'fee': str(exam.fee) if hasattr(exam, 'fee') and exam.fee else '0',
                    'price': float(exam.fee) if hasattr(exam, 'fee') and exam.fee else 0,
                    'is_registered': is_registered,
                    'registration_open': exam.registration_deadline >= timezone.now().date() if hasattr(exam, 'registration_deadline') and exam.registration_deadline else True,
                    'available_grades': list(exam.available_grades.values_list('name', flat=True)) if hasattr(exam, 'available_grades') else [],
                    'examiner': getattr(exam, 'examiner', ''),
                    'max_participants': getattr(exam, 'max_participants', None),
                }

            elif event_type == 'training':
                # TrainingSession is a separate model from Event
                from apps.competitions.models.training import TrainingSession
                session = TrainingSession.objects.select_related(
                    'training_slot', 'training_slot__club', 'training_slot__discipline'
                ).get(id=event_id)
                slot = session.training_slot
                data = {
                    'id': session.id,
                    'type': 'training',
                    'title': slot.name if slot else 'Entraînement',
                    'name': slot.name if slot else 'Entraînement',
                    'date': session.date.isoformat() if session.date else None,
                    'start_date': session.date.isoformat() if session.date else None,
                    'end_date': session.date.isoformat() if session.date else None,
                    'start_time': slot.start_time.isoformat() if slot and slot.start_time else None,
                    'end_time': slot.end_time.isoformat() if slot and slot.end_time else None,
                    'location': session.location or (slot.club.name if slot and slot.club else 'Non spécifié'),
                    'address': '',
                    'description': slot.description if slot else '',
                    'event_type': 'training',
                    'price': 0,
                    'max_participants': slot.max_participants if slot else None,
                    'registration_required': False,
                    'is_registered': False,
                    'discipline': slot.discipline.name if slot and slot.discipline else '',
                    'organization': {
                        'id': slot.club.id,
                        'name': slot.club.name,
                    } if slot and slot.club else None,
                }

            elif event_type in ['club', 'event', 'seminar', 'meeting', 'social']:
                from apps.competitions.models.event import Event, EventParticipant

                event = Event.objects.select_related('organization').get(id=event_id)
                event_date = getattr(event, 'start_date', getattr(event, 'date', None))

                # Get participants count
                participants_count = 0
                try:
                    participants_count = event.participants.count()
                except Exception:
                    pass

                # Check if user is registered
                is_registered = False
                try:
                    is_registered = EventParticipant.objects.filter(
                        event=event,
                        user=user
                    ).exists()
                except Exception:
                    pass

                # Build image URL
                image_url = None
                if hasattr(event, 'image') and event.image:
                    image_url = request.build_absolute_uri(event.image.url)
                    if 'martialcomp.com' in image_url and image_url.startswith('http://'):
                        image_url = image_url.replace('http://', 'https://')

                # Récupérer les inscrits du club de l'utilisateur
                club_participants_data = []
                is_club_manager = False
                try:
                    from apps.competitions.utils.permission_helpers import get_user_club
                    from apps.competitions.models.practitioners import Practitioner
                    from django.db.models import Q
                    user_club = get_user_club(request)
                    if user_club:
                        is_club_manager = True
                        club_org = user_club.organization or getattr(user_club, 'as_organization', None)
                        if club_org:
                            club_user_ids = list(
                                Practitioner.objects.filter(
                                    organization=club_org,
                                    user__isnull=False
                                ).values_list('user_id', flat=True)
                            )
                            # Noms du club pour matcher les invités
                            club_names = [user_club.name]
                            if club_org.name and club_org.name != user_club.name:
                                club_names.append(club_org.name)
                            guest_q = Q()
                            for cn in club_names:
                                guest_q |= Q(is_guest=True, guest_club__iexact=cn)
                            club_regs = EventParticipant.objects.filter(
                                event=event
                            ).filter(
                                Q(practitioner__organization=club_org) |
                                Q(user_id__in=club_user_ids) |
                                guest_q
                            ).exclude(status='cancelled').select_related('practitioner', 'user').distinct()
                            for p in club_regs:
                                name = 'Invité'
                                practitioner_id = None
                                if p.practitioner:
                                    name = f"{p.practitioner.first_name} {p.practitioner.last_name}"
                                    practitioner_id = p.practitioner_id
                                elif p.user:
                                    pract = Practitioner.objects.filter(user=p.user, organization=club_org).first()
                                    if pract:
                                        name = f"{pract.first_name} {pract.last_name}"
                                        practitioner_id = pract.id
                                    else:
                                        name = p.user.get_full_name() or p.user.username
                                elif p.is_guest and (p.guest_first_name or p.guest_last_name):
                                    name = f"{p.guest_first_name or ''} {p.guest_last_name or ''}".strip()
                                club_participants_data.append({
                                    'id': p.id,
                                    'practitioner_id': practitioner_id,
                                    'name': name,
                                    'status': p.status,
                                    'status_display': p.get_status_display(),
                                    'role': getattr(p, 'role', 'participant'),
                                    'registered_at': p.registered_at.isoformat() if p.registered_at else None,
                                })
                except Exception:
                    pass

                data = {
                    'id': event.id,
                    'type': getattr(event, 'event_type', 'event'),
                    'title': getattr(event, 'title', getattr(event, 'name', 'Événement')),
                    'name': getattr(event, 'name', getattr(event, 'title', 'Événement')),
                    'date': event_date.isoformat() if event_date else None,
                    'start_date': event_date.isoformat() if event_date else None,
                    'end_date': event.end_date.isoformat() if hasattr(event, 'end_date') and event.end_date else None,
                    'start_time': event.start_time.isoformat() if hasattr(event, 'start_time') and event.start_time else None,
                    'end_time': event.end_time.isoformat() if hasattr(event, 'end_time') and event.end_time else None,
                    'location': getattr(event, 'location', getattr(event, 'city', 'Non spécifié')),
                    'address': getattr(event, 'address', ''),
                    'description': getattr(event, 'description', ''),
                    'event_type': getattr(event, 'event_type', ''),
                    'price': float(event.price) if hasattr(event, 'price') and event.price else 0,
                    'max_participants': getattr(event, 'max_participants', None),
                    'registration_required': getattr(event, 'registration_required', False),
                    'is_registered': is_registered,
                    'participants_count': participants_count,
                    'image': image_url,
                    'banner': image_url,
                    'organization': {
                        'id': event.organization.id,
                        'name': event.organization.name,
                        'logo': request.build_absolute_uri(event.organization.logo.url) if event.organization and hasattr(event.organization, 'logo') and event.organization.logo else None,
                    } if event.organization else None,
                    'is_club_manager': is_club_manager,
                    'can_edit': self._check_can_edit(user, event.organization, getattr(event, 'created_by', None)),
                    'is_owner': self._check_is_owner(user, getattr(event, 'created_by', None)),
                    'club_participants': club_participants_data,
                    'club_participants_count': len(club_participants_data),
                }

            else:
                return Response({'error': f'Type invalide: {event_type}'}, status=status.HTTP_400_BAD_REQUEST)

            return Response(data)

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"EventDetailAPIView error: {e}")
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class EventRegistrationAPIView(APIView):
    """
    API REST pour inscription/désinscription à un événement - Compatible JWT.
    POST /api/competitions/events/<id>/register/
    POST /api/competitions/events/<id>/unregister/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, event_id, action='register'):
        from apps.competitions.models.event import Event, EventParticipant
        import logging
        logger = logging.getLogger(__name__)

        try:
            event = Event.objects.get(id=event_id)
            user = request.user

            logger.info(f"EventRegistrationAPIView: {action} user={user.id} event={event_id}")

            if action == 'register':
                # Check if already registered
                existing = EventParticipant.objects.filter(event=event, user=user).first()
                if existing:
                    return Response({
                        'success': False,
                        'message': 'Vous êtes déjà inscrit à cet événement.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check registration deadline
                if event.registration_deadline and event.registration_deadline < timezone.now():
                    return Response({
                        'success': False,
                        'message': 'La date limite d\'inscription est dépassée.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Check max participants
                if event.max_participants:
                    current_count = EventParticipant.objects.filter(event=event).count()
                    if current_count >= event.max_participants:
                        return Response({
                            'success': False,
                            'message': 'Le nombre maximum de participants est atteint.'
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Create registration
                registration = EventParticipant.objects.create(
                    event=event,
                    user=user,
                    status='registered'
                )

                logger.info(f"EventRegistrationAPIView: Created registration {registration.id}")

                return Response({
                    'success': True,
                    'message': 'Inscription réussie.',
                    'registration_id': registration.id
                }, status=status.HTTP_201_CREATED)

            elif action == 'unregister':
                # Find and delete registration
                registration = EventParticipant.objects.filter(event=event, user=user).first()
                if not registration:
                    return Response({
                        'success': False,
                        'message': 'Vous n\'êtes pas inscrit à cet événement.'
                    }, status=status.HTTP_400_BAD_REQUEST)

                registration.delete()
                logger.info(f"EventRegistrationAPIView: Deleted registration for user={user.id} event={event_id}")

                return Response({
                    'success': True,
                    'message': 'Inscription annulée.'
                })

            else:
                return Response({
                    'success': False,
                    'message': f'Action invalide: {action}'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Événement non trouvé.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"EventRegistrationAPIView error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventDeleteAPIView(APIView):
    """
    API REST pour supprimer un événement - Compatible JWT.
    DELETE /api/competitions/events/<id>/delete/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def delete(self, request, event_id):
        from apps.competitions.models.event import Event
        import logging
        logger = logging.getLogger(__name__)

        try:
            event = Event.objects.get(id=event_id)
            user = request.user

            # Check permissions using same logic as EventDetailAPIView
            can_delete = EventDetailAPIView._check_can_edit(
                user, event.organization, getattr(event, 'created_by', None)
            )

            if not can_delete:
                return Response({
                    'success': False,
                    'message': "Vous n'avez pas les droits pour supprimer cet événement."
                }, status=status.HTTP_403_FORBIDDEN)

            event_title = event.title
            event.delete()
            logger.info(f"Event '{event_title}' (id={event_id}) deleted by user {user.id}")

            return Response({
                'success': True,
                'message': 'Événement supprimé avec succès.'
            })

        except Event.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Événement non trouvé.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"EventDeleteAPIView error: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EventDuplicateAPIView(APIView):
    """
    API REST pour dupliquer un événement ou une compétition - Compatible JWT.
    POST /api/competitions/event-duplicate/<event_type>/<event_id>/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, event_type, event_id):
        from django.db import transaction
        import logging
        logger = logging.getLogger(__name__)

        user = request.user

        try:
            if event_type == 'competition':
                from apps.competitions.models.competitions import Competition
                from apps.competitions.models.categories import CompetitionCategory
                source = Competition.objects.get(pk=event_id)

                can_edit = EventDetailAPIView._check_can_edit(
                    user,
                    source.organization if hasattr(source, 'organization') else source.organizing_organization,
                    getattr(source, 'created_by', None)
                )
                if not can_edit:
                    return Response({'success': False, 'message': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)

                with transaction.atomic():
                    source_types = list(source.competition_types.all())
                    source_categories = list(source.categories.all())

                    new_comp = Competition()
                    for field in ['description', 'start_date', 'end_date', 'start_time', 'end_time',
                                  'venue_name', 'address', 'city', 'postal_code', 'max_participants',
                                  'registration_deadline', 'logo', 'min_age', 'max_age',
                                  'requires_medical_certificate', 'requires_license', 'discipline',
                                  'organizing_organization', 'stream_enabled', 'stream_platform',
                                  'stream_url', 'stream_chat_enabled']:
                        if hasattr(source, field):
                            setattr(new_comp, field, getattr(source, field))
                    new_comp.title = f"{source.title} (Copie)"
                    new_comp.status = 'draft'
                    new_comp.is_published = False
                    new_comp.created_by = user
                    new_comp.slug = ''
                    new_comp.save()

                    new_comp.competition_types.set(source_types)

                    for cat in source_categories:
                        CompetitionCategory.objects.create(
                            competition=new_comp,
                            competition_type=cat.competition_type,
                            template=cat.template,
                            name=cat.name,
                            min_age=cat.min_age, max_age=cat.max_age,
                            min_grade=cat.min_grade, max_grade=cat.max_grade,
                            min_weight=cat.min_weight, max_weight=cat.max_weight,
                            gender=cat.gender,
                            max_participants=cat.max_participants,
                            combat_mode=cat.combat_mode,
                            estimated_duration=cat.estimated_duration,
                            registration_status='open',
                            is_completed=False,
                        )

                logger.info(f"Competition '{source.title}' duplicated as '{new_comp.title}' by user {user.id}")
                return Response({
                    'success': True,
                    'message': 'Compétition dupliquée avec succès.',
                    'new_id': new_comp.pk,
                    'new_event_id': f"comp_{new_comp.pk}",
                    'new_title': new_comp.title,
                })

            else:
                # Standard event (event, training, seminar, etc.)
                from apps.competitions.models.event import Event
                source = Event.objects.get(pk=event_id)

                can_edit = EventDetailAPIView._check_can_edit(
                    user, source.organization, getattr(source, 'created_by', None)
                )
                if not can_edit:
                    return Response({'success': False, 'message': "Permission refusée."}, status=status.HTTP_403_FORBIDDEN)

                new_event = Event()
                for field in ['description', 'event_type', 'organization', 'start_date', 'end_date',
                              'start_time', 'end_time', 'all_day', 'location', 'address', 'city',
                              'postal_code', 'visibility', 'is_public', 'max_participants',
                              'registration_required', 'registration_deadline', 'price',
                              'contact_email', 'contact_phone', 'color', 'image', 'event_format',
                              'online_url', 'online_platform', 'online_meeting_id', 'online_password',
                              'is_recurring', 'recurrence_frequency', 'recurrence_interval',
                              'recurrence_days', 'recurrence_day_of_month', 'recurrence_week_of_month',
                              'recurrence_end_type', 'recurrence_end_after', 'recurrence_end_date']:
                    if hasattr(source, field):
                        setattr(new_event, field, getattr(source, field))
                new_event.title = f"{source.title} (Copie)"
                new_event.is_cancelled = False
                new_event.is_archived = False
                new_event.created_by = user
                new_event.contact_person = user
                new_event.save()

                logger.info(f"Event '{source.title}' duplicated as '{new_event.title}' by user {user.id}")

                # Determine event type prefix for the mobile app
                type_prefix = source.event_type if source.event_type else 'event'
                return Response({
                    'success': True,
                    'message': 'Événement dupliqué avec succès.',
                    'new_id': new_event.pk,
                    'new_event_id': f"{type_prefix}_{new_event.pk}",
                    'new_title': new_event.title,
                })

        except Competition.DoesNotExist:
            return Response({'success': False, 'message': 'Compétition non trouvée.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            from apps.competitions.models.event import Event as EventModel
            if isinstance(e, EventModel.DoesNotExist):
                return Response({'success': False, 'message': 'Événement non trouvé.'}, status=status.HTTP_404_NOT_FOUND)
            logger.error(f"EventDuplicateAPIView error: {e}")
            return Response({'success': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


urlpatterns = [
    path('', CompetitionListView.as_view(), name='competitions_list'),
    path('upcoming/', CompetitionListView.as_view(), name='competitions_upcoming'),
    path('events/', PublicEventsView.as_view(), name='public_events'),
    path('generate-license-number/', generate_license_number, name='generate_license_number'),

    # Event detail API (JWT compatible)
    path('event-detail/<str:event_type>/<int:event_id>/', EventDetailAPIView.as_view(), name='event_detail_api'),

    # Event registration API (JWT compatible) - for mobile app
    path('events/<int:event_id>/register/', EventRegistrationAPIView.as_view(), {'action': 'register'}, name='event_register_api'),
    path('events/<int:event_id>/unregister/', EventRegistrationAPIView.as_view(), {'action': 'unregister'}, name='event_unregister_api'),
    path('events/<int:event_id>/delete/', EventDeleteAPIView.as_view(), name='event_delete_api'),
    path('event-duplicate/<str:event_type>/<int:event_id>/', EventDuplicateAPIView.as_view(), name='event_duplicate_api'),

    # Calendar API (Prompt 4) - Session based
    path('practitioner/calendar-events/', calendar_events_api, name='calendar_events'),
    path('practitioner/calendar-events/export.ics', export_calendar_ics, name='calendar_export_ics'),
    path('practitioner/calendar-events/<str:event_type>/<int:event_id>/', event_detail_api, name='calendar_event_detail'),
]
