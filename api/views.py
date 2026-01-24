from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from datetime import datetime
from django.conf import settings
from apps.grades.services import CertificateNumberGenerator
from apps.competitions.services import LicenseNumberGenerator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@csrf_exempt
def generate_certificate_number(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        discipline_id = data.get('discipline_id')
        organization_id = data.get('organization_id')
        birth_date = data.get('birth_date')
        certificate_number = CertificateNumberGenerator.generate(
            discipline_id=discipline_id,
            organization_id=organization_id,
            birth_date=birth_date
        )
        return JsonResponse({'certificate_number': certificate_number})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
def generate_license_number(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    try:
        data = json.loads(request.body.decode('utf-8'))
        discipline_id = data.get('discipline_id')
        club_id = data.get('club_id')
        birth_date = data.get('birth_date')
        license_number = LicenseNumberGenerator.generate(
            discipline_id=discipline_id,
            club_id=club_id,
            birth_date=birth_date
        )
        return JsonResponse({'license_number': license_number})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400) 


def health(request):
    """Simple health check endpoint for mobile/web clients."""
    return JsonResponse({
        'status': 'ok',
        'time': datetime.utcnow().isoformat() + 'Z',
        'environment': getattr(settings, 'ENVIRONMENT', 'development'),
    })


def info(request):
    """Basic info endpoint to expose minimal runtime details."""
    return JsonResponse({
        'app': 'MartialComp',
        'version': getattr(settings, 'APP_VERSION', 'dev'),
        'debug': getattr(settings, 'DEBUG', False),
    })


def recent_notifications(request):
    """Return a small list of recent notifications (placeholder)."""
    data = [
        { 'id': 1, 'title': 'Bienvenue sur MartialComp', 'message': 'Votre compte est prêt.', 'type': 'system' },
        { 'id': 2, 'title': 'Événement', 'message': 'Nouvelle compétition publiée.', 'type': 'competition' },
        { 'id': 3, 'title': 'Paiement', 'message': 'Paiement enregistré.', 'type': 'payment' },
    ]
    return JsonResponse({'notifications': data})


class MobileDashboardView(APIView):
    """Mobile dashboard endpoint returning comprehensive club statistics.

    Returns statistics for:
    - Practitioners count
    - Active competitions
    - Active registrations
    - Judges/Referees count
    - Financial summary
    - Upcoming competitions
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = getattr(request, 'user', None)

        # Get organization from various sources
        organization = None

        # 0. PRIORITY: Try via X-Tenant-ID header (sent by mobile app)
        tenant_id = request.META.get('HTTP_X_TENANT_ID') or request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                from apps.organizations.models import Organization
                org_by_tenant = Organization.objects.filter(id=tenant_id).first()
                if org_by_tenant:
                    organization = org_by_tenant
                    print(f"DEBUG Mobile Dashboard: Found organization via X-Tenant-ID header: {organization.name} (id={organization.id})")
            except Exception as e:
                print(f"Error getting organization from X-Tenant-ID: {e}")

        if user and not organization:
            # 1. Try via UserProfile (most common case for club managers)
            try:
                from apps.competitions.models import UserProfile
                profile = UserProfile.objects.filter(user=user).select_related('organization').first()
                if profile and profile.organization:
                    organization = profile.organization
                    print(f"DEBUG Mobile Dashboard: Found organization via UserProfile: {organization.name} (id={organization.id})")
            except Exception as e:
                print(f"Error getting UserProfile organization: {e}")

            # 2. Try direct organization attribute on user
            if not organization:
                organization = getattr(user, 'organization', None)
                if organization:
                    print(f"DEBUG Mobile Dashboard: Found organization via user.organization: {organization.name}")

            # 3. Try via practitioner relationship
            if not organization:
                try:
                    from apps.competitions.models import Practitioner
                    practitioner = Practitioner.objects.filter(user=user).select_related('organization').first()
                    if practitioner:
                        organization = getattr(practitioner, 'organization', None) or getattr(practitioner, 'club', None)
                        if organization:
                            print(f"DEBUG Mobile Dashboard: Found organization via Practitioner: {organization.name}")
                except Exception as e:
                    print(f"Error getting practitioner for user: {e}")

            # 4. Try via OrganizationMember (newer model)
            if not organization:
                try:
                    from apps.organizations.models import OrganizationMember
                    membership = OrganizationMember.objects.filter(user=user, is_active=True).select_related('organization').first()
                    if membership and membership.organization:
                        organization = membership.organization
                        print(f"DEBUG Mobile Dashboard: Found organization via OrganizationMember: {organization.name}")
                except Exception as e:
                    print(f"Error getting OrganizationMember: {e}")

            # 5. Try via old Membership model (for compatibility)
            if not organization:
                try:
                    from apps.organizations.models import Membership
                    membership = Membership.objects.filter(user=user, is_active=True).select_related('organization').first()
                    if membership and membership.organization:
                        organization = membership.organization
                        print(f"DEBUG Mobile Dashboard: Found organization via Membership: {organization.name}")
                except Exception as e:
                    print(f"Error getting membership for user: {e}")

            # 6. Try via managed clubs (managers M2M field)
            if not organization:
                try:
                    from apps.organizations.models import Organization
                    managed_org = Organization.objects.filter(managers=user).first()
                    if managed_org:
                        organization = managed_org
                        print(f"DEBUG Mobile Dashboard: Found organization via managers: {managed_org.name}")
                except Exception as e:
                    print(f"Error getting managed organization: {e}")

            # 7. Try via created_by field
            if not organization:
                try:
                    from apps.organizations.models import Organization
                    created_org = Organization.objects.filter(created_by=user).first()
                    if created_org:
                        organization = created_org
                        print(f"DEBUG Mobile Dashboard: Found organization via created_by: {created_org.name}")
                except Exception as e:
                    print(f"Error getting created organization: {e}")

            if not organization:
                print(f"DEBUG Mobile Dashboard: No organization found for user {user.username} (id={user.id})")

        # Build statistics
        statistics = self._get_statistics(user, organization)

        # Build modules list (features enabled for this user/org)
        modules = self._get_modules(user, organization)

        # Get upcoming competitions
        upcoming_competitions = self._get_upcoming_competitions(organization)

        # Get practitioner info for the user (needed for attendance, etc.)
        practitioner_id = None
        practitioner_name = None
        if user:
            try:
                from apps.competitions.models import Practitioner
                practitioner = Practitioner.objects.filter(user=user).first()
                if practitioner:
                    practitioner_id = practitioner.id
                    practitioner_name = practitioner.full_name
            except Exception as e:
                print(f"Error getting practitioner for dashboard: {e}")

        return Response({
            'role': getattr(user, 'role', 'guest') if user else 'guest',
            'practitioner_id': practitioner_id,
            'practitioner_name': practitioner_name,
            'organization': {
                'id': str(getattr(organization, 'id', '')),
                'name': getattr(organization, 'name', ''),
                'type': getattr(organization, 'organization_type', 'club'),
                'logo_url': getattr(organization, 'logo_url', None) if organization else None,
            } if organization else None,
            'statistics': statistics,
            'modules': modules,
            'upcoming_competitions': upcoming_competitions,
            'capabilities': getattr(user, 'permissions', []) if user and hasattr(user, 'permissions') else [],
        })

    def _get_statistics(self, user, organization):
        """Get comprehensive statistics for the dashboard."""
        stats = {
            'practitioners_count': 0,
            'active_registrations': 0,
            'organized_competitions': 0,
            'judges_referees': 0,
        }

        try:
            from apps.competitions.models import Practitioner, Competition, Judge
            from django.db.models import Q

            # Filter by organization if available
            if organization:
                org_id = organization.id

                # Practitioners count - Practitioner has 'organization' field (not club_id)
                try:
                    stats['practitioners_count'] = Practitioner.objects.filter(
                        organization_id=org_id
                    ).count()
                except Exception as e:
                    print(f"Error counting practitioners: {e}")
                    stats['practitioners_count'] = 0

                # Organized competitions - Competition uses 'organizing_organization'
                try:
                    stats['organized_competitions'] = Competition.objects.filter(
                        organizing_organization_id=org_id
                    ).count()
                except Exception as e:
                    print(f"Error counting competitions: {e}")
                    stats['organized_competitions'] = 0

                # Active registrations - use CompetitionRegistration model
                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    stats['active_registrations'] = CompetitionRegistration.objects.filter(
                        Q(competition__organizing_organization_id=org_id) | Q(practitioner__organization_id=org_id),
                        status__in=['pending', 'confirmed', 'validated', 'registered']
                    ).count()
                except Exception as e:
                    print(f"Error counting registrations: {e}")
                    stats['active_registrations'] = 0

                # Judges/Referees - Judge has 'organization' and 'practitioner' fields
                try:
                    stats['judges_referees'] = Judge.objects.filter(
                        Q(practitioner__organization_id=org_id) | Q(organization_id=org_id),
                        active=True
                    ).count()
                except Exception as e:
                    print(f"Error counting judges: {e}")
                    try:
                        stats['judges_referees'] = Judge.objects.filter(
                            organization_id=org_id,
                            active=True
                        ).count()
                    except Exception:
                        stats['judges_referees'] = 0
            else:
                # No organization - return 0s (don't show global stats)
                # This is important for data isolation
                print(f"DEBUG: No organization found for user, returning zero stats")

        except ImportError as e:
            print(f"Import error in statistics: {e}")
        except Exception as e:
            print(f"Error getting statistics: {e}")

        return stats

    def _get_modules(self, user, organization):
        """Get list of enabled modules/features."""
        # Default modules available
        modules = [
            {'id': 'dashboard', 'name': 'Tableau de bord', 'enabled': True, 'icon': 'view-dashboard'},
            {'id': 'practitioners', 'name': 'Pratiquants', 'enabled': True, 'icon': 'account-group'},
            {'id': 'competitions', 'name': 'Compétitions', 'enabled': True, 'icon': 'trophy'},
            {'id': 'finances', 'name': 'Finances', 'enabled': True, 'icon': 'cash'},
            {'id': 'grades', 'name': 'Grades', 'enabled': True, 'icon': 'certificate'},
            {'id': 'documents', 'name': 'Documents', 'enabled': True, 'icon': 'file-document'},
            {'id': 'qr_scanner', 'name': 'Scanner QR', 'enabled': True, 'icon': 'qrcode-scan'},
        ]

        # Check subscription for premium features
        if organization:
            subscription = getattr(organization, 'subscription', None)
            if subscription:
                plan = getattr(subscription, 'plan', None)
                if plan:
                    plan_code = getattr(plan, 'code', 'essentials')
                    if plan_code in ['masters', 'champion']:
                        modules.append({'id': 'shop', 'name': 'Boutique', 'enabled': True, 'icon': 'cart'})
                        modules.append({'id': 'analytics', 'name': 'Statistiques', 'enabled': True, 'icon': 'chart-line'})

        return modules

    def _get_upcoming_competitions(self, organization):
        """Get list of upcoming competitions."""
        competitions = []

        try:
            from apps.competitions.models import Competition
            from django.utils import timezone
            from django.db.models import Q

            now = timezone.now()
            qs = Competition.objects.filter(start_date__gte=now).order_by('start_date')[:5]

            if organization:
                # Filter by organization
                qs = qs.filter(
                    Q(organization_id=organization.id) | Q(club_id=organization.id) | Q(is_public=True)
                )

            for comp in qs:
                competitions.append({
                    'id': str(comp.id),
                    'name': comp.name,
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if comp.end_date else None,
                    'location': getattr(comp, 'location', '') or getattr(comp, 'venue', '') or '',
                    'status': 'upcoming',
                })
        except ImportError:
            pass
        except Exception as e:
            print(f"Error getting competitions: {e}")

        return competitions


class PractitionerDashboardView(APIView):
    """
    Dashboard spécifique pour les pratiquants (participants).

    Retourne des données différentes de celles d'un admin ou d'un juge:
    - Prochaines compétitions auxquelles le pratiquant peut s'inscrire
    - Inscriptions en cours du pratiquant
    - Historique des combats et résultats
    - Progression de grade
    - Événements du calendrier personnel
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        # Récupérer le pratiquant lié à l'utilisateur
        practitioner = None
        try:
            from apps.competitions.models import Practitioner
            practitioner = Practitioner.objects.filter(user=user).select_related(
                'organization', 'club'
            ).first()
        except Exception as e:
            print(f"Error getting practitioner: {e}")

        if not practitioner:
            return Response({
                'error': 'no_practitioner',
                'message': 'Aucun profil pratiquant trouvé pour cet utilisateur',
                'dashboard_type': 'participant',
            }, status=200)

        # Récupérer l'organisation
        organization = getattr(practitioner, 'organization', None) or getattr(practitioner, 'club', None)

        # Construire la réponse spécifique au pratiquant
        # Récupérer les événements unifiés (compétitions + événements club)
        unified_events = self._get_unified_events(practitioner)

        response_data = {
            'dashboard_type': 'participant',
            'practitioner': self._get_practitioner_info(practitioner),
            'upcoming_competitions': self._get_upcoming_competitions(practitioner),
            # NOUVEAU: événements unifiés pour l'écran "Événements" de l'app mobile
            'upcoming_events': unified_events,
            'events': unified_events,  # Alias pour compatibilité
            'my_registrations': self._get_my_registrations(practitioner),
            'combat_stats': self._get_combat_stats(practitioner),
            'grade_progress': self._get_grade_progress(practitioner),
            'calendar_events': self._get_calendar_events(practitioner),
            'notifications_count': self._get_notifications_count(user),
        }

        return Response(response_data)

    def _get_practitioner_info(self, practitioner):
        """Informations de base du pratiquant."""
        return {
            'id': str(practitioner.id),
            'full_name': f"{practitioner.first_name} {practitioner.last_name}".strip(),
            'license_number': getattr(practitioner, 'license_number', None),
            'photo_url': practitioner.photo.url if hasattr(practitioner, 'photo') and practitioner.photo else None,
            'organization': {
                'id': str(practitioner.organization.id) if practitioner.organization else None,
                'name': practitioner.organization.name if practitioner.organization else None,
            } if practitioner.organization else None,
        }

    def _get_upcoming_competitions(self, practitioner):
        """Compétitions à venir auxquelles le pratiquant peut s'inscrire."""
        competitions = []
        try:
            from apps.competitions.models import Competition
            from django.utils import timezone
            from django.db.models import Q

            # Compétitions publiées à venir
            qs = Competition.objects.filter(
                status__in=['published', 'open', 'registration_open'],
                start_date__gte=timezone.now().date()
            ).order_by('start_date')[:10]

            # Filtrer par discipline si le pratiquant en a une
            if hasattr(practitioner, 'disciplines') and practitioner.disciplines.exists():
                discipline_ids = list(practitioner.disciplines.values_list('id', flat=True))
                qs = qs.filter(Q(discipline_id__in=discipline_ids) | Q(discipline__isnull=True))

            for comp in qs:
                # Vérifier si déjà inscrit
                is_registered = False
                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    is_registered = CompetitionRegistration.objects.filter(
                        competition=comp,
                        practitioner=practitioner
                    ).exists()
                except Exception:
                    pass

                competitions.append({
                    'id': str(comp.id),
                    'name': comp.name,
                    'title': getattr(comp, 'title', comp.name),
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if comp.end_date else None,
                    'location': getattr(comp, 'location', '') or getattr(comp, 'venue', ''),
                    'discipline': comp.discipline.name if comp.discipline else None,
                    'registration_deadline': comp.registration_deadline.isoformat() if comp.registration_deadline else None,
                    'is_registered': is_registered,
                    'registration_open': comp.status in ['open', 'registration_open', 'published'],
                })
        except Exception as e:
            print(f"Error getting upcoming competitions: {e}")

        return competitions

    def _get_my_registrations(self, practitioner):
        """Inscriptions en cours du pratiquant."""
        registrations = []
        try:
            from apps.competitions.models.registrations import CompetitionRegistration
            from django.utils import timezone

            qs = CompetitionRegistration.objects.filter(
                practitioner=practitioner,
                competition__start_date__gte=timezone.now().date()
            ).select_related('competition', 'category').order_by('competition__start_date')[:10]

            for reg in qs:
                registrations.append({
                    'id': str(reg.id),
                    'competition': {
                        'id': str(reg.competition.id),
                        'name': reg.competition.name,
                        'start_date': reg.competition.start_date.isoformat() if reg.competition.start_date else None,
                        'location': getattr(reg.competition, 'location', ''),
                    },
                    'category': reg.category.name if reg.category else None,
                    'status': reg.status,
                    'registered_at': reg.created_at.isoformat() if hasattr(reg, 'created_at') and reg.created_at else None,
                })
        except Exception as e:
            print(f"Error getting registrations: {e}")

        return registrations

    def _get_combat_stats(self, practitioner):
        """Statistiques de combat du pratiquant."""
        stats = {
            'total_combats': 0,
            'victories': 0,
            'defeats': 0,
            'draws': 0,
            'win_rate': 0.0,
            'recent_combats': [],
        }

        try:
            from apps.competitions.models import Combat
            from django.db.models import Q

            # Combats où le pratiquant est participant
            combats = Combat.objects.filter(
                Q(participant1__user=practitioner.user) | Q(participant2__user=practitioner.user),
                status='completed'
            ).select_related('participant1', 'participant2', 'winner', 'competition').order_by('-date_time')

            stats['total_combats'] = combats.count()

            for combat in combats[:5]:  # 5 derniers combats
                is_participant1 = combat.participant1 and combat.participant1.user == practitioner.user
                opponent = combat.participant2 if is_participant1 else combat.participant1
                is_winner = combat.winner and combat.winner.user == practitioner.user
                is_draw = combat.winner is None and combat.status == 'completed'

                if is_winner:
                    stats['victories'] += 1
                elif is_draw:
                    stats['draws'] += 1
                else:
                    stats['defeats'] += 1

                stats['recent_combats'].append({
                    'id': str(combat.id),
                    'opponent': f"{opponent.first_name} {opponent.last_name}".strip() if opponent else 'Inconnu',
                    'result': 'victory' if is_winner else ('draw' if is_draw else 'defeat'),
                    'score': f"{combat.score1 or 0} - {combat.score2 or 0}" if is_participant1 else f"{combat.score2 or 0} - {combat.score1 or 0}",
                    'competition': combat.competition.name if combat.competition else None,
                    'date': combat.date_time.isoformat() if combat.date_time else None,
                })

            if stats['total_combats'] > 0:
                stats['win_rate'] = round((stats['victories'] / stats['total_combats']) * 100, 1)

        except Exception as e:
            print(f"Error getting combat stats: {e}")

        return stats

    def _get_grade_progress(self, practitioner):
        """Progression de grade du pratiquant."""
        progress = {
            'current_grade': None,
            'next_grade': None,
            'progress_percentage': 0,
            'eligible_date': None,
            'is_eligible': False,
            'status': 'EN PROGRESSION',
            'disciplines': [],
        }

        try:
            from apps.grades.models import PractitionerGrade, Grade
            from datetime import date

            # Récupérer les grades du pratiquant par discipline
            practitioner_grades = PractitionerGrade.objects.filter(
                practitioner=practitioner
            ).select_related('grade', 'grade__discipline').order_by('-grade__level')

            for pg in practitioner_grades:
                if pg.grade and pg.grade.discipline:
                    # Calculate progression percentage and eligibility
                    progress_percent = 0
                    is_eligible = False
                    next_grade_data = None

                    # Trouver le grade suivant
                    try:
                        next_grade = Grade.objects.filter(
                            discipline=pg.grade.discipline,
                            level__gt=pg.grade.level
                        ).order_by('level').first()

                        if next_grade:
                            next_grade_data = {
                                'id': next_grade.id,
                                'name': next_grade.name,
                                'level': next_grade.level,
                                'color': getattr(next_grade, 'color', '#000000'),
                            }

                            # Calculate progression based on minimum_months_at_grade
                            min_months = getattr(next_grade, 'minimum_months_at_grade', 0) or 0
                            if min_months > 0 and pg.date_obtained:
                                months_at_grade = (date.today() - pg.date_obtained).days / 30.0
                                progress_percent = min(100, int((months_at_grade / min_months) * 100))
                                is_eligible = months_at_grade >= min_months
                            else:
                                # Default: assume eligible after getting current grade
                                progress_percent = 100
                                is_eligible = True
                        else:
                            # No next grade = max grade reached
                            progress_percent = 100
                            is_eligible = True
                    except Exception:
                        pass

                    disc_data = {
                        'discipline': {
                            'id': pg.grade.discipline.id,
                            'name': pg.grade.discipline.name,
                        },
                        'current_grade': {
                            'id': pg.grade.id,
                            'name': pg.grade.name,
                            'level': pg.grade.level,
                            'color': getattr(pg.grade, 'color', '#000000'),
                        },
                        'date_obtained': pg.date_obtained.isoformat() if pg.date_obtained else None,
                        'next_grade': next_grade_data,
                        'progress_percentage': progress_percent,
                        'is_eligible': is_eligible,
                        'status': 'ELIGIBLE' if is_eligible else 'EN PROGRESSION',
                    }

                    progress['disciplines'].append(disc_data)

            # Définir le grade principal (premier trouvé)
            if progress['disciplines']:
                main = progress['disciplines'][0]
                progress['current_grade'] = main['current_grade']
                progress['next_grade'] = main['next_grade']
                progress['progress_percentage'] = main['progress_percentage']
                progress['is_eligible'] = main['is_eligible']
                progress['status'] = main['status']

        except Exception as e:
            print(f"Error getting grade progress: {e}")

        return progress

    def _get_calendar_events(self, practitioner):
        """Événements du calendrier personnel."""
        events = []
        try:
            from apps.competitions.services.calendar_service import CalendarService
            from datetime import date, timedelta

            service = CalendarService(practitioner)
            start_date = date.today()
            end_date = start_date + timedelta(days=30)

            calendar_events = service.get_events(
                start_date=start_date,
                end_date=end_date,
                types=['competition', 'exam', 'club'],
                max_events=6
            )

            for ev in calendar_events:
                events.append({
                    'id': ev.id,
                    'type': ev.type,
                    'title': ev.title,
                    'start': ev.start.isoformat() if ev.start else None,
                    'end': ev.end.isoformat() if ev.end else None,
                    'location': ev.location,
                    'color': ev.color,
                    'url': ev.url,
                })
        except Exception as e:
            print(f"Error getting calendar events: {e}")

        return events

    def _get_notifications_count(self, user):
        """Nombre de notifications non lues."""
        try:
            from apps.competitions.models import Notification
            return Notification.objects.filter(user=user, read=False).count()
        except Exception:
            return 0

    def _get_unified_events(self, practitioner):
        """
        Événements unifiés: compétitions + événements du club.

        Cette méthode combine les compétitions et les événements du club
        pour l'écran "Événements" de l'application mobile.
        """
        events = []
        today = timezone.now().date()

        # 1. Récupérer les compétitions
        try:
            from apps.competitions.models import Competition
            from django.db.models import Q

            qs = Competition.objects.filter(
                status__in=['published', 'open', 'registration_open'],
                start_date__gte=today
            ).select_related('discipline').order_by('start_date')[:20]

            # Filtrer par discipline si le pratiquant en a une
            if hasattr(practitioner, 'disciplines') and practitioner.disciplines.exists():
                discipline_ids = list(practitioner.disciplines.values_list('id', flat=True))
                qs = qs.filter(Q(discipline_id__in=discipline_ids) | Q(discipline__isnull=True))

            for comp in qs:
                # Vérifier si inscrit
                is_registered = False
                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    is_registered = CompetitionRegistration.objects.filter(
                        competition=comp,
                        practitioner=practitioner
                    ).exists()
                except Exception:
                    pass

                events.append({
                    'id': f'competition_{comp.id}',
                    'type': 'competition',
                    'title': comp.name or getattr(comp, 'title', ''),
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if comp.end_date else None,
                    'location': getattr(comp, 'location', '') or getattr(comp, 'venue', ''),
                    'discipline': comp.discipline.name if comp.discipline else None,
                    'is_registered': is_registered,
                    'status': 'upcoming',
                    'color': '#3498db',
                })
        except Exception as e:
            print(f"Error getting competitions for unified events: {e}")

        # 2. Récupérer les événements du club
        try:
            from apps.competitions.models import Event
            from django.db.models import Q

            # Récupérer l'organisation
            organization = None
            if practitioner.club:
                organization = getattr(practitioner.club, 'organization', None)
            if not organization:
                organization = practitioner.organization

            if not organization:
                # Essayer via OrganizationMember
                try:
                    from apps.organizations.models import OrganizationMember
                    membership = OrganizationMember.objects.filter(
                        user=practitioner.user,
                        is_active=True
                    ).first()
                    if membership:
                        organization = membership.organization
                except Exception:
                    pass

            if organization:
                club_events = Event.objects.filter(
                    organization=organization,
                    start_date__gte=today,
                    is_cancelled=False,
                    is_archived=False
                ).filter(
                    Q(visibility='public') | Q(visibility='members') | Q(is_public=True)
                ).order_by('start_date')[:20]

                for event in club_events:
                    events.append({
                        'id': f'club_{event.id}',
                        'type': 'club',
                        'title': event.title,
                        'start_date': event.start_date.isoformat() if event.start_date else None,
                        'end_date': event.end_date.isoformat() if event.end_date else None,
                        'start_time': event.start_time.isoformat() if event.start_time else None,
                        'location': event.location or '',
                        'description': event.description or '',
                        'organization': organization.name if organization else '',
                        'status': 'upcoming',
                        'color': '#2ecc71',
                    })
        except Exception as e:
            print(f"Error getting club events for unified events: {e}")
            import traceback
            traceback.print_exc()

        # Trier par date
        events.sort(key=lambda x: x.get('start_date') or '9999-12-31')

        return events


# =============================================================================
# NOTIFICATIONS API
# =============================================================================

class NotificationsAPIView(APIView):
    """
    API REST pour les notifications mobiles.

    GET /api/notifications/
        ?page=1
        &limit=20
        &unread_only=false

    Retourne:
        - notifications: liste des notifications
        - total: nombre total
        - unread: nombre non lues
        - hasMore: s'il y a plus de pages
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

        try:
            from apps.competitions.models.notifications import Notification

            # Query de base
            qs = Notification.objects.filter(user=user).order_by('-created_at')

            # Filtrer par non-lu si demandé
            if unread_only:
                qs = qs.filter(is_read=False)

            # Comptages
            total = qs.count()
            unread_count = Notification.objects.filter(user=user, is_read=False).count()

            # Pagination
            offset = (page - 1) * limit
            notifications_qs = qs[offset:offset + limit]
            has_more = (offset + limit) < total

            # Sérialiser
            notifications_data = []
            for notif in notifications_qs:
                notifications_data.append({
                    'id': str(notif.id),
                    'title': notif.title,
                    'message': notif.message,
                    'type': notif.notification_type,
                    'priority': notif.priority,
                    'is_read': notif.is_read,
                    'created_at': notif.created_at.isoformat() if notif.created_at else None,
                    'read_at': notif.read_at.isoformat() if notif.read_at else None,
                    'action_url': notif.action_url,
                    'action_text': notif.action_text,
                    'css_class': notif.css_class,
                    'icon_class': notif.icon_class,
                })

            return Response({
                'notifications': notifications_data,
                'total': total,
                'unread': unread_count,
                'hasMore': has_more,
                'has_next': has_more,
                'page': page,
                'limit': limit,
            })

        except Exception as e:
            import traceback
            print(f"Error in NotificationsAPIView: {e}")
            traceback.print_exc()
            return Response({
                'notifications': [],
                'total': 0,
                'unread': 0,
                'hasMore': False,
                'error': str(e)
            }, status=500)


class NotificationDetailAPIView(APIView):
    """
    Détail d'une notification.

    GET /api/notifications/{id}/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request, notification_id):
        user = request.user
        try:
            from apps.competitions.models.notifications import Notification

            notif = Notification.objects.filter(id=notification_id, user=user).first()
            if not notif:
                return Response({'error': 'Notification non trouvée'}, status=404)

            return Response({
                'id': str(notif.id),
                'title': notif.title,
                'message': notif.message,
                'type': notif.notification_type,
                'priority': notif.priority,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
                'read_at': notif.read_at.isoformat() if notif.read_at else None,
                'action_url': notif.action_url,
                'action_text': notif.action_text,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class NotificationMarkReadAPIView(APIView):
    """
    Marquer une ou plusieurs notifications comme lues.

    POST /api/notifications/mark-read/
        { "notificationIds": [1, 2, 3] } ou { "markAll": true }

    POST /api/notifications/mark-read/{id}/
        Marque une seule notification
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, notification_id=None):
        user = request.user
        try:
            from apps.competitions.models.notifications import Notification
            from django.utils import timezone

            if notification_id:
                # Marquer une seule notification
                notif = Notification.objects.filter(id=notification_id, user=user).first()
                if notif:
                    notif.mark_as_read()
                    return Response({'success': True, 'marked': 1})
                return Response({'error': 'Notification non trouvée'}, status=404)

            # Marquer plusieurs notifications
            data = request.data
            mark_all = data.get('markAll', False)
            notification_ids = data.get('notificationIds', [])

            if mark_all:
                count = Notification.objects.filter(user=user, is_read=False).update(
                    is_read=True,
                    read_at=timezone.now()
                )
                return Response({'success': True, 'marked': count})

            if notification_ids:
                count = Notification.objects.filter(
                    user=user,
                    id__in=notification_ids,
                    is_read=False
                ).update(
                    is_read=True,
                    read_at=timezone.now()
                )
                return Response({'success': True, 'marked': count})

            return Response({'success': True, 'marked': 0})

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class NotificationDeleteAPIView(APIView):
    """
    Supprimer une ou plusieurs notifications.

    POST /api/notifications/delete/
        { "notificationIds": [1, 2, 3] } ou { "deleteAll": true }
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        user = request.user
        try:
            from apps.competitions.models.notifications import Notification

            data = request.data
            delete_all = data.get('deleteAll', False)
            delete_read = data.get('delete_read', False)
            notification_ids = data.get('notificationIds', [])

            if delete_all:
                count, _ = Notification.objects.filter(user=user).delete()
                return Response({'success': True, 'deleted': count})

            if delete_read:
                count, _ = Notification.objects.filter(user=user, is_read=True).delete()
                return Response({'success': True, 'deleted': count})

            if notification_ids:
                count, _ = Notification.objects.filter(
                    user=user,
                    id__in=notification_ids
                ).delete()
                return Response({'success': True, 'deleted': count})

            return Response({'success': True, 'deleted': 0})

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class NotificationPreferencesAPIView(APIView):
    """
    Préférences de notification de l'utilisateur.

    GET /api/notifications/preferences/
    PUT /api/notifications/preferences/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        try:
            from apps.competitions.models.notifications import NotificationPreference

            prefs, _ = NotificationPreference.objects.get_or_create(user=user)

            return Response({
                'email_enabled': prefs.email_enabled,
                'sms_enabled': prefs.sms_enabled,
                'push_enabled': prefs.push_enabled,
                'competition_notifications': prefs.competition_notifications,
                'training_notifications': prefs.training_notifications,
                'grade_notifications': prefs.grade_notifications,
                'order_notifications': prefs.order_notifications,
                'membership_notifications': prefs.membership_notifications,
                'message_notifications': prefs.message_notifications,
                'system_notifications': prefs.system_notifications,
                'notification_frequency': prefs.notification_frequency,
                'quiet_hours_start': prefs.quiet_hours_start.isoformat() if prefs.quiet_hours_start else None,
                'quiet_hours_end': prefs.quiet_hours_end.isoformat() if prefs.quiet_hours_end else None,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def put(self, request):
        user = request.user
        try:
            from apps.competitions.models.notifications import NotificationPreference

            prefs, _ = NotificationPreference.objects.get_or_create(user=user)
            data = request.data

            # Mettre à jour les champs fournis
            for field in ['email_enabled', 'sms_enabled', 'push_enabled',
                         'competition_notifications', 'training_notifications',
                         'grade_notifications', 'order_notifications',
                         'membership_notifications', 'message_notifications',
                         'system_notifications', 'notification_frequency']:
                if field in data:
                    setattr(prefs, field, data[field])

            prefs.save()

            return Response({'success': True})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class PaymentMethodsView(APIView):
    """Basic list of payment methods for mobile app."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        return Response([
            {'id': 'card', 'name': 'Carte bancaire', 'enabled': True},
            {'id': 'paypal', 'name': 'PayPal', 'enabled': True},
            {'id': 'bank_transfer', 'name': 'Virement bancaire', 'enabled': False},
        ])


class MobileEventsListView(APIView):
    """
    Liste unifiée des événements pour l'application mobile.

    Retourne les compétitions ET les événements du club, alignés avec
    ce que le site web affiche dans le calendrier du dashboard participant.

    GET /api/v1/mobile/events/
        ?filter=upcoming|past|all (default: upcoming)
        &limit=20 (default: 20)
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from django.utils import timezone

        user = request.user
        filter_type = request.GET.get('filter', 'upcoming')
        limit = int(request.GET.get('limit', 20))

        # Récupérer le pratiquant
        practitioner = None
        try:
            from apps.competitions.models import Practitioner
            practitioner = Practitioner.objects.filter(user=user).select_related(
                'organization', 'club'
            ).first()
        except Exception as e:
            print(f"Error getting practitioner: {e}")

        # Si pas de pratiquant, essayer de créer un objet "pseudo-practitioner" pour les gestionnaires
        if not practitioner:
            # Vérifier si l'utilisateur est un gestionnaire via UserProfile ou OrganizationMember
            try:
                from apps.competitions.models import UserProfile
                profile = UserProfile.objects.filter(user=user).select_related('organization').first()
                if profile and profile.organization:
                    # Créer un objet temporaire avec les infos nécessaires
                    class PseudoPractitioner:
                        def __init__(self, user, organization):
                            self.user = user
                            self.organization = organization
                            self.club = None
                            self._cached_disciplines = None

                        @property
                        def disciplines(self):
                            """Retourne les disciplines de l'organisation."""
                            if self._cached_disciplines is not None:
                                return self._cached_disciplines
                            if self.organization:
                                return self.organization.disciplines
                            return None

                        def get_all_discipline_ids(self):
                            """
                            Récupère les IDs de disciplines de toutes les sources:
                            1. Organization.disciplines
                            2. Grades de l'utilisateur (PractitionerGrade)
                            """
                            discipline_ids = set()

                            # 1. Disciplines de l'organisation
                            if self.organization and hasattr(self.organization, 'disciplines'):
                                org_disc_ids = list(self.organization.disciplines.values_list('id', flat=True))
                                discipline_ids.update(org_disc_ids)

                            # 2. Disciplines via les grades de l'utilisateur
                            try:
                                from apps.grades.models import PractitionerGrade
                                from apps.competitions.models import Practitioner

                                # Chercher un pratiquant lié à cet utilisateur
                                pract = Practitioner.objects.filter(user=self.user).first()
                                if pract:
                                    grades = PractitionerGrade.objects.filter(
                                        practitioner=pract
                                    ).select_related('grade__discipline')
                                    for pg in grades:
                                        if pg.grade and pg.grade.discipline_id:
                                            discipline_ids.add(pg.grade.discipline_id)
                            except Exception as e:
                                print(f"PseudoPractitioner: Error getting grades disciplines: {e}")

                            return list(discipline_ids)

                    practitioner = PseudoPractitioner(user, profile.organization)
            except Exception as e:
                print(f"Error getting user profile: {e}")

        if not practitioner:
            return Response({
                'events': [],
                'filter': filter_type,
                'total': 0,
                'message': 'Aucun profil pratiquant trouvé'
            })

        events = []
        today = timezone.now().date()

        # 1. Récupérer les compétitions
        events.extend(self._get_competitions(practitioner, filter_type, today))

        # 2. Récupérer les événements du club (via CalendarService)
        events.extend(self._get_club_events(practitioner, filter_type, today))

        # Trier par date
        events.sort(key=lambda x: x.get('start_date') or '9999-12-31')

        # Filtrer selon le type
        if filter_type == 'upcoming':
            events = [e for e in events if (e.get('start_date') or '9999-12-31') >= today.isoformat()]
        elif filter_type == 'past':
            events = [e for e in events if (e.get('start_date') or '0000-01-01') < today.isoformat()]
            events.reverse()  # Plus récents d'abord

        # Limiter
        events = events[:limit]

        return Response({
            'events': events,
            'filter': filter_type,
            'total': len(events),
        })

    def _get_competitions(self, practitioner, filter_type, today):
        """Récupérer les compétitions."""
        competitions = []
        try:
            from apps.competitions.models import Competition
            from django.db.models import Q
            from datetime import timedelta

            qs = Competition.objects.filter(
                status__in=['published', 'open', 'registration_open', 'in_progress', 'completed']
            ).select_related('discipline', 'organizing_organization')

            # Filtrer par date selon le type
            if filter_type == 'upcoming':
                qs = qs.filter(start_date__gte=today)
            elif filter_type == 'past':
                qs = qs.filter(end_date__lt=today)

            # Filtrer par discipline du pratiquant ou de l'organisation
            discipline_ids = []

            # Méthode optimisée: utiliser get_all_discipline_ids() si disponible (PseudoPractitioner)
            if hasattr(practitioner, 'get_all_discipline_ids'):
                discipline_ids = practitioner.get_all_discipline_ids()

            # Sinon, utiliser la méthode classique
            if not discipline_ids:
                # 1. Disciplines du pratiquant
                if hasattr(practitioner, 'disciplines') and practitioner.disciplines and practitioner.disciplines.exists():
                    discipline_ids = list(practitioner.disciplines.values_list('id', flat=True))

            # 2. Disciplines de l'organisation (pour les gestionnaires de club)
            if not discipline_ids:
                org = None
                if practitioner.organization:
                    org = practitioner.organization
                elif hasattr(practitioner, 'club') and practitioner.club and practitioner.club.organization:
                    org = practitioner.club.organization

                # Essayer via OrganizationMember
                if not org:
                    try:
                        from apps.organizations.models import OrganizationMember
                        membership = OrganizationMember.objects.filter(
                            user=practitioner.user, is_active=True
                        ).select_related('organization').first()
                        if membership:
                            org = membership.organization
                    except Exception:
                        pass

                # Essayer via UserProfile
                if not org:
                    try:
                        from apps.competitions.models import UserProfile
                        profile = UserProfile.objects.filter(user=practitioner.user).select_related('organization').first()
                        if profile and profile.organization:
                            org = profile.organization
                    except Exception:
                        pass

                if org and hasattr(org, 'disciplines') and org.disciplines.exists():
                    discipline_ids = list(org.disciplines.values_list('id', flat=True))

            # Appliquer le filtre si des disciplines sont trouvées
            # Si aucune discipline n'est trouvée, ne pas afficher de compétitions (isolation des données)
            if discipline_ids:
                qs = qs.filter(Q(discipline_id__in=discipline_ids) | Q(discipline__isnull=True))
            else:
                # Pas de discipline = pas de compétitions affichées (isolation)
                return competitions

            qs = qs.order_by('start_date')[:30]

            for comp in qs:
                # Vérifier si inscrit
                is_registered = False
                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    is_registered = CompetitionRegistration.objects.filter(
                        competition=comp,
                        practitioner=practitioner
                    ).exists()
                except Exception:
                    pass

                competitions.append({
                    'id': f'competition_{comp.id}',
                    'type': 'competition',
                    'title': comp.name or comp.title,
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if comp.end_date else None,
                    'location': getattr(comp, 'location', '') or getattr(comp, 'venue', ''),
                    'discipline': comp.discipline.name if comp.discipline else None,
                    'status': comp.status,
                    'is_registered': is_registered,
                    'registration_deadline': comp.registration_deadline.isoformat() if comp.registration_deadline else None,
                    'color': '#3498db',  # Bleu pour compétitions
                    'url': f'/competitions/competitions/{comp.id}/',
                })

        except Exception as e:
            print(f"Error getting competitions: {e}")

        return competitions

    def _get_club_events(self, practitioner, filter_type, today):
        """Récupérer les événements du club/organisation."""
        events = []
        try:
            from apps.competitions.models import Event
            from django.db.models import Q
            from datetime import timedelta

            # Récupérer l'organisation
            organization = None
            if practitioner.club:
                organization = practitioner.club.organization
            if not organization and practitioner.organization:
                organization = practitioner.organization

            if not organization:
                # Essayer via OrganizationMember
                try:
                    from apps.organizations.models import OrganizationMember
                    membership = OrganizationMember.objects.filter(
                        user=practitioner.user,
                        is_active=True
                    ).first()
                    if membership:
                        organization = membership.organization
                except Exception:
                    pass

            if not organization:
                return events

            qs = Event.objects.filter(
                organization=organization,
                is_cancelled=False,
                is_archived=False
            ).filter(
                Q(visibility='public') | Q(visibility='members') | Q(is_public=True)
            )

            # Filtrer par date
            if filter_type == 'upcoming':
                qs = qs.filter(start_date__gte=today)
            elif filter_type == 'past':
                qs = qs.filter(end_date__lt=today)

            qs = qs.order_by('start_date')[:30]

            for event in qs:
                events.append({
                    'id': f'club_{event.id}',
                    'type': 'club',
                    'title': event.title,
                    'start_date': event.start_date.isoformat() if event.start_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'start_time': event.start_time.isoformat() if event.start_time else None,
                    'end_time': event.end_time.isoformat() if event.end_time else None,
                    'location': event.location or '',
                    'description': event.description or '',
                    'event_type': event.event_type or '',
                    'organization': organization.name if organization else '',
                    'color': '#2ecc71',  # Vert pour événements club
                    'url': f'/competitions/events/{event.id}/',
                })

        except Exception as e:
            print(f"Error getting club events: {e}")
            import traceback
            traceback.print_exc()

        return events


class MobilePalmaresView(APIView):
    """
    API endpoint pour le palmarès du pratiquant.

    Retourne les résultats de compétition (médailles, classements)
    alignés avec le dashboard web participant.

    GET /api/v1/mobile/palmares/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        # Récupérer le pratiquant
        practitioner = None
        try:
            from apps.competitions.models import Practitioner
            practitioner = Practitioner.objects.filter(user=user).select_related(
                'organization', 'club'
            ).first()
        except Exception as e:
            print(f"Error getting practitioner: {e}")

        if not practitioner:
            return Response({
                'results': [],
                'summary': None,
                'error': 'no_practitioner',
                'message': 'Aucun profil pratiquant trouvé'
            })

        # Récupérer les résultats
        results = self._get_results(practitioner)
        summary = self._get_summary(practitioner, results)
        achievements = self._get_achievements(practitioner)

        return Response({
            'results': results,
            'summary': summary,
            'achievements': achievements,
        })

    def _get_results(self, practitioner):
        """Récupérer les résultats de compétition du pratiquant."""
        results = []

        try:
            # Méthode 1: Via CompetitionRegistration avec place/ranking
            from apps.competitions.models.registrations import CompetitionRegistration

            registrations = CompetitionRegistration.objects.filter(
                practitioner=practitioner,
                status__in=['completed', 'validated', 'finished']
            ).select_related(
                'competition', 'category', 'competition__discipline'
            ).order_by('-competition__start_date')

            for reg in registrations:
                place = getattr(reg, 'place', None) or getattr(reg, 'ranking', None) or getattr(reg, 'final_rank', None)

                if place:
                    medal_type = None
                    if place == 1:
                        medal_type = 'gold'
                    elif place == 2:
                        medal_type = 'silver'
                    elif place == 3:
                        medal_type = 'bronze'

                    results.append({
                        'id': str(reg.id),
                        'competition_id': reg.competition.id,
                        'competition_name': reg.competition.name,
                        'competition_date': reg.competition.start_date.isoformat() if reg.competition.start_date else None,
                        'category_name': reg.category.name if reg.category else 'Catégorie inconnue',
                        'discipline_name': reg.competition.discipline.name if reg.competition.discipline else '',
                        'place': place,
                        'medal_type': medal_type,
                        'score': getattr(reg, 'score', None) or getattr(reg, 'final_score', None),
                        'points': getattr(reg, 'points', None),
                    })

        except Exception as e:
            print(f"Error getting competition results: {e}")
            import traceback
            traceback.print_exc()

        # Méthode 2: Via les combats
        try:
            from apps.competitions.models import Combat
            from django.db.models import Q

            # Combats où le pratiquant a gagné (1ère place dans un combat)
            winning_combats = Combat.objects.filter(
                Q(participant1__user=practitioner.user, winner_id=Q(participant1_id)) |
                Q(participant2__user=practitioner.user, winner_id=Q(participant2_id)),
                status='completed'
            ).select_related('competition', 'competition__discipline').order_by('-date_time')[:50]

            # Note: Cette logique peut être ajustée selon le modèle exact

        except Exception as e:
            print(f"Error getting combat results: {e}")

        # Méthode 3: Via le modèle ScoringResult si disponible
        try:
            from apps.competitions.models.scoring_results import ScoringResult

            scoring_results = ScoringResult.objects.filter(
                practitioner=practitioner
            ).select_related('competition', 'category', 'discipline').order_by('-competition__start_date')

            for sr in scoring_results:
                place = getattr(sr, 'final_rank', None) or getattr(sr, 'position', None)
                if place:
                    medal_type = None
                    if place == 1:
                        medal_type = 'gold'
                    elif place == 2:
                        medal_type = 'silver'
                    elif place == 3:
                        medal_type = 'bronze'

                    # Éviter les doublons
                    existing_ids = [r['id'] for r in results]
                    result_id = f'sr_{sr.id}'
                    if result_id not in existing_ids:
                        results.append({
                            'id': result_id,
                            'competition_id': sr.competition.id if sr.competition else None,
                            'competition_name': sr.competition.name if sr.competition else 'Compétition',
                            'competition_date': sr.competition.start_date.isoformat() if sr.competition and sr.competition.start_date else None,
                            'category_name': sr.category.name if sr.category else '',
                            'discipline_name': sr.discipline.name if sr.discipline else '',
                            'place': place,
                            'medal_type': medal_type,
                            'score': getattr(sr, 'total_score', None) or getattr(sr, 'score', None),
                            'points': getattr(sr, 'points', None),
                        })

        except ImportError:
            pass
        except Exception as e:
            print(f"Error getting scoring results: {e}")

        # Trier par date décroissante
        results.sort(key=lambda x: x.get('competition_date') or '0000-01-01', reverse=True)

        return results

    def _get_summary(self, practitioner, results):
        """Calculer le résumé du palmarès."""
        gold = sum(1 for r in results if r.get('medal_type') == 'gold')
        silver = sum(1 for r in results if r.get('medal_type') == 'silver')
        bronze = sum(1 for r in results if r.get('medal_type') == 'bronze')

        # Compter les compétitions uniques
        competition_ids = set(r.get('competition_id') for r in results if r.get('competition_id'))

        # Disciplines uniques
        disciplines = list(set(r.get('discipline_name') for r in results if r.get('discipline_name')))

        # Meilleur classement
        places = [r.get('place') for r in results if r.get('place')]
        best_ranking = min(places) if places else None

        return {
            'total_competitions': len(competition_ids),
            'total_medals': gold + silver + bronze,
            'gold_medals': gold,
            'silver_medals': silver,
            'bronze_medals': bronze,
            'total_participations': len(results),
            'best_ranking': best_ranking,
            'disciplines': disciplines,
        }

    def _get_achievements(self, practitioner):
        """Récupérer les achievements/accomplissements formatés pour l'affichage."""
        achievements = []

        try:
            # Récupérer les mêmes données que _get_results mais formatées différemment
            from apps.competitions.models.registrations import CompetitionRegistration

            registrations = CompetitionRegistration.objects.filter(
                practitioner=practitioner,
                status__in=['completed', 'validated', 'finished']
            ).select_related(
                'competition', 'category'
            ).order_by('-competition__start_date')[:10]

            for reg in registrations:
                place = getattr(reg, 'place', None) or getattr(reg, 'ranking', None) or getattr(reg, 'final_rank', None)

                if place and place <= 5:  # Top 5
                    title = f"{place}{'er' if place == 1 else 'ème'} place"
                    if reg.category:
                        title += f" - {reg.category.name}"

                    achievements.append({
                        'id': str(reg.id),
                        'title': title,
                        'competition_name': reg.competition.name if reg.competition else '',
                        'competitionName': reg.competition.name if reg.competition else '',  # Alias pour compat mobile
                        'place': place,
                        'date': reg.competition.start_date.isoformat() if reg.competition and reg.competition.start_date else None,
                    })

        except Exception as e:
            print(f"Error getting achievements: {e}")

        return achievements


# =============================================================================
# Judge API Views (Mobile App)
# =============================================================================

class JudgeCanAccessView(APIView):
    """Vérifie si l'utilisateur peut accéder au dashboard Juge."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        can_access = False
        judge_type = None

        try:
            # 1. Vérifier si Judge profile existe (tout juge actif, pas seulement technique)
            from apps.competitions.models.judges import Judge
            judge = Judge.objects.filter(user=user, active=True).first()
            if judge:
                can_access = True
                judge_type = 'technical' if getattr(judge, 'is_technical_judge', False) else 'standard'

            # 2. Vérifier via Practitioner si pas trouvé directement
            if not can_access:
                from apps.competitions.models.practitioners import Practitioner
                practitioner = Practitioner.objects.filter(user=user).first()
                if practitioner:
                    judge = Judge.objects.filter(practitioner=practitioner, active=True).first()
                    if judge:
                        can_access = True
                        judge_type = 'technical' if getattr(judge, 'is_technical_judge', False) else 'standard'

            # 3. Vérifier si AdHocJudge actif
            if not can_access:
                try:
                    from apps.competitions.models.adhoc_judges import AdHocJudge
                    from apps.competitions.models.practitioners import Practitioner
                    practitioner = Practitioner.objects.filter(user=user).first()
                    if practitioner:
                        adhoc = AdHocJudge.get_active_for_practitioner(practitioner)
                        if adhoc.exists():
                            can_access = True
                            judge_type = 'adhoc'
                except Exception:
                    pass

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error checking judge access: {e}")

        return Response({'can_access': can_access, 'judge_type': judge_type})


class JudgeProfileView(APIView):
    """Récupère le profil Juge de l'utilisateur."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        try:
            from apps.competitions.models.judges import Judge
            from apps.competitions.models.practitioners import Practitioner

            # Chercher le Judge profile
            judge = Judge.objects.filter(user=user, active=True).first()
            if not judge:
                practitioner = Practitioner.objects.filter(user=user).first()
                if practitioner:
                    judge = Judge.objects.filter(practitioner=practitioner, active=True).first()

            if not judge:
                return Response({'error': 'No judge profile found'}, status=404)

            return Response({
                'id': judge.id,
                'user_id': judge.user_id if judge.user_id else None,
                'practitioner_id': judge.practitioner_id if hasattr(judge, 'practitioner_id') else None,
                'qualification_level': getattr(judge, 'qualification_level', 'novice'),
                'years_experience': getattr(judge, 'years_experience', 0),
                'is_technical_judge': getattr(judge, 'is_technical_judge', False),
                'is_combat_referee': getattr(judge, 'is_combat_referee', False),
                'certification_number': getattr(judge, 'certification_number', None),
                'certified_since': str(judge.certified_since) if getattr(judge, 'certified_since', None) else None,
                'organization_id': getattr(judge.organization, 'id', None) if hasattr(judge, 'organization') else None,
                'organization_name': getattr(judge.organization, 'name', None) if hasattr(judge, 'organization') else None,
                'active': judge.active,
                'full_name': getattr(judge, 'full_name', '') or str(judge),
            })

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting judge profile: {e}")
            return Response({'error': str(e)}, status=500)


class JudgeDashboardAPIView(APIView):
    """Dashboard Juge avec statistiques et assignations."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        from datetime import date, timedelta

        try:
            from apps.competitions.models.judges import Judge
            from apps.competitions.models.practitioners import Practitioner

            # Obtenir le profil Judge
            judge = None
            practitioner = None

            judge = Judge.objects.filter(user=user, active=True).first()
            if not judge:
                practitioner = Practitioner.objects.filter(user=user).first()
                if practitioner:
                    judge = Judge.objects.filter(practitioner=practitioner, active=True).first()

            # Vérifier si ad-hoc judge
            is_adhoc = False
            adhoc_assignments = []
            try:
                from apps.competitions.models.adhoc_judges import AdHocJudge
                if practitioner:
                    adhoc_qs = AdHocJudge.get_active_for_practitioner(practitioner)
                    if adhoc_qs.exists():
                        is_adhoc = True
                        adhoc_assignments = list(adhoc_qs)
            except Exception:
                pass

            if not judge and not is_adhoc:
                return Response({
                    'judge': None,
                    'stats': {
                        'assignments_today': 0,
                        'performance_highlights': 0,
                        'upcoming_competitions': 0,
                        'years_experience': 0,
                        'total_competitions': 0,
                        'completed_competitions': 0,
                        'qualifications_count': 0,
                        'pending_performances': 0,
                    },
                    'current_assignments': [],
                    'upcoming_assignments': [],
                    'pending_performances': [],
                    'today_schedule': [],
                    'recent_competitions': [],
                    'is_adhoc_judge': is_adhoc,
                    'has_practitioner_profile': practitioner is not None,
                })

            # Construire les données
            today = date.today()

            # Assignations
            current_assignments = []
            upcoming_assignments = []
            try:
                from apps.competitions.models.judges import JudgeAssignment
                if judge:
                    assignments_qs = JudgeAssignment.objects.filter(user=user).select_related('category', 'category__competition')

                    for a in assignments_qs:
                        assignment_data = {
                            'id': a.id,
                            'competition_id': a.category.competition.id if a.category and a.category.competition else None,
                            'competition_name': a.category.competition.name if a.category and a.category.competition else '',
                            'category_id': a.category.id if a.category else None,
                            'category_name': a.category.name if a.category else '',
                            'assignment_type': a.assignment_type,
                            'status': a.status,
                            'start_time': str(a.start_time) if a.start_time else None,
                            'end_time': str(a.end_time) if a.end_time else None,
                            'tatami': a.tatami,
                            'is_adhoc': False,
                            'date': str(a.start_time.date()) if a.start_time else str(today),
                        }
                        if a.start_time and a.start_time.date() == today:
                            current_assignments.append(assignment_data)
                        elif a.start_time and a.start_time.date() > today:
                            upcoming_assignments.append(assignment_data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error getting assignments: {e}")

            # Add adhoc assignments
            for adhoc in adhoc_assignments:
                for cat in adhoc.assigned_categories.all():
                    assignment_data = {
                        'id': f'adhoc_{adhoc.id}_{cat.id}',
                        'competition_id': adhoc.competition.id if adhoc.competition else None,
                        'competition_name': adhoc.competition.name if adhoc.competition else '',
                        'category_id': cat.id,
                        'category_name': cat.name,
                        'assignment_type': adhoc.judge_type,
                        'status': adhoc.status,
                        'is_adhoc': True,
                        'date': str(today),
                    }
                    current_assignments.append(assignment_data)

            # Pending performances
            pending_performances = []
            pending_count = 0
            try:
                from apps.competitions.models.scoring_results import Performance

                # Get categories the judge is assigned to
                assigned_category_ids = [a.get('category_id') for a in current_assignments + upcoming_assignments if a.get('category_id')]

                if assigned_category_ids:
                    perfs = Performance.objects.filter(
                        category_id__in=assigned_category_ids,
                        status__in=['ready', 'in_progress', 'pending_validation']
                    ).select_related('practitioner', 'category', 'category__competition')[:20]

                    for p in perfs:
                        pending_performances.append({
                            'id': p.id,
                            'practitioner_id': p.practitioner.id if p.practitioner else None,
                            'practitioner_name': f"{p.practitioner.first_name} {p.practitioner.last_name}" if p.practitioner else '',
                            'category_id': p.category.id if p.category else None,
                            'category_name': p.category.name if p.category else '',
                            'competition_id': p.category.competition.id if p.category and p.category.competition else None,
                            'competition_name': p.category.competition.name if p.category and p.category.competition else '',
                            'scheduled_time': str(p.scheduled_time) if p.scheduled_time else None,
                            'order': p.order,
                            'status': p.status,
                        })
                    pending_count = len(pending_performances)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error getting performances: {e}")

            # Stats
            years_exp = getattr(judge, 'years_experience', 0) if judge else 0
            stats = {
                'assignments_today': len(current_assignments),
                'performance_highlights': 0,
                'upcoming_competitions': len(set(a.get('competition_id') for a in upcoming_assignments if a.get('competition_id'))),
                'years_experience': years_exp,
                'total_competitions': len(current_assignments) + len(upcoming_assignments),
                'completed_competitions': 0,
                'qualifications_count': 1 if judge else 0,
                'pending_performances': pending_count,
            }

            # Judge profile data
            judge_data = None
            if judge:
                judge_data = {
                    'id': judge.id,
                    'qualification_level': getattr(judge, 'qualification_level', 'novice'),
                    'years_experience': years_exp,
                    'is_technical_judge': getattr(judge, 'is_technical_judge', False),
                    'is_combat_referee': getattr(judge, 'is_combat_referee', False),
                    'full_name': getattr(judge, 'full_name', '') or str(judge),
                    'active': judge.active,
                }

            return Response({
                'judge': judge_data,
                'stats': stats,
                'current_assignments': current_assignments,
                'upcoming_assignments': upcoming_assignments,
                'pending_performances': pending_performances,
                'pending_performances_count': pending_count,
                'today_schedule': current_assignments,  # Simplified
                'recent_competitions': [],
                'is_adhoc_judge': is_adhoc,
                'has_practitioner_profile': practitioner is not None,
            })

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error in JudgeDashboardAPIView: {e}")
            return Response({'error': str(e)}, status=500)


class JudgeAssignmentsView(APIView):
    """Liste des assignations du juge."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        filter_type = request.GET.get('filter', 'all')
        from datetime import date

        try:
            from apps.competitions.models.judges import JudgeAssignment

            qs = JudgeAssignment.objects.filter(user=user).select_related('category', 'category__competition')

            today = date.today()
            if filter_type == 'today':
                qs = qs.filter(start_time__date=today)
            elif filter_type == 'upcoming':
                qs = qs.filter(start_time__date__gt=today)
            elif filter_type == 'past':
                qs = qs.filter(start_time__date__lt=today)

            assignments = []
            for a in qs:
                assignments.append({
                    'id': a.id,
                    'competition_id': a.category.competition.id if a.category and a.category.competition else None,
                    'competition_name': a.category.competition.name if a.category and a.category.competition else '',
                    'category_id': a.category.id if a.category else None,
                    'category_name': a.category.name if a.category else '',
                    'assignment_type': a.assignment_type,
                    'assignment_type_display': a.get_assignment_type_display() if hasattr(a, 'get_assignment_type_display') else a.assignment_type,
                    'status': a.status,
                    'start_time': str(a.start_time) if a.start_time else None,
                    'end_time': str(a.end_time) if a.end_time else None,
                    'tatami': a.tatami,
                    'notes': a.notes,
                    'is_adhoc': False,
                    'location': a.category.competition.location if a.category and a.category.competition else None,
                    'date': str(a.start_time.date()) if a.start_time else '',
                })

            return Response({'assignments': assignments})

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting assignments: {e}")
            return Response({'assignments': []})


class JudgeAssignmentRespondView(APIView):
    """Accepter ou décliner une assignation."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, assignment_id):
        action = request.data.get('action')

        if action not in ['accept', 'decline']:
            return Response({'error': 'Invalid action'}, status=400)

        try:
            from apps.competitions.models.judges import JudgeAssignment

            assignment = JudgeAssignment.objects.get(id=assignment_id, user=request.user)
            assignment.status = 'confirmed' if action == 'accept' else 'declined'
            assignment.save()

            return Response({'success': True, 'status': assignment.status})

        except JudgeAssignment.DoesNotExist:
            return Response({'error': 'Assignment not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class JudgePendingPerformancesView(APIView):
    """Performances en attente de notation."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        try:
            from apps.competitions.models.scoring_results import Performance
            from apps.competitions.models.judges import JudgeAssignment

            # Get assigned categories
            assigned_category_ids = list(
                JudgeAssignment.objects.filter(
                    user=user,
                    status__in=['confirmed', 'pending']
                ).values_list('category_id', flat=True)
            )

            performances = []
            if assigned_category_ids:
                perfs = Performance.objects.filter(
                    category_id__in=assigned_category_ids,
                    status__in=['ready', 'in_progress', 'pending_validation']
                ).select_related('practitioner', 'category', 'category__competition')

                for p in perfs:
                    performances.append({
                        'id': p.id,
                        'practitioner_id': p.practitioner.id if p.practitioner else None,
                        'practitioner_name': f"{p.practitioner.first_name} {p.practitioner.last_name}" if p.practitioner else '',
                        'category_id': p.category.id if p.category else None,
                        'category_name': p.category.name if p.category else '',
                        'competition_id': p.category.competition.id if p.category and p.category.competition else None,
                        'competition_name': p.category.competition.name if p.category and p.category.competition else '',
                        'scheduled_time': str(p.scheduled_time) if p.scheduled_time else None,
                        'order': p.order,
                        'status': p.status,
                        'total_score': p.total_score,
                    })

            return Response({'performances': performances})

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting pending performances: {e}")
            return Response({'performances': []})


class JudgePerformanceHistoryView(APIView):
    """Historique des performances notées."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))

        try:
            from apps.competitions.models.scoring_results import Performance
            from apps.competitions.models.judges import JudgeAssignment

            # Get assigned categories
            assigned_category_ids = list(
                JudgeAssignment.objects.filter(user=request.user).values_list('category_id', flat=True)
            )

            if not assigned_category_ids:
                return Response({'performances': [], 'total': 0, 'has_more': False})

            perfs_qs = Performance.objects.filter(
                category_id__in=assigned_category_ids,
                status='completed'
            ).select_related('practitioner', 'category', 'category__competition').order_by('-completion_time')

            total = perfs_qs.count()
            offset = (page - 1) * limit
            perfs = perfs_qs[offset:offset + limit]

            performances = []
            for p in perfs:
                performances.append({
                    'id': p.id,
                    'practitioner_id': p.practitioner.id if p.practitioner else None,
                    'practitioner_name': f"{p.practitioner.first_name} {p.practitioner.last_name}" if p.practitioner else '',
                    'category_id': p.category.id if p.category else None,
                    'category_name': p.category.name if p.category else '',
                    'competition_id': p.category.competition.id if p.category and p.category.competition else None,
                    'competition_name': p.category.competition.name if p.category and p.category.competition else '',
                    'total_score': p.total_score,
                    'status': p.status,
                })

            return Response({
                'performances': performances,
                'total': total,
                'has_more': offset + limit < total,
            })

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting performance history: {e}")
            return Response({'performances': [], 'total': 0, 'has_more': False})


class JudgePerformanceScoreView(APIView):
    """Soumettre une notation pour une performance."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request, performance_id):
        scores = request.data.get('scores', {})
        notes = request.data.get('notes', '')

        try:
            from apps.competitions.models.scoring_results import Performance, TechnicalScore

            perf = Performance.objects.get(id=performance_id)

            # Créer le score technique
            TechnicalScore.objects.create(
                performance=perf,
                judge=request.user,
                scores=scores,
                notes=notes,
            )

            # Recalculer le score total
            perf.calculate_total_score()
            perf.save()

            return Response({'success': True, 'total_score': perf.total_score})

        except Performance.DoesNotExist:
            return Response({'error': 'Performance not found'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class JudgeCombatAreasView(APIView):
    """Aires de combat disponibles."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from datetime import date

        try:
            from apps.competitions.models.combat import AireCombat
            from apps.competitions.models.competitions import Competition

            today = date.today()

            # Get active competitions for today
            competitions = Competition.objects.filter(
                start_date__lte=today,
                end_date__gte=today,
                status__in=['active', 'in_progress']
            )

            areas = []
            for comp in competitions:
                aires = AireCombat.objects.filter(competition=comp)
                for aire in aires:
                    areas.append({
                        'id': aire.id,
                        'name': getattr(aire, 'name', f"Aire {aire.numero}"),
                        'number': aire.numero,
                        'competition_id': comp.id,
                        'competition_name': comp.name,
                        'is_active': getattr(aire, 'is_active', True),
                    })

            return Response({'areas': areas})

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting combat areas: {e}")
            return Response({'areas': []})


class JudgeSettingsView(APIView):
    """Paramètres du juge."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        try:
            from apps.competitions.models.judges import Judge

            judge = Judge.objects.filter(user=request.user, active=True).first()
            if not judge:
                return Response({})

            return Response({
                'notification_enabled': True,
                'auto_accept_assignments': False,
                'preferred_categories': [],
                'qualification_level': getattr(judge, 'qualification_level', 'novice'),
            })

        except Exception as e:
            return Response({})

    def put(self, request):
        # Placeholder for settings update
        return Response({'success': True})


class JudgeSwitchModeView(APIView):
    """Bascule entre mode Juge et mode Pratiquant."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        mode = request.data.get('mode')

        if mode not in ['judge', 'practitioner']:
            return Response({'error': 'Invalid mode'}, status=400)

        # Store mode in session
        request.session['dashboard_mode'] = 'judge_technical' if mode == 'judge' else 'participant'

        return Response({'success': True, 'mode': mode})