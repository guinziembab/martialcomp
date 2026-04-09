"""
API endpoints pour le calendrier du pratiquant (Prompt 4).
"""

from datetime import datetime, date, timedelta
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.competitions.models import Practitioner
from apps.competitions.services.calendar_service import CalendarService


@method_decorator(login_required, name='dispatch')
class CalendarEventsAPIView(View):
    """
    API pour récupérer les événements du calendrier.

    GET /api/practitioner/calendar-events/
        ?start_date=2024-12-01
        &end_date=2024-12-31
        &types[]=competition&types[]=exam
        &disciplines[]=1&disciplines[]=2
        &include_registered_only=false
    """

    def get(self, request):
        try:
            # Récupérer le pratiquant de l'utilisateur
            practitioner = Practitioner.objects.filter(user=request.user).first()
            if not practitioner:
                return JsonResponse({
                    'error': _("Profil pratiquant non trouvé"),
                    'events': [],
                    'total': 0
                }, status=200)

            # Parser les paramètres
            start_date = self._parse_date(request.GET.get('start'), default_days_ago=0)
            end_date = self._parse_date(request.GET.get('end'), default_days_ahead=60)

            # Types d'événements
            types = request.GET.getlist('types[]') or request.GET.getlist('types')
            if not types:
                types = ['competition', 'exam', 'club', 'deadline']

            # Disciplines
            discipline_ids = request.GET.getlist('disciplines[]') or request.GET.getlist('disciplines')
            discipline_ids = [int(d) for d in discipline_ids if d.isdigit()] if discipline_ids else None

            # Inscriptions uniquement
            registered_only = request.GET.get('include_registered_only', 'false').lower() == 'true'

            # Récupérer les événements
            service = CalendarService(practitioner)
            events = service.get_events(
                start_date=start_date,
                end_date=end_date,
                types=types,
                discipline_ids=discipline_ids,
                include_registered_only=registered_only
            )

            # Convertir en format FullCalendar
            events_data = [event.to_dict() for event in events]

            return JsonResponse({
                'events': events_data,
                'total': len(events_data),
                'has_more': False,
                'filters': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'types': types,
                    'disciplines': discipline_ids,
                }
            })

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Calendar API error: {e}")
            return JsonResponse({
                'error': str(e),
                'events': [],
                'total': 0
            }, status=500)

    def _parse_date(self, date_str, default_days_ago=0, default_days_ahead=0):
        """Parse une date string ou retourne une date par défaut."""
        if date_str:
            try:
                # Essayer plusieurs formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        return datetime.strptime(date_str.split('T')[0], '%Y-%m-%d').date()
                    except ValueError:
                        continue
            except Exception:
                pass

        # Date par défaut
        today = timezone.now().date()
        if default_days_ago:
            return today - timedelta(days=default_days_ago)
        elif default_days_ahead:
            return today + timedelta(days=default_days_ahead)
        return today


@login_required
@require_GET
def calendar_events_api(request):
    """Function-based view wrapper pour l'API calendrier."""
    view = CalendarEventsAPIView.as_view()
    return view(request)


@login_required
@require_GET
def export_calendar_ics(request):
    """
    Exporte le calendrier au format ICS.

    GET /api/practitioner/calendar-events/export.ics
        ?start_date=2024-12-01
        &end_date=2024-12-31
        &types[]=competition
    """
    try:
        practitioner = Practitioner.objects.filter(user=request.user).first()
        if not practitioner:
            return HttpResponse("Profil pratiquant non trouvé", status=404)

        # Parser les paramètres
        start_date_str = request.GET.get('start')
        end_date_str = request.GET.get('end')

        today = timezone.now().date()
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else today
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today + timedelta(days=90)

        # Types
        types = request.GET.getlist('types[]') or request.GET.getlist('types')
        if not types:
            types = ['competition', 'exam', 'club']

        # Récupérer les événements
        service = CalendarService(practitioner)
        events = service.get_events(
            start_date=start_date,
            end_date=end_date,
            types=types
        )

        # Générer le fichier ICS
        ics_content = service.generate_ics(
            events,
            calendar_name=f"MartialComp - {practitioner.full_name}"
        )

        # Retourner le fichier
        response = HttpResponse(ics_content, content_type='text/calendar')
        response['Content-Disposition'] = f'attachment; filename="martialcomp_calendar.ics"'
        return response

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"ICS export error: {e}")
        return HttpResponse(f"Erreur: {e}", status=500)


@login_required
@require_GET
def event_detail_api(request, event_type, event_id):
    """
    Récupère les détails d'un événement spécifique.

    GET /api/practitioner/calendar-events/<type>/<id>/
    """
    try:
        data = {}

        if event_type == 'competition':
            from apps.competitions.models import Competition, CompetitionRegistration

            comp = Competition.objects.select_related('discipline').get(id=event_id)
            is_registered = CompetitionRegistration.objects.filter(
                practitioner__user=request.user,
                competition=comp,
                status__in=['confirmed', 'pending']
            ).exists()

            data = {
                'id': comp.id,
                'type': 'competition',
                'title': comp.title,
                'date': comp.start_date.isoformat(),
                'start_time': comp.start_time.isoformat() if comp.start_time else None,
                'end_time': comp.end_time.isoformat() if hasattr(comp, 'end_time') and comp.end_time else None,
                'location': comp.location if hasattr(comp, 'location') else '',
                'discipline': comp.discipline.name if comp.discipline else '',
                'description': comp.description if hasattr(comp, 'description') else '',
                'registration_deadline': comp.registration_deadline.isoformat() if hasattr(comp, 'registration_deadline') and comp.registration_deadline else None,
                'registration_fee': str(comp.registration_fee) if hasattr(comp, 'registration_fee') and comp.registration_fee else None,
                'is_registered': is_registered,
                'registration_open': comp.registration_deadline >= timezone.now().date() if hasattr(comp, 'registration_deadline') and comp.registration_deadline else True,
                'categories': list(comp.categories.values_list('name', flat=True)) if hasattr(comp, 'categories') else [],
                'url': f"/competitions/competitions/{comp.id}/",
            }

        elif event_type == 'exam':
            from apps.grades.models import GradeExam, GradeExamRegistration

            exam = GradeExam.objects.select_related('discipline').get(id=event_id)
            is_registered = False
            try:
                is_registered = GradeExamRegistration.objects.filter(
                    practitioner__user=request.user,
                    exam=exam,
                    status__in=['registered', 'confirmed']
                ).exists()
            except Exception:
                pass

            data = {
                'id': exam.id,
                'type': 'exam',
                'title': exam.title,
                'date': exam.date.isoformat(),
                'start_time': exam.start_time.isoformat() if hasattr(exam, 'start_time') and exam.start_time else None,
                'end_time': exam.end_time.isoformat() if hasattr(exam, 'end_time') and exam.end_time else None,
                'location': exam.location if hasattr(exam, 'location') else '',
                'discipline': exam.discipline.name if exam.discipline else '',
                'registration_deadline': exam.registration_deadline.isoformat() if exam.registration_deadline else None,
                'fee': str(exam.fee) if hasattr(exam, 'fee') and exam.fee else None,
                'is_registered': is_registered,
                'registration_open': exam.registration_deadline >= timezone.now().date() if exam.registration_deadline else True,
                'available_grades': list(exam.available_grades.values_list('name', flat=True)) if hasattr(exam, 'available_grades') else [],
                'examiner': exam.examiner if hasattr(exam, 'examiner') else '',
                'url': reverse('grades:exam_detail', kwargs={'pk': exam.id}),
            }

        elif event_type == 'club':
            from apps.competitions.models import Event

            event = Event.objects.get(id=event_id)
            data = {
                'id': event.id,
                'type': 'club',
                'title': event.title,
                'date': event.date.isoformat(),
                'start_time': event.start_time.isoformat() if hasattr(event, 'start_time') and event.start_time else None,
                'end_time': event.end_time.isoformat() if hasattr(event, 'end_time') and event.end_time else None,
                'location': event.location if hasattr(event, 'location') else '',
                'description': event.description if hasattr(event, 'description') else '',
                'event_type': event.event_type if hasattr(event, 'event_type') else '',
                'url': f"/competitions/events/{event.id}/",
            }

        else:
            return JsonResponse({'error': 'Type invalide'}, status=400)

        return JsonResponse(data)

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Event detail API error: {e}")
        return JsonResponse({'error': str(e)}, status=404)
