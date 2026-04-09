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

        # Build subscription info
        subscription_data = self._get_subscription_info(organization)

        return Response({
            'role': getattr(user, 'role', 'guest') if user else 'guest',
            'practitioner_id': practitioner_id,
            'practitioner_name': practitioner_name,
            'organization': {
                'id': str(getattr(organization, 'id', '')),
                'name': getattr(organization, 'name', ''),
                'type': getattr(organization, 'organization_type', 'club'),
                'slug': getattr(organization, 'slug', None),
                'logo_url': getattr(organization, 'logo_url', None) if organization else None,
            } if organization else None,
            'statistics': statistics,
            'modules': modules,
            'upcoming_competitions': upcoming_competitions,
            'capabilities': getattr(user, 'permissions', []) if user and hasattr(user, 'permissions') else [],
            'subscription': subscription_data,
        })

    def _get_subscription_info(self, organization):
        """Get subscription info for the mobile dashboard."""
        try:
            from apps.finances.services.subscription_service import get_subscription_info
            info = get_subscription_info(organization)
            return {
                'tier_name': info.get('tier_name', 'free'),
                'display_name': info.get('display_name', 'Free'),
                'is_free': info.get('is_free', True),
                'members_count': info.get('members_count', 0),
                'max_members': info.get('max_members', 10),
                'can_add_member': info.get('can_add_member', True),
                'remaining_slots': info.get('remaining_slots', 10),
                'is_at_limit': info.get('is_at_limit', False),
                'is_near_limit': info.get('is_near_limit', False),
            }
        except Exception as e:
            print(f"Error getting subscription info: {e}")
            return {
                'tier_name': 'free',
                'display_name': 'Free',
                'is_free': True,
                'members_count': 0,
                'max_members': 10,
                'can_add_member': True,
                'remaining_slots': 10,
                'is_at_limit': False,
                'is_near_limit': False,
            }

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
                org_type = getattr(organization, 'organization_type', 'club')

                # Check if this is a federation
                is_federation = org_type in ['national_federation', 'international_federation', 'regional_body', 'global_body']

                if is_federation:
                    # Federation statistics - count affiliated clubs, participants across all clubs, etc.
                    stats = self._get_federation_statistics(organization)
                else:
                    # Club statistics
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

    def _get_federation_statistics(self, federation_org):
        """Get statistics specific to federations."""
        stats = {
            'practitioners_count': 0,
            'active_registrations': 0,
            'organized_competitions': 0,
            'judges_referees': 0,
            # Federation-specific stats
            'affiliated_clubs_count': 0,
            'clubs_count': 0,
            'participants_count': 0,
            'certified_judges_count': 0,
            'files_count': 0,
            'upcoming_events_count': 0,
            'competitions_count': 0,
        }

        try:
            from apps.organizations.models import Affiliation, Organization
            from apps.competitions.models import Practitioner, Competition, Judge
            from django.db.models import Q
            from django.utils import timezone

            org_id = federation_org.id
            affiliated_clubs = []

            # Count affiliated clubs (via Affiliation model)
            try:
                affiliated_clubs = list(Affiliation.objects.filter(
                    parent_organization_id=org_id,
                    is_active=True,
                    parent_status='approved'
                ).values_list('child_organization_id', flat=True))
                stats['affiliated_clubs_count'] = len(affiliated_clubs)
                stats['clubs_count'] = len(affiliated_clubs)
            except Exception as e:
                print(f"Error counting affiliated clubs: {e}")

            # Count total participants across all affiliated clubs
            try:
                if affiliated_clubs:
                    stats['participants_count'] = Practitioner.objects.filter(
                        Q(organization_id__in=affiliated_clubs) | Q(organization_id=org_id)
                    ).count()
                else:
                    stats['participants_count'] = Practitioner.objects.filter(
                        organization_id=org_id
                    ).count()
                stats['practitioners_count'] = stats['participants_count']
            except Exception as e:
                print(f"Error counting participants: {e}")

            # Count competitions organized by federation or affiliated clubs
            try:
                if affiliated_clubs:
                    stats['competitions_count'] = Competition.objects.filter(
                        Q(organizing_organization_id__in=affiliated_clubs) | Q(organizing_organization_id=org_id)
                    ).count()
                else:
                    stats['competitions_count'] = Competition.objects.filter(
                        organizing_organization_id=org_id
                    ).count()
                stats['organized_competitions'] = stats['competitions_count']
            except Exception as e:
                print(f"Error counting competitions: {e}")

            # Count certified judges across federation
            try:
                if affiliated_clubs:
                    stats['certified_judges_count'] = Judge.objects.filter(
                        Q(organization_id__in=affiliated_clubs) | Q(organization_id=org_id),
                        active=True
                    ).count()
                else:
                    stats['certified_judges_count'] = Judge.objects.filter(
                        organization_id=org_id,
                        active=True
                    ).count()
                stats['judges_referees'] = stats['certified_judges_count']
            except Exception as e:
                print(f"Error counting judges: {e}")

            # Count upcoming events
            try:
                from apps.competitions.models.event import Event
                if affiliated_clubs:
                    stats['upcoming_events_count'] = Event.objects.filter(
                        Q(organization_id__in=affiliated_clubs) | Q(organization_id=org_id),
                        date__gte=timezone.now().date()
                    ).count()
                else:
                    stats['upcoming_events_count'] = Event.objects.filter(
                        organization_id=org_id,
                        date__gte=timezone.now().date()
                    ).count()
            except Exception as e:
                print(f"Error counting upcoming events: {e}")

            # Count files/documents
            try:
                from apps.documents.models import Document
                if affiliated_clubs:
                    stats['files_count'] = Document.objects.filter(
                        Q(organization_id__in=affiliated_clubs) | Q(organization_id=org_id)
                    ).count()
                else:
                    stats['files_count'] = Document.objects.filter(
                        organization_id=org_id
                    ).count()
            except Exception as e:
                print(f"Error counting files: {e}")

        except Exception as e:
            print(f"Error getting federation statistics: {e}")

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
            qs = Competition.objects.filter(start_date__gte=now).order_by('start_date')

            if organization:
                qs = qs.filter(
                    Q(organizing_organization=organization) | Q(is_published=True)
                )
            else:
                qs = qs.filter(is_published=True)

            for comp in qs[:5]:
                location = ', '.join(filter(None, [comp.venue_name, comp.city])) or ''
                competitions.append({
                    'id': str(comp.id),
                    'name': comp.title or '',
                    'title': comp.title or '',
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if comp.end_date else None,
                    'location': location,
                    'status': 'upcoming',
                    'registrations_count': 0,
                    'categories_count': comp.categories.count() if hasattr(comp, 'categories') else 0,
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
                'organization'
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
        """Compétitions à venir dans la discipline du pratiquant, avec statut d'inscription."""
        competitions = []
        try:
            from apps.competitions.models import Competition, PractitionerDiscipline
            from apps.competitions.models.registrations import CompetitionRegistration
            from django.utils import timezone
            from django.db.models import Q

            today = timezone.now().date()

            # Collect discipline IDs from multiple sources (aligned with web dashboard)
            discipline_ids = set(
                PractitionerDiscipline.objects.filter(
                    practitioner=practitioner
                ).values_list('discipline_id', flat=True)
            )
            if hasattr(practitioner, 'disciplines'):
                discipline_ids.update(
                    practitioner.disciplines.values_list('id', flat=True)
                )
            if hasattr(practitioner, 'primary_discipline_id') and practitioner.primary_discipline_id:
                discipline_ids.add(practitioner.primary_discipline_id)
            # Fallback: organization disciplines
            if not discipline_ids and practitioner.organization and hasattr(practitioner.organization, 'disciplines'):
                discipline_ids.update(
                    practitioner.organization.disciplines.values_list('id', flat=True)
                )

            # Build queryset - filter by discipline BEFORE slicing
            qs = Competition.objects.filter(
                status__in=['published', 'open', 'registration_open'],
                start_date__gte=today
            ).select_related('discipline').order_by('start_date')

            if discipline_ids:
                qs = qs.filter(Q(discipline_id__in=list(discipline_ids)) | Q(discipline__isnull=True))

            # Get registration statuses in bulk (single query)
            registered_statuses = dict(
                CompetitionRegistration.objects.filter(
                    practitioner=practitioner,
                    competition__start_date__gte=today
                ).values_list('competition_id', 'status')
            )

            for comp in qs[:10]:
                reg_status = registered_statuses.get(comp.id)
                city = getattr(comp, 'city', '') or ''
                location = getattr(comp, 'location', '') or getattr(comp, 'venue', '') or city

                competitions.append({
                    'id': str(comp.id),
                    'name': getattr(comp, 'title', '') or getattr(comp, 'name', ''),
                    'title': getattr(comp, 'title', '') or getattr(comp, 'name', ''),
                    'start_date': comp.start_date.isoformat() if comp.start_date else None,
                    'end_date': comp.end_date.isoformat() if comp.end_date else None,
                    'location': location,
                    'city': city,
                    'discipline': comp.discipline.name if comp.discipline else None,
                    'discipline_id': comp.discipline_id,
                    'registration_deadline': comp.registration_deadline.isoformat() if comp.registration_deadline else None,
                    'is_registered': reg_status in ('approved', 'pending', 'confirmed'),
                    'registration_status': reg_status,  # approved/pending/confirmed/None
                    'registration_open': comp.status in ['open', 'registration_open', 'published'],
                })
        except Exception as e:
            import traceback
            print(f"Error getting upcoming competitions: {e}")
            traceback.print_exc()

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
            ).select_related('competition').order_by('competition__start_date')[:10]

            for reg in qs:
                registrations.append({
                    'id': str(reg.id),
                    'competition': {
                        'id': str(reg.competition.id),
                        'name': reg.competition.title,
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
            from apps.competitions.models.combat import Combat
            from django.db.models import Q

            # Combats terminés où le pratiquant est participant (rouge ou blanc)
            combats = Combat.objects.filter(
                Q(pratiquant_rouge=practitioner) | Q(pratiquant_blanc=practitioner),
                status='termine'
            ).select_related('pratiquant_rouge', 'pratiquant_blanc', 'competition').order_by('-fin_combat')

            stats['total_combats'] = combats.count()

            for combat in combats[:5]:  # 5 derniers combats
                is_rouge = combat.pratiquant_rouge == practitioner
                opponent = combat.pratiquant_blanc if is_rouge else combat.pratiquant_rouge

                # Déterminer le résultat
                if combat.est_nul:
                    is_winner = False
                    is_draw = True
                elif combat.vainqueur == 'rouge' and is_rouge:
                    is_winner = True
                    is_draw = False
                elif combat.vainqueur == 'blanc' and not is_rouge:
                    is_winner = True
                    is_draw = False
                else:
                    is_winner = False
                    is_draw = False

                if is_winner:
                    stats['victories'] += 1
                elif is_draw:
                    stats['draws'] += 1
                else:
                    stats['defeats'] += 1

                # Nom de l'adversaire
                opponent_name = 'Inconnu'
                if opponent and opponent.user:
                    opponent_name = f"{opponent.user.first_name} {opponent.user.last_name}".strip()

                # Score
                my_score = float(combat.score_rouge) if is_rouge else float(combat.score_blanc)
                opp_score = float(combat.score_blanc) if is_rouge else float(combat.score_rouge)

                stats['recent_combats'].append({
                    'id': str(combat.uuid),
                    'opponent': opponent_name,
                    'result': 'victory' if is_winner else ('draw' if is_draw else 'defeat'),
                    'score': f"{my_score:.0f} - {opp_score:.0f}",
                    'competition': combat.competition.title if combat.competition else None,
                    'date': combat.fin_combat.isoformat() if combat.fin_combat else (combat.debut_combat.isoformat() if combat.debut_combat else None),
                })

            if stats['total_combats'] > 0:
                stats['win_rate'] = round((stats['victories'] / stats['total_combats']) * 100, 1)

        except Exception as e:
            import traceback
            print(f"Error getting combat stats: {e}")
            traceback.print_exc()

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
            )[:6]

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
        from django.utils import timezone as tz
        today = tz.now().date()

        # 1. Récupérer les compétitions
        try:
            from apps.competitions.models import Competition
            from django.db.models import Q

            qs = Competition.objects.filter(
                status__in=['published', 'open', 'registration_open'],
                start_date__gte=today
            ).select_related('discipline').order_by('start_date')

            # Filtrer par discipline si le pratiquant en a une
            if hasattr(practitioner, 'disciplines') and practitioner.disciplines.exists():
                discipline_ids = list(practitioner.disciplines.values_list('id', flat=True))
                qs = qs.filter(Q(discipline_id__in=discipline_ids) | Q(discipline__isnull=True))

            for comp in qs[:20]:
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
                'organization'
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
                'organization'
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
                status__in=['completed', 'validated', 'finished', 'participated']
            ).select_related(
                'competition'
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
                        'competition_name': reg.competition.title,
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

        # Méthode 2: Via les combats (victoires = 1ère place)
        try:
            from apps.competitions.models.combat import Combat
            from django.db.models import Q

            # Combats terminés où le pratiquant a gagné
            # Rouge gagnant ou Blanc gagnant
            winning_combats_rouge = Combat.objects.filter(
                pratiquant_rouge=practitioner,
                vainqueur='rouge',
                status='termine'
            ).select_related('competition')

            winning_combats_blanc = Combat.objects.filter(
                pratiquant_blanc=practitioner,
                vainqueur='blanc',
                status='termine'
            ).select_related('competition')

            # Ajouter les victoires comme 1ère place
            for combat in winning_combats_rouge:
                if combat.competition:
                    existing_ids = [r['id'] for r in results]
                    result_id = f'combat_win_{combat.id}'
                    if result_id not in existing_ids:
                        results.append({
                            'id': result_id,
                            'competition_id': combat.competition.id,
                            'competition_name': combat.competition.title,
                            'competition_date': combat.competition.start_date.isoformat() if combat.competition.start_date else None,
                            'category_name': '',
                            'discipline_name': combat.competition.discipline.name if hasattr(combat.competition, 'discipline') and combat.competition.discipline else '',
                            'place': 1,
                            'medal_type': 'gold',
                            'score': float(combat.score_rouge),
                            'points': None,
                        })

            for combat in winning_combats_blanc:
                if combat.competition:
                    existing_ids = [r['id'] for r in results]
                    result_id = f'combat_win_{combat.id}'
                    if result_id not in existing_ids:
                        results.append({
                            'id': result_id,
                            'competition_id': combat.competition.id,
                            'competition_name': combat.competition.title,
                            'competition_date': combat.competition.start_date.isoformat() if combat.competition.start_date else None,
                            'category_name': '',
                            'discipline_name': combat.competition.discipline.name if hasattr(combat.competition, 'discipline') and combat.competition.discipline else '',
                            'place': 1,
                            'medal_type': 'gold',
                            'score': float(combat.score_blanc),
                            'points': None,
                        })

        except Exception as e:
            print(f"Error getting combat results: {e}")

        # Méthode 3: Via le modèle ScoringResult si disponible
        try:
            from apps.competitions.models.scoring_results import ScoringResult

            scoring_results = ScoringResult.objects.filter(
                practitioner=practitioner
            ).select_related('competition').order_by('-competition__start_date')

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
                            'competition_name': sr.competition.title if sr.competition else 'Compétition',
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

        # Méthode 4: Via CompetitionRanking (technical competitions - source principale des médailles)
        try:
            from apps.competitions.models import CompetitionRanking

            competition_rankings = CompetitionRanking.objects.filter(
                practitioner=practitioner
            ).select_related('competition').order_by('-competition__start_date')

            for cr in competition_rankings:
                place = getattr(cr, 'rank', None) or getattr(cr, 'position', None)
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
                    result_id = f'cr_{cr.id}'
                    if result_id not in existing_ids:
                        results.append({
                            'id': result_id,
                            'competition_id': cr.competition.id if cr.competition else None,
                            'competition_name': cr.competition.title if cr.competition else 'Compétition',
                            'competition_date': cr.competition.start_date.isoformat() if cr.competition and cr.competition.start_date else None,
                            'category_name': cr.category.name if hasattr(cr, 'category') and cr.category else '',
                            'discipline_name': cr.competition.discipline.name if cr.competition and cr.competition.discipline else '',
                            'place': place,
                            'medal_type': medal_type,
                            'score': getattr(cr, 'total_score', None) or getattr(cr, 'score', None),
                            'points': getattr(cr, 'points', None),
                        })

        except ImportError:
            pass
        except Exception as e:
            print(f"Error getting competition rankings: {e}")

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
                status__in=['completed', 'validated', 'finished', 'participated']
            ).select_related(
                'competition'
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
                        'competition_name': reg.competition.title if reg.competition else '',
                        'competitionName': reg.competition.title if reg.competition else '',  # Alias pour compat mobile
                        'place': place,
                        'date': reg.competition.start_date.isoformat() if reg.competition and reg.competition.start_date else None,
                    })

        except Exception as e:
            print(f"Error getting achievements: {e}")

        return achievements


# =============================================================================
# Mobile Combats API View
# =============================================================================

class MobileCombatsView(APIView):
    """
    API pour les statistiques de combats d'un pratiquant (App mobile).
    Retourne l'historique des combats avec statistiques (victoires, défaites, nuls).
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        try:
            from apps.competitions.models.practitioners import Practitioner
            from apps.competitions.models.combat import Combat

            # Trouver le pratiquant
            practitioner = Practitioner.objects.filter(user=user).first()

            if not practitioner:
                return Response({
                    'summary': self._empty_summary(),
                    'combats': [],
                    'message': 'Aucun profil pratiquant trouvé'
                })

            # Récupérer tous les combats terminés du pratiquant
            combats_rouge = Combat.objects.filter(
                pratiquant_rouge=practitioner,
                status='termine'
            ).select_related('competition', 'pratiquant_blanc')

            combats_blanc = Combat.objects.filter(
                pratiquant_blanc=practitioner,
                status='termine'
            ).select_related('competition', 'pratiquant_rouge')

            # Calculer les statistiques
            total_combats = combats_rouge.count() + combats_blanc.count()
            victories = 0
            defeats = 0
            draws = 0

            combat_list = []

            # Combats où le pratiquant était rouge
            for combat in combats_rouge:
                is_victory = combat.vainqueur == 'rouge'
                is_draw = combat.est_nul

                if is_draw:
                    draws += 1
                    result = 'draw'
                elif is_victory:
                    victories += 1
                    result = 'victory'
                else:
                    defeats += 1
                    result = 'defeat'

                opponent = combat.pratiquant_blanc
                opponent_name = f"{opponent.user.first_name} {opponent.user.last_name}" if opponent and opponent.user else "Adversaire inconnu"

                combat_list.append({
                    'id': str(combat.uuid),
                    'competition_id': combat.competition.id if combat.competition else None,
                    'competition_name': combat.competition.title if combat.competition else 'Compétition',
                    'competition_date': combat.competition.start_date.isoformat() if combat.competition and combat.competition.start_date else None,
                    'opponent_name': opponent_name,
                    'my_score': float(combat.score_rouge),
                    'opponent_score': float(combat.score_blanc),
                    'result': result,
                    'my_color': 'rouge',
                    'date': combat.fin_combat.isoformat() if combat.fin_combat else (combat.debut_combat.isoformat() if combat.debut_combat else None),
                })

            # Combats où le pratiquant était blanc
            for combat in combats_blanc:
                is_victory = combat.vainqueur == 'blanc'
                is_draw = combat.est_nul

                if is_draw:
                    draws += 1
                    result = 'draw'
                elif is_victory:
                    victories += 1
                    result = 'victory'
                else:
                    defeats += 1
                    result = 'defeat'

                opponent = combat.pratiquant_rouge
                opponent_name = f"{opponent.user.first_name} {opponent.user.last_name}" if opponent and opponent.user else "Adversaire inconnu"

                combat_list.append({
                    'id': str(combat.uuid),
                    'competition_id': combat.competition.id if combat.competition else None,
                    'competition_name': combat.competition.title if combat.competition else 'Compétition',
                    'competition_date': combat.competition.start_date.isoformat() if combat.competition and combat.competition.start_date else None,
                    'opponent_name': opponent_name,
                    'my_score': float(combat.score_blanc),
                    'opponent_score': float(combat.score_rouge),
                    'result': result,
                    'my_color': 'blanc',
                    'date': combat.fin_combat.isoformat() if combat.fin_combat else (combat.debut_combat.isoformat() if combat.debut_combat else None),
                })

            # Trier par date décroissante
            combat_list.sort(key=lambda x: x.get('date') or '0000-01-01', reverse=True)

            # Calculer le taux de victoire
            win_rate = (victories / total_combats * 100) if total_combats > 0 else 0.0

            summary = {
                'total_combats': total_combats,
                'victories': victories,
                'defeats': defeats,
                'draws': draws,
                'win_rate': round(win_rate, 1),
            }

            return Response({
                'summary': summary,
                'combats': combat_list,
            })

        except Exception as e:
            import traceback
            print(f"Error in MobileCombatsView: {e}")
            traceback.print_exc()
            return Response({
                'summary': self._empty_summary(),
                'combats': [],
                'error': str(e)
            }, status=500)

    def _empty_summary(self):
        return {
            'total_combats': 0,
            'victories': 0,
            'defeats': 0,
            'draws': 0,
            'win_rate': 0.0,
        }


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

            # Also check if user has JudgeCompetitionAssignment or judge registrations
            has_judge_registrations = False
            if not judge and not is_adhoc:
                try:
                    from apps.competitions.models.registrations import JudgeCompetitionAssignment, CompetitionRegistration
                    from django.db.models import Q as Q_check
                    has_judge_registrations = (
                        JudgeCompetitionAssignment.objects.filter(
                            registration__practitioner__user=user
                        ).exists()
                        or CompetitionRegistration.objects.filter(
                            practitioner__user=user
                        ).filter(
                            Q_check(is_technical_judge=True) | Q_check(is_combat_referee=True)
                        ).exists()
                    )
                except Exception:
                    pass


            if not judge and not is_adhoc and not has_judge_registrations:

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
                from apps.competitions.models.registrations import JudgeCompetitionAssignment
                from django.db.models import Q

                # 1. JudgeAssignment (si Judge record existe)
                assignments_qs = JudgeAssignment.objects.none()
                if judge:
                    q_filter = Q(user=user)
                    q_filter |= Q(registration__practitioner__user=user)
                    if practitioner:
                        q_filter |= Q(registration__practitioner=practitioner)
                    assignments_qs = JudgeAssignment.objects.filter(
                        q_filter
                    ).select_related(
                        'category', 'category__competition'
                    ).distinct()

                # 2. JudgeCompetitionAssignment (toujours chercher)
                jca_qs = JudgeCompetitionAssignment.objects.none()
                existing_cat_ids = set()
                try:
                    jca_qs = JudgeCompetitionAssignment.objects.filter(
                        registration__practitioner__user=user
                    ).select_related(
                        'category', 'category__competition'
                    )
                    existing_cat_ids = set(
                        assignments_qs.values_list('category_id', flat=True)
                    )
                except Exception as jca_err:
                    pass



                for a in assignments_qs:
                    comp = a.category.competition if a.category else None
                    comp_start = comp.start_date if comp else None
                    comp_end = comp.end_date if comp else None

                    if a.start_time:
                        assignment_date = a.start_time.date()
                    else:
                        assignment_date = comp_start

                    assignment_data = {
                        'id': a.id,
                        'competition_id': comp.id if comp else None,
                        'competition_name': comp.title if comp else '',
                        'category_id': a.category.id if a.category else None,
                        'category_name': a.category.name if a.category else '',
                        'assignment_type': a.assignment_type,
                        'status': a.status,
                        'start_time': str(a.start_time) if a.start_time else None,
                        'end_time': str(a.end_time) if a.end_time else None,
                        'tatami': a.tatami,
                        'is_adhoc': False,
                        'date': str(assignment_date) if assignment_date else str(today),
                    }

                    if assignment_date:
                        is_today = (assignment_date == today) or (
                            comp_start and comp_end and comp_start <= today <= comp_end
                        )
                        if is_today:
                            current_assignments.append(assignment_data)
                        elif assignment_date > today:
                            upcoming_assignments.append(assignment_data)

                # Process JudgeCompetitionAssignment results
                for jca in jca_qs:
                    if jca.category_id in existing_cat_ids:
                        continue
                    existing_cat_ids.add(jca.category_id)
                    comp = jca.category.competition if jca.category else None
                    comp_start = comp.start_date if comp else None
                    comp_end = comp.end_date if comp else None
                    assignment_date = comp_start

                    assignment_data = {
                        'id': f'jca_{jca.id}',
                        'competition_id': comp.id if comp else None,
                        'competition_name': comp.title if comp else '',
                        'category_id': jca.category.id if jca.category else None,
                        'category_name': jca.category.name if jca.category else '',
                        'assignment_type': jca.assignment_type,
                        'status': 'confirmed',
                        'start_time': None,
                        'end_time': None,
                        'tatami': None,
                        'is_adhoc': False,
                        'date': str(assignment_date) if assignment_date else str(today),
                    }

                    if assignment_date:
                        is_today = (assignment_date == today) or (
                            comp_start and comp_end and comp_start <= today <= comp_end
                        )
                        if is_today:
                            current_assignments.append(assignment_data)
                        elif assignment_date > today:
                            upcoming_assignments.append(assignment_data)
                    else:
                        current_assignments.append(assignment_data)

                # 3. CompetitionRegistration with judge flags (is_technical_judge / is_combat_referee)
                # This is the primary source for users registered as judges via competition registration
                try:
                    from apps.competitions.models.registrations import CompetitionRegistration
                    from apps.competitions.models.categories import CompetitionCategory

                    judge_registrations = CompetitionRegistration.objects.filter(
                        practitioner__user=user
                    ).filter(
                        Q(is_technical_judge=True) | Q(is_combat_referee=True)
                    ).select_related('competition')

                    for reg in judge_registrations:
                        comp = reg.competition
                        if not comp:
                            continue
                        comp_start = comp.start_date
                        comp_end = comp.end_date

                        # Determine assignment type from registration flags
                        if reg.is_technical_judge and reg.is_combat_referee:
                            reg_assignment_type = 'technical_judge'
                        elif reg.is_combat_referee:
                            reg_assignment_type = 'combat_referee'
                        else:
                            reg_assignment_type = 'technical_judge'

                        # Get all categories for this competition
                        categories = CompetitionCategory.objects.filter(competition=comp)
                        for cat in categories:
                            if cat.id in existing_cat_ids:
                                continue
                            existing_cat_ids.add(cat.id)
                            assignment_date = comp_start

                            assignment_data = {
                                'id': f'reg_{reg.id}_{cat.id}',
                                'competition_id': comp.id,
                                'competition_name': comp.title,
                                'category_id': cat.id,
                                'category_name': cat.name,
                                'assignment_type': reg_assignment_type,
                                'status': 'confirmed',
                                'start_time': None,
                                'end_time': None,
                                'tatami': None,
                                'is_adhoc': False,
                                'date': str(assignment_date) if assignment_date else str(today),
                                'location': getattr(comp, 'location', '') or '',
                            }

                            if assignment_date:
                                is_today = (assignment_date == today) or (
                                    comp_start and comp_end and comp_start <= today <= comp_end
                                )
                                if is_today:
                                    current_assignments.append(assignment_data)
                                elif assignment_date > today or (comp_end and comp_end >= today):
                                    upcoming_assignments.append(assignment_data)
                            else:
                                current_assignments.append(assignment_data)
                except Exception as reg_err:
                    pass

            except Exception as e:
                pass



            # Add adhoc assignments - also check competition dates
            for adhoc in adhoc_assignments:
                comp = adhoc.competition
                comp_start = comp.start_date if comp else None
                comp_end = comp.end_date if comp else None

                for cat in adhoc.assigned_categories.all():
                    assignment_date = comp_start or today
                    assignment_data = {
                        'id': f'adhoc_{adhoc.id}_{cat.id}',
                        'competition_id': comp.id if comp else None,
                        'competition_name': comp.title if comp else '',
                        'category_id': cat.id,
                        'category_name': cat.name,
                        'assignment_type': adhoc.judge_type,
                        'status': adhoc.status,
                        'is_adhoc': True,
                        'date': str(assignment_date),
                    }

                    is_today = (comp_start and comp_end and comp_start <= today <= comp_end) or (not comp_start)
                    if is_today:
                        current_assignments.append(assignment_data)
                    elif comp_start and comp_start > today:
                        upcoming_assignments.append(assignment_data)
                    else:
                        current_assignments.append(assignment_data)

            # Pending performances (TechnicalPerformance model)
            pending_performances = []
            pending_count = 0
            try:
                from apps.competitions.models.technical_scoring import TechnicalPerformance

                # Get categories the judge is assigned to
                assigned_category_ids = [a.get('category_id') for a in current_assignments + upcoming_assignments if a.get('category_id')]

                if assigned_category_ids:
                    perfs = TechnicalPerformance.objects.filter(
                        category_id__in=assigned_category_ids,
                        status__in=['pending', 'in_progress']
                    ).select_related('practitioner', 'category', 'category__competition')[:20]

                    for p in perfs:
                        pending_performances.append({
                            'id': p.id,
                            'practitioner_id': p.practitioner.id if p.practitioner else None,
                            'practitioner_name': p.practitioner.full_name if p.practitioner else '',
                            'category_id': p.category.id if p.category else None,
                            'category_name': p.category.name if p.category else '',
                            'competition_id': p.category.competition.id if p.category and p.category.competition else None,
                            'competition_name': p.category.competition.title if p.category and p.category.competition else '',
                            'scheduled_time': str(p.start_time) if p.start_time else None,
                            'order': p.performance_order,
                            'status': p.status,
                        })
                    pending_count = len(pending_performances)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Error getting performances: {e}")

            # Stats - include TechnicalScore data
            years_exp = getattr(judge, 'years_experience', 0) if judge else 0
            total_scored = 0
            completed_competitions_count = 0
            try:
                from apps.competitions.models.technical_scoring import TechnicalScore
                total_scored = TechnicalScore.objects.filter(
                    judge=user, is_active_for_ranking=True
                ).values('performance').distinct().count()
                completed_competitions_count = TechnicalScore.objects.filter(
                    judge=user, is_active_for_ranking=True
                ).values('performance__competition').distinct().count()
            except Exception:
                pass

            stats = {
                'assignments_today': len(current_assignments),
                'performance_highlights': total_scored,
                'upcoming_competitions': len(set(a.get('competition_id') for a in upcoming_assignments if a.get('competition_id'))),
                'years_experience': years_exp,
                'total_competitions': completed_competitions_count or (len(current_assignments) + len(upcoming_assignments)),
                'completed_competitions': completed_competitions_count,
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
                    'competition_name': a.category.competition.title if a.category and a.category.competition else '',
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
    """Performances en attente de notation (TechnicalPerformance)."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        try:
            from apps.competitions.models.technical_scoring import (
                TechnicalPerformance
            )
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
                perfs = TechnicalPerformance.objects.filter(
                    category_id__in=assigned_category_ids,
                    status__in=['pending', 'in_progress']
                ).select_related(
                    'practitioner', 'category',
                    'category__competition'
                )

                for p in perfs:
                    performances.append({
                        'id': p.id,
                        'practitioner_id': p.practitioner.id if p.practitioner else None,
                        'practitioner_name': p.practitioner.full_name if p.practitioner else '',
                        'category_id': p.category.id if p.category else None,
                        'category_name': p.category.name if p.category else '',
                        'competition_id': p.category.competition.id if p.category and p.category.competition else None,
                        'competition_name': p.category.competition.title if p.category and p.category.competition else '',
                        'scheduled_time': str(p.start_time) if p.start_time else None,
                        'order': p.performance_order,
                        'status': p.status,
                    })

            return Response({'performances': performances})

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error getting pending performances: {e}")
            return Response({'performances': []})


class JudgePerformanceHistoryView(APIView):
    """Historique des performances notées (TechnicalScore)."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 20))

        try:
            from apps.competitions.models.technical_scoring import (
                TechnicalScore, TechnicalPerformance
            )
            from django.db.models import Avg

            # Get distinct performances this judge has scored
            scored_perf_ids = TechnicalScore.objects.filter(
                judge=request.user,
                is_active_for_ranking=True
            ).values_list(
                'performance_id', flat=True
            ).distinct()

            if not scored_perf_ids:
                return Response({
                    'performances': [],
                    'total': 0,
                    'has_more': False,
                    'stats': {
                        'total_scored': 0,
                        'average_score': 0,
                    }
                })

            perfs_qs = TechnicalPerformance.objects.filter(
                id__in=scored_perf_ids,
                status='completed'
            ).select_related(
                'practitioner', 'category',
                'category__competition'
            ).order_by('-created_at')

            total = perfs_qs.count()
            offset = (page - 1) * limit
            perfs = perfs_qs[offset:offset + limit]

            performances = []
            for p in perfs:
                # Get this judge's scores for this performance
                judge_scores = TechnicalScore.objects.filter(
                    performance=p,
                    judge=request.user,
                    is_active_for_ranking=True
                )
                avg = judge_scores.aggregate(
                    avg=Avg('value')
                )['avg'] or 0

                performances.append({
                    'id': p.id,
                    'practitioner_id': (
                        p.practitioner.id if p.practitioner
                        else None
                    ),
                    'practitioner_name': (
                        p.practitioner.full_name if p.practitioner
                        else ''
                    ),
                    'category_id': (
                        p.category.id if p.category else None
                    ),
                    'category_name': (
                        p.category.name if p.category else ''
                    ),
                    'competition_id': (
                        p.category.competition.id
                        if p.category and p.category.competition
                        else None
                    ),
                    'competition_name': (
                        p.category.competition.title
                        if p.category and p.category.competition
                        else ''
                    ),
                    'total_score': round(float(avg), 2),
                    'final_score': round(
                        float(p.calculate_final_score()), 2
                    ),
                    'status': p.status,
                    'date': str(p.created_at.date()),
                    'scores_detail': list(
                        judge_scores.values(
                            'criterion__name', 'value'
                        )
                    ),
                })

            # Global stats
            all_scores = TechnicalScore.objects.filter(
                judge=request.user,
                is_active_for_ranking=True
            )
            global_avg = all_scores.aggregate(
                avg=Avg('value')
            )['avg'] or 0

            return Response({
                'performances': performances,
                'total': total,
                'has_more': offset + limit < total,
                'stats': {
                    'total_scored': total,
                    'average_score': round(float(global_avg), 2),
                }
            })

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(
                f"Error getting performance history: {e}"
            )
            return Response({
                'performances': [],
                'total': 0,
                'has_more': False,
                'stats': {
                    'total_scored': 0,
                    'average_score': 0,
                }
            })


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
    """Aires de combat disponibles pour le juge."""
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from datetime import date, timedelta

        try:
            from apps.competitions.models.combat import AireCombat
            from apps.competitions.models.competitions import Competition

            today = date.today()
            upcoming_limit = today + timedelta(days=30)

            # Get competitions: ongoing today or starting within next 30 days
            competitions = Competition.objects.filter(
                end_date__gte=today,
                start_date__lte=upcoming_limit,
            ).order_by('start_date')

            areas = []
            for comp in competitions:
                aires = AireCombat.objects.filter(competition=comp, is_active=True)
                is_today = comp.start_date <= today <= comp.end_date
                for aire in aires:
                    areas.append({
                        'id': aire.id,
                        'name': getattr(aire, 'nom', None) or getattr(aire, 'name', f"Aire {aire.numero}"),
                        'number': aire.numero,
                        'competition_id': comp.id,
                        'competition_name': comp.title,
                        'is_active': getattr(aire, 'is_active', True),
                        'is_today': is_today,
                        'competition_date': str(comp.start_date),
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


# =============================================================================
# Federation API Views (Mobile App)
# =============================================================================

class FederationAffiliatedClubsView(APIView):
    """
    Liste des clubs affiliés à une fédération.

    GET /api/v1/mobile/federation/clubs/
        ?search=name (optionnel)
        &status=approved|pending|all (default: approved)
        &limit=50 (default: 50)
        &offset=0 (default: 0)

    Retourne la liste des clubs affiliés à la fédération de l'utilisateur.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        search = request.GET.get('search', '').strip()
        status_filter = request.GET.get('status', 'approved')
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        # Récupérer la fédération de l'utilisateur
        federation = self._get_user_federation(user)

        if not federation:
            return Response({
                'clubs': [],
                'total': 0,
                'is_federation': False,
                'message': 'Vous n\'êtes pas associé à une fédération',
            })

        # Vérifier que c'est bien une fédération
        org_type = getattr(federation, 'organization_type', 'club')
        is_federation = org_type in ['national_federation', 'international_federation', 'regional_body', 'global_body']

        if not is_federation:
            return Response({
                'clubs': [],
                'total': 0,
                'is_federation': False,
                'message': 'Votre organisation n\'est pas une fédération',
            })

        # Récupérer les clubs affiliés
        clubs_data, total = self._get_affiliated_clubs(federation, search, status_filter, limit, offset, request)

        return Response({
            'clubs': clubs_data,
            'total': total,
            'is_federation': True,
            'federation': {
                'id': str(federation.id),
                'name': federation.name,
                'type': org_type,
            },
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total,
        })

    def _get_user_federation(self, user):
        """Récupère la fédération de l'utilisateur."""
        federation = None
        federation_types = ['national_federation', 'international_federation', 'regional_body', 'global_body']

        # 0. PRIORITY: Check if user has federation_admin role - if so, find their federation
        user_role = None
        user_profile = None
        try:
            from apps.competitions.models import UserProfile
            user_profile = UserProfile.objects.filter(user=user).select_related('organization').first()
            if user_profile:
                user_role = getattr(user_profile, 'role', None)
                print(f"DEBUG _get_user_federation: User {user.username} has role: {user_role}")
        except Exception as e:
            print(f"Error getting user role: {e}")

        # 1. Via UserProfile - check organization type
        if user_profile and user_profile.organization:
            org_type = getattr(user_profile.organization, 'organization_type', '')
            print(f"DEBUG _get_user_federation: UserProfile.organization type: {org_type}")
            if org_type in federation_types:
                federation = user_profile.organization
                print(f"DEBUG _get_user_federation: Found federation via UserProfile: {federation.name}")

        # 2. If user has federation_admin role but organization is not federation type,
        #    look for federation via Affiliation (parent organization)
        if not federation and user_role == 'federation_admin' and user_profile and user_profile.organization:
            try:
                from apps.organizations.models import Affiliation
                # Check if user's organization has a parent federation
                affiliation = Affiliation.objects.filter(
                    child_organization=user_profile.organization,
                    is_active=True
                ).select_related('parent_organization').first()
                if affiliation and affiliation.parent_organization:
                    parent_type = getattr(affiliation.parent_organization, 'organization_type', '')
                    if parent_type in federation_types:
                        federation = affiliation.parent_organization
                        print(f"DEBUG _get_user_federation: Found federation via Affiliation parent: {federation.name}")
            except Exception as e:
                print(f"Error getting federation from Affiliation: {e}")

        # 3. Via OrganizationMember - check for federation membership
        if not federation:
            try:
                from apps.organizations.models import OrganizationMember
                memberships = OrganizationMember.objects.filter(
                    user=user, is_active=True
                ).select_related('organization')
                for membership in memberships:
                    if membership.organization:
                        org_type = getattr(membership.organization, 'organization_type', '')
                        if org_type in federation_types:
                            federation = membership.organization
                            print(f"DEBUG _get_user_federation: Found federation via OrganizationMember: {federation.name}")
                            break
            except Exception as e:
                print(f"Error getting federation from OrganizationMember: {e}")

        # 4. Via created_by (créateur de la fédération)
        if not federation:
            try:
                from apps.organizations.models import Organization
                created_orgs = Organization.objects.filter(
                    created_by=user,
                    organization_type__in=federation_types
                ).first()
                if created_orgs:
                    federation = created_orgs
                    print(f"DEBUG _get_user_federation: Found federation via created_by: {federation.name}")
            except Exception as e:
                print(f"Error getting federation from created_by: {e}")

        # 5. Via managers M2M field
        if not federation:
            try:
                from apps.organizations.models import Organization
                managed_orgs = Organization.objects.filter(
                    managers=user,
                    organization_type__in=federation_types
                ).first()
                if managed_orgs:
                    federation = managed_orgs
                    print(f"DEBUG _get_user_federation: Found federation via managers: {federation.name}")
            except Exception as e:
                print(f"Error getting federation from managers: {e}")

        # 6. FALLBACK: If user has federation_admin role, find ANY federation they might have access to
        if not federation and user_role == 'federation_admin':
            try:
                from apps.organizations.models import Organization
                # Try to find a federation directly associated with user via any path
                any_federation = Organization.objects.filter(
                    organization_type__in=federation_types
                ).first()
                if any_federation:
                    # Check if user has any relationship to this federation
                    # This is a last resort - might need to be more specific
                    federation = any_federation
                    print(f"DEBUG _get_user_federation: FALLBACK - Found federation: {federation.name}")
            except Exception as e:
                print(f"Error in fallback federation search: {e}")

        if not federation:
            print(f"DEBUG _get_user_federation: No federation found for user {user.username}")

        return federation

    def _get_affiliated_clubs(self, federation, search, status_filter, limit, offset, request):
        """Récupère les clubs affiliés à la fédération."""
        clubs_data = []
        total = 0

        try:
            from apps.organizations.models import Affiliation, Organization
            from apps.competitions.models import Practitioner
            from django.db.models import Q, Count

            # Base queryset - clubs affiliés à cette fédération
            affiliations_qs = Affiliation.objects.filter(
                parent_organization=federation
            ).select_related('child_organization')

            # Filter by status
            if status_filter == 'approved':
                affiliations_qs = affiliations_qs.filter(is_active=True, parent_status='approved')
            elif status_filter == 'pending':
                affiliations_qs = affiliations_qs.filter(
                    Q(parent_status='pending') | Q(child_status='pending')
                )
            # status_filter == 'all' -> no additional filter

            # Search by club name
            if search:
                affiliations_qs = affiliations_qs.filter(
                    Q(child_organization__name__icontains=search) |
                    Q(child_organization__short_name__icontains=search)
                )

            total = affiliations_qs.count()
            affiliations = affiliations_qs.order_by('child_organization__name')[offset:offset + limit]

            for affiliation in affiliations:
                club = affiliation.child_organization
                if not club:
                    continue

                # Count practitioners in this club
                practitioners_count = 0
                try:
                    practitioners_count = Practitioner.objects.filter(organization=club).count()
                except Exception:
                    pass

                # Build logo URL
                logo_url = None
                try:
                    if hasattr(club, 'logo') and club.logo:
                        logo_url = request.build_absolute_uri(club.logo.url)
                        if 'martialcomp.com' in logo_url and logo_url.startswith('http://'):
                            logo_url = logo_url.replace('http://', 'https://')
                except Exception:
                    pass

                clubs_data.append({
                    'id': str(club.id),
                    'name': club.name,
                    'short_name': getattr(club, 'short_name', '') or '',
                    'logo_url': logo_url,
                    'city': getattr(club, 'city', '') or '',
                    'country': getattr(club, 'country', '') or '',
                    'practitioners_count': practitioners_count,
                    'affiliation_date': affiliation.created_at.isoformat() if affiliation.created_at else None,
                    'affiliation_status': affiliation.parent_status,
                    'is_active': affiliation.is_active,
                    'subdomain': getattr(club, 'subdomain', '') or '',
                    'email': getattr(club, 'email', '') or '',
                    'phone': getattr(club, 'phone', '') or '',
                })

        except Exception as e:
            import traceback
            print(f"Error getting affiliated clubs: {e}")
            traceback.print_exc()

        return clubs_data, total


class FederationInviteClubView(APIView):
    """
    Inviter un club à rejoindre la fédération.

    POST /api/v1/mobile/federation/clubs/invite/
    Body: {
        "club_email": "club@example.com",
        "club_name": "Club Name" (optionnel),
        "message": "Message d'invitation" (optionnel)
    }
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def post(self, request):
        user = request.user
        club_email = request.data.get('club_email', '').strip()
        club_name = request.data.get('club_name', '').strip()
        message = request.data.get('message', '').strip()

        if not club_email:
            return Response({'error': 'L\'email du club est requis'}, status=400)

        # Récupérer la fédération
        federation = FederationAffiliatedClubsView()._get_user_federation(user)
        if not federation:
            return Response({'error': 'Vous n\'êtes pas associé à une fédération'}, status=403)

        try:
            # Créer une invitation (à implémenter selon le modèle existant)
            # Pour l'instant, retourner un succès simulé
            return Response({
                'success': True,
                'message': f'Invitation envoyée à {club_email}',
                'invitation': {
                    'email': club_email,
                    'club_name': club_name,
                    'federation_id': str(federation.id),
                    'federation_name': federation.name,
                }
            })

        except Exception as e:
            return Response({'error': str(e)}, status=500)


class FederationJudgesView(APIView):
    """
    Liste des juges des clubs affiliés à une fédération.

    GET /api/v1/mobile/federation/judges/
        ?search=name (optionnel)
        ?type=all|technical|combat (default: all)
        ?club_id=uuid (optionnel - filtrer par club)
        &limit=50 (default: 50)
        &offset=0 (default: 0)

    Retourne la liste des juges de tous les clubs affiliés à la fédération.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        search = request.GET.get('search', '').strip()
        judge_type = request.GET.get('type', 'all')
        club_id = request.GET.get('club_id', '').strip()
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        # Récupérer la fédération de l'utilisateur
        federation = FederationAffiliatedClubsView()._get_user_federation(user)

        if not federation:
            return Response({
                'judges': [],
                'total': 0,
                'statistics': {},
                'is_federation': False,
                'message': 'Vous n\'êtes pas associé à une fédération',
            })

        # Vérifier que c'est bien une fédération
        org_type = getattr(federation, 'organization_type', 'club')
        is_federation = org_type in ['national_federation', 'international_federation', 'regional_body', 'global_body']

        if not is_federation:
            return Response({
                'judges': [],
                'total': 0,
                'statistics': {},
                'is_federation': False,
                'message': 'Votre organisation n\'est pas une fédération',
            })

        # Récupérer les juges des clubs affiliés
        judges_data, total, statistics = self._get_federation_judges(
            federation, search, judge_type, club_id, limit, offset, request
        )

        return Response({
            'judges': judges_data,
            'total': total,
            'statistics': statistics,
            'is_federation': True,
            'federation': {
                'id': str(federation.id),
                'name': federation.name,
                'type': org_type,
            },
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total,
        })

    def _get_federation_judges(self, federation, search, judge_type, club_id, limit, offset, request):
        """Récupère les juges des clubs affiliés à la fédération."""
        judges_data = []
        total = 0
        statistics = {
            'total_judges': 0,
            'technical_judges': 0,
            'combat_referees': 0,
            'clubs_count': 0,
        }

        try:
            from apps.organizations.models import Affiliation
            from apps.competitions.models import UserProfile, Practitioner
            from django.db.models import Q

            # Get affiliated clubs
            affiliated_clubs_qs = Affiliation.objects.filter(
                parent_organization=federation,
                is_active=True,
                parent_status='approved'
            ).values_list('child_organization_id', flat=True)

            affiliated_club_ids = list(affiliated_clubs_qs)
            statistics['clubs_count'] = len(affiliated_club_ids)

            # Filter by specific club if provided
            if club_id:
                if club_id in [str(cid) for cid in affiliated_club_ids]:
                    affiliated_club_ids = [club_id]
                else:
                    return judges_data, 0, statistics

            # Get users with referee/judge roles from affiliated clubs
            judges_qs = UserProfile.objects.filter(
                organization_id__in=affiliated_club_ids,
                role__in=['referee', 'judge', 'technical_judge', 'combat_referee']
            ).select_related('user', 'organization')

            # Filter by judge type
            if judge_type == 'technical':
                judges_qs = judges_qs.filter(role__in=['judge', 'technical_judge'])
            elif judge_type == 'combat':
                judges_qs = judges_qs.filter(role__in=['referee', 'combat_referee'])

            # Search
            if search:
                judges_qs = judges_qs.filter(
                    Q(user__first_name__icontains=search) |
                    Q(user__last_name__icontains=search) |
                    Q(user__email__icontains=search)
                )

            total = judges_qs.count()

            # Statistics
            all_judges = UserProfile.objects.filter(
                organization_id__in=affiliated_club_ids,
                role__in=['referee', 'judge', 'technical_judge', 'combat_referee']
            )
            statistics['total_judges'] = all_judges.count()
            statistics['technical_judges'] = all_judges.filter(role__in=['judge', 'technical_judge']).count()
            statistics['combat_referees'] = all_judges.filter(role__in=['referee', 'combat_referee']).count()

            # Paginate
            judges = judges_qs.order_by('user__last_name', 'user__first_name')[offset:offset + limit]

            for profile in judges:
                user_obj = profile.user
                org = profile.organization

                # Build photo URL
                photo_url = None
                try:
                    if hasattr(user_obj, 'photo') and user_obj.photo:
                        photo_url = request.build_absolute_uri(user_obj.photo.url)
                        if 'martialcomp.com' in photo_url and photo_url.startswith('http://'):
                            photo_url = photo_url.replace('http://', 'https://')
                except Exception:
                    pass

                # Get certification info
                certifications = []
                try:
                    from apps.competitions.models import Certification
                    certs = Certification.objects.filter(user=user_obj, is_active=True)
                    for cert in certs[:3]:  # Limit to 3
                        certifications.append({
                            'type': getattr(cert, 'certification_type', ''),
                            'level': getattr(cert, 'level', ''),
                            'expires_at': cert.expires_at.isoformat() if cert.expires_at else None,
                        })
                except Exception:
                    pass

                judges_data.append({
                    'id': str(profile.id),
                    'user_id': str(user_obj.id),
                    'first_name': user_obj.first_name or '',
                    'last_name': user_obj.last_name or '',
                    'email': user_obj.email or '',
                    'photo_url': photo_url,
                    'role': profile.role,
                    'role_display': self._get_role_display(profile.role),
                    'club': {
                        'id': str(org.id) if org else None,
                        'name': org.name if org else '',
                    } if org else None,
                    'certifications': certifications,
                    'is_active': getattr(profile, 'is_active', True),
                })

        except Exception as e:
            import traceback
            print(f"Error getting federation judges: {e}")
            traceback.print_exc()

        return judges_data, total, statistics

    def _get_role_display(self, role):
        """Retourne le libellé du rôle."""
        role_map = {
            'referee': 'Arbitre',
            'judge': 'Juge',
            'technical_judge': 'Juge technique',
            'combat_referee': 'Arbitre combat',
        }
        return role_map.get(role, role)


class FederationGradesView(APIView):
    """
    Liste des pratiquants avec leurs grades des clubs affiliés à une fédération.

    GET /api/v1/mobile/federation/grades/
        ?search=name (optionnel)
        ?club_id=uuid (optionnel - filtrer par club)
        ?has_grade=true|false (optionnel)
        &limit=50 (default: 50)
        &offset=0 (default: 0)

    Retourne la liste des pratiquants avec leurs grades.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        search = request.GET.get('search', '').strip()
        club_id = request.GET.get('club_id', '').strip()
        has_grade = request.GET.get('has_grade', '').lower()
        limit = int(request.GET.get('limit', 50))
        offset = int(request.GET.get('offset', 0))

        # Récupérer la fédération de l'utilisateur
        federation = FederationAffiliatedClubsView()._get_user_federation(user)

        if not federation:
            return Response({
                'practitioners': [],
                'total': 0,
                'statistics': {},
                'clubs': [],
                'is_federation': False,
                'message': 'Vous n\'êtes pas associé à une fédération',
            })

        # Vérifier que c'est bien une fédération
        org_type = getattr(federation, 'organization_type', 'club')
        is_federation = org_type in ['national_federation', 'international_federation', 'regional_body', 'global_body']

        if not is_federation:
            return Response({
                'practitioners': [],
                'total': 0,
                'statistics': {},
                'clubs': [],
                'is_federation': False,
                'message': 'Votre organisation n\'est pas une fédération',
            })

        # Récupérer les pratiquants avec grades
        practitioners_data, total, statistics, clubs = self._get_federation_grades(
            federation, search, club_id, has_grade, limit, offset, request
        )

        return Response({
            'practitioners': practitioners_data,
            'total': total,
            'statistics': statistics,
            'clubs': clubs,
            'is_federation': True,
            'federation': {
                'id': str(federation.id),
                'name': federation.name,
                'type': org_type,
            },
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total,
        })

    def _get_federation_grades(self, federation, search, club_id, has_grade, limit, offset, request):
        """Récupère les pratiquants avec leurs grades des clubs affiliés."""
        practitioners_data = []
        total = 0
        statistics = {
            'total_practitioners': 0,
            'with_grade': 0,
            'without_grade': 0,
            'clubs_count': 0,
        }
        clubs = []

        try:
            from apps.organizations.models import Affiliation, Organization
            from apps.competitions.models import Practitioner
            from apps.grades.models import PractitionerGrade
            from django.db.models import Q, Prefetch, OuterRef, Subquery, Exists

            # Get affiliated clubs
            affiliated_clubs_qs = Affiliation.objects.filter(
                parent_organization=federation,
                is_active=True,
                parent_status='approved'
            ).select_related('child_organization')

            affiliated_club_ids = list(affiliated_clubs_qs.values_list('child_organization_id', flat=True))
            statistics['clubs_count'] = len(affiliated_club_ids)

            # Build clubs list for filter
            for aff in affiliated_clubs_qs:
                if aff.child_organization:
                    clubs.append({
                        'id': str(aff.child_organization.id),
                        'name': aff.child_organization.name,
                    })

            # Filter by specific club if provided
            if club_id:
                if club_id in [str(cid) for cid in affiliated_club_ids]:
                    affiliated_club_ids = [club_id]
                else:
                    return practitioners_data, 0, statistics, clubs

            # Get practitioners from affiliated clubs
            practitioners_qs = Practitioner.objects.filter(
                organization_id__in=affiliated_club_ids
            ).select_related('organization', 'user')

            # Annotate with current grade
            current_grade_subquery = PractitionerGrade.objects.filter(
                practitioner=OuterRef('pk'),
                is_current=True
            )
            practitioners_qs = practitioners_qs.annotate(
                has_current_grade=Exists(current_grade_subquery)
            )

            # Filter by has_grade
            if has_grade == 'true':
                practitioners_qs = practitioners_qs.filter(has_current_grade=True)
            elif has_grade == 'false':
                practitioners_qs = practitioners_qs.filter(has_current_grade=False)

            # Search
            if search:
                practitioners_qs = practitioners_qs.filter(
                    Q(first_name__icontains=search) |
                    Q(last_name__icontains=search) |
                    Q(user__email__icontains=search)
                )

            total = practitioners_qs.count()

            # Statistics
            all_practitioners = Practitioner.objects.filter(organization_id__in=affiliated_club_ids)
            statistics['total_practitioners'] = all_practitioners.count()

            # Count with/without grade
            with_grade_count = 0
            without_grade_count = 0
            for p in all_practitioners:
                has_g = PractitionerGrade.objects.filter(practitioner=p, is_current=True).exists()
                if has_g:
                    with_grade_count += 1
                else:
                    without_grade_count += 1
            statistics['with_grade'] = with_grade_count
            statistics['without_grade'] = without_grade_count

            # Paginate
            practitioners = practitioners_qs.order_by('last_name', 'first_name')[offset:offset + limit]

            for practitioner in practitioners:
                org = practitioner.organization

                # Build photo URL
                photo_url = None
                try:
                    if hasattr(practitioner, 'photo') and practitioner.photo:
                        photo_url = request.build_absolute_uri(practitioner.photo.url)
                        if 'martialcomp.com' in photo_url and photo_url.startswith('http://'):
                            photo_url = photo_url.replace('http://', 'https://')
                except Exception:
                    pass

                # Get current grade
                current_grade = None
                grade_history = []
                try:
                    grades = PractitionerGrade.objects.filter(
                        practitioner=practitioner
                    ).select_related('grade').order_by('-awarded_date')

                    for pg in grades[:5]:  # Last 5 grades
                        grade_data = {
                            'id': str(pg.id),
                            'grade_name': pg.grade.name if pg.grade else '',
                            'grade_level': pg.grade.level if pg.grade else 0,
                            'grade_color': getattr(pg.grade, 'color', '') if pg.grade else '',
                            'awarded_date': pg.awarded_date.isoformat() if pg.awarded_date else None,
                            'is_current': pg.is_current,
                        }
                        if pg.is_current:
                            current_grade = grade_data
                        grade_history.append(grade_data)
                except Exception as e:
                    print(f"Error getting grades for practitioner {practitioner.id}: {e}")

                practitioners_data.append({
                    'id': str(practitioner.id),
                    'first_name': practitioner.first_name or '',
                    'last_name': practitioner.last_name or '',
                    'email': getattr(practitioner.user, 'email', '') if practitioner.user else '',
                    'photo_url': photo_url,
                    'birth_date': practitioner.birth_date.isoformat() if practitioner.birth_date else None,
                    'club': {
                        'id': str(org.id) if org else None,
                        'name': org.name if org else '',
                    } if org else None,
                    'current_grade': current_grade,
                    'grade_history': grade_history,
                    'has_grade': current_grade is not None,
                })

        except Exception as e:
            import traceback
            print(f"Error getting federation grades: {e}")
            traceback.print_exc()

        return practitioners_data, total, statistics, clubs


class FederationResultsView(APIView):
    """
    Résultats des compétitions agrégés pour une fédération.

    GET /api/v1/mobile/federation/results/

    Retourne les médailles, statistiques et résultats des clubs affiliés.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        # Récupérer la fédération de l'utilisateur
        federation = FederationAffiliatedClubsView()._get_user_federation(user)

        if not federation:
            return Response({
                'is_federation': False,
                'message': 'Vous n\'êtes pas associé à une fédération',
                'medals': {'gold': 0, 'silver': 0, 'bronze': 0, 'total': 0},
                'statistics': {},
                'recent_competitions': [],
                'top_clubs': [],
                'results': [],
            })

        # Vérifier que c'est bien une fédération
        org_type = getattr(federation, 'organization_type', 'club')
        is_federation = org_type in ['national_federation', 'international_federation', 'regional_body', 'global_body']

        if not is_federation:
            return Response({
                'is_federation': False,
                'message': 'Votre organisation n\'est pas une fédération',
                'medals': {'gold': 0, 'silver': 0, 'bronze': 0, 'total': 0},
                'statistics': {},
                'recent_competitions': [],
                'top_clubs': [],
                'results': [],
            })

        # Récupérer les données
        data = self._get_federation_results(federation)

        return Response({
            'is_federation': True,
            'federation': {
                'id': str(federation.id),
                'name': federation.name,
            },
            **data
        })

    def _get_federation_results(self, federation):
        """Récupère les résultats des compétitions pour la fédération."""
        medals = {'gold': 0, 'silver': 0, 'bronze': 0, 'total': 0}
        statistics = {
            'total_participations': 0,
            'total_competitions': 0,
            'best_ranking': '-',
            'clubs_with_medals': 0,
        }
        recent_competitions = []
        top_clubs = []
        results = []

        try:
            from apps.organizations.models import Affiliation
            from apps.competitions.models import (
                Competition, Registration, Ranking, Category
            )
            from django.db.models import Count, Q, Sum
            from collections import defaultdict

            # Get affiliated clubs
            affiliated_clubs_qs = Affiliation.objects.filter(
                parent_organization=federation,
                is_active=True,
                parent_status='approved'
            ).values_list('child_organization_id', flat=True)

            affiliated_club_ids = list(affiliated_clubs_qs)

            if not affiliated_club_ids:
                return {
                    'medals': medals,
                    'statistics': statistics,
                    'recent_competitions': recent_competitions,
                    'top_clubs': top_clubs,
                    'results': results,
                }

            # Get rankings from competitions where affiliated clubs participated
            try:
                rankings = Ranking.objects.filter(
                    Q(practitioner__organization_id__in=affiliated_club_ids) |
                    Q(participant__practitioner__organization_id__in=affiliated_club_ids)
                ).select_related(
                    'category__competition',
                    'practitioner__organization',
                    'participant__practitioner__organization'
                )

                club_medals = defaultdict(lambda: {'gold': 0, 'silver': 0, 'bronze': 0, 'participations': 0})
                competition_ids = set()
                clubs_with_medals = set()

                for ranking in rankings:
                    # Get practitioner and club info
                    practitioner = ranking.practitioner or (ranking.participant.practitioner if ranking.participant else None)
                    if not practitioner:
                        continue

                    club = practitioner.organization
                    if not club or str(club.id) not in [str(cid) for cid in affiliated_club_ids]:
                        continue

                    club_id = str(club.id)
                    club_name = club.name

                    # Track participation
                    club_medals[club_id]['name'] = club_name
                    club_medals[club_id]['participations'] += 1
                    statistics['total_participations'] += 1

                    # Track competition
                    if ranking.category and ranking.category.competition:
                        competition_ids.add(ranking.category.competition.id)

                    # Count medals based on position
                    position = getattr(ranking, 'position', None) or getattr(ranking, 'rank', None)
                    if position == 1:
                        medals['gold'] += 1
                        club_medals[club_id]['gold'] += 1
                        clubs_with_medals.add(club_id)
                    elif position == 2:
                        medals['silver'] += 1
                        club_medals[club_id]['silver'] += 1
                        clubs_with_medals.add(club_id)
                    elif position == 3:
                        medals['bronze'] += 1
                        club_medals[club_id]['bronze'] += 1
                        clubs_with_medals.add(club_id)

                    # Build result entry
                    competition = ranking.category.competition if ranking.category else None
                    results.append({
                        'id': str(ranking.id),
                        'competition_name': competition.name if competition else 'N/A',
                        'competition_date': competition.start_date.strftime('%d/%m/%Y') if competition and competition.start_date else '',
                        'club_name': club_name,
                        'athlete_name': f"{practitioner.first_name or ''} {practitioner.last_name or ''}".strip(),
                        'category': ranking.category.name if ranking.category else '',
                        'position': position or 0,
                        'medal_type': 'gold' if position == 1 else ('silver' if position == 2 else ('bronze' if position == 3 else None)),
                    })

                medals['total'] = medals['gold'] + medals['silver'] + medals['bronze']
                statistics['total_competitions'] = len(competition_ids)
                statistics['clubs_with_medals'] = len(clubs_with_medals)

                # Build top clubs list
                for club_id, data in sorted(club_medals.items(), key=lambda x: (x[1]['gold'], x[1]['silver'], x[1]['bronze']), reverse=True)[:10]:
                    top_clubs.append({
                        'club_id': club_id,
                        'club_name': data.get('name', 'N/A'),
                        'gold': data['gold'],
                        'silver': data['silver'],
                        'bronze': data['bronze'],
                        'total_participations': data['participations'],
                    })

                # Sort results by date (most recent first)
                results = sorted(results, key=lambda x: x.get('competition_date', ''), reverse=True)[:50]

            except Exception as e:
                print(f"Error getting rankings: {e}")

            # Get recent competitions
            try:
                recent_comps = Competition.objects.filter(
                    organization_id__in=affiliated_club_ids
                ).order_by('-start_date')[:5]

                for comp in recent_comps:
                    # Count participants from affiliated clubs
                    participants = Registration.objects.filter(
                        competition=comp,
                        practitioner__organization_id__in=affiliated_club_ids
                    ).count()

                    # Count medals in this competition
                    comp_medals = Ranking.objects.filter(
                        category__competition=comp,
                        practitioner__organization_id__in=affiliated_club_ids,
                        position__lte=3
                    ).count()

                    recent_competitions.append({
                        'id': str(comp.id),
                        'name': comp.name,
                        'date': comp.start_date.strftime('%d/%m/%Y') if comp.start_date else '',
                        'location': getattr(comp, 'city', '') or getattr(comp, 'location', '') or '',
                        'participants_count': participants,
                        'medals_count': comp_medals,
                    })
            except Exception as e:
                print(f"Error getting recent competitions: {e}")

        except Exception as e:
            import traceback
            print(f"Error getting federation results: {e}")
            traceback.print_exc()

        return {
            'medals': medals,
            'statistics': statistics,
            'recent_competitions': recent_competitions,
            'top_clubs': top_clubs,
            'results': results,
        }


# =============================================================================
# FAMILY MANAGEMENT API
# =============================================================================

class FamilyManagementAPIView(APIView):
    """API endpoint for mobile family management.

    Returns the list of families for the authenticated user.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        families_data = []

        try:
            from apps.family_management.models import Family, FamilyMember

            # Get families where user is primary responsible
            managed_families = Family.objects.filter(
                primary_responsible=user,
                is_active=True
            ).prefetch_related('members__practitioner')

            # Get families where user is a member
            member_families = Family.objects.filter(
                members__user=user,
                members__is_active=True,
                is_active=True
            ).exclude(primary_responsible=user).distinct()

            # Combine both sets
            all_families = list(managed_families) + list(member_families)

            for family in all_families:
                members = []
                for member in family.members.filter(is_active=True):
                    member_data = {
                        'id': str(member.id),
                        'role': member.role,
                        'practitioner_id': str(member.practitioner_id) if member.practitioner_id else None,
                        'user_id': str(member.user_id) if member.user_id else None,
                        'first_name': '',
                        'last_name': '',
                    }
                    if member.practitioner:
                        member_data['first_name'] = member.practitioner.first_name or ''
                        member_data['last_name'] = member.practitioner.last_name or ''
                    elif member.user:
                        member_data['first_name'] = member.user.first_name or ''
                        member_data['last_name'] = member.user.last_name or ''
                    members.append(member_data)

                families_data.append({
                    'id': str(family.id),
                    'family_name': family.family_name,
                    'description': family.description or '',
                    'is_primary_responsible': family.primary_responsible == user,
                    'members_count': len(members),
                    'members': members,
                    'created_at': family.created_at.isoformat() if family.created_at else None,
                })

        except ImportError:
            # Family management app not installed
            return Response({
                'families': [],
                'message': 'Family management module not available'
            })
        except Exception as e:
            print(f"Error getting families: {e}")
            return Response({
                'families': [],
                'error': str(e)
            })

        return Response({
            'families': families_data,
            'total': len(families_data),
        })


# =============================================================================
# COACH DASHBOARD API
# =============================================================================

class CoachDashboardAPIView(APIView):
    """
    API endpoint for Coach Dashboard (Mobile App).

    Returns comprehensive coach data including:
    - Students (practitioners under coach supervision)
    - Disciplines
    - Sessions/Planning
    - Programs
    - Statistics
    - Finances
    - Upcoming events

    GET /api/v1/coach/dashboard/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user

        # Get organization from various sources
        organization = self._get_organization(user, request)

        # Get coach profile
        coach_profile = self._get_coach_profile(user)

        # Build comprehensive coach data
        students = self._get_students(user, organization)
        disciplines = self._get_disciplines(user, organization, coach_profile)
        sessions = self._get_sessions(user, organization)
        programs = self._get_programs(user, organization)
        statistics = self._get_statistics(user, organization, students)
        finances = self._get_finances(user, organization)
        upcoming_events = self._get_upcoming_events(user, organization)
        upcoming_competitions = self._get_upcoming_competitions(organization)

        return Response({
            'role': 'coach',
            'coach_profile': {
                'id': str(coach_profile.id) if coach_profile else None,
                'specialties': getattr(coach_profile, 'specialties', '') if coach_profile else '',
                'experience_years': getattr(coach_profile, 'experience_years', 0) if coach_profile else 0,
            } if coach_profile else None,
            'organization': {
                'id': str(organization.id) if organization else '',
                'name': organization.name if organization else '',
                'type': getattr(organization, 'organization_type', 'club') if organization else 'club',
                'logo_url': getattr(organization, 'logo_url', None) if organization else None,
            } if organization else None,
            'students': students,
            'disciplines': disciplines,
            'sessions': sessions,
            'programs': programs,
            'statistics': statistics,
            'finances': finances,
            'upcoming_events': upcoming_events,
            'upcoming_competitions': upcoming_competitions,
            'quick_actions': [
                {'key': 'broadcast', 'label': 'Groupes de diffusion', 'icon': 'bullhorn', 'route': 'BroadcastGroups'},
                {'key': 'attendance', 'label': 'Présences', 'icon': 'clipboard-check', 'route': 'AttendanceManagement'},
                {'key': 'sessions', 'label': 'Mes sessions', 'icon': 'calendar', 'route': 'CoachSessions'},
                {'key': 'students', 'label': 'Mes élèves', 'icon': 'account-group', 'route': 'CoachStudents'},
                {'key': 'programs', 'label': 'Programmes', 'icon': 'book-education', 'route': 'CoachPrograms'},
            ],
        })

    def _get_organization(self, user, request):
        """Get organization for the coach."""
        organization = None

        # Try X-Tenant-ID header first
        tenant_id = request.META.get('HTTP_X_TENANT_ID') or request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                from apps.organizations.models import Organization
                organization = Organization.objects.filter(id=tenant_id).first()
            except Exception:
                pass

        if not organization:
            try:
                from apps.competitions.models import UserProfile
                profile = UserProfile.objects.filter(user=user).select_related('organization').first()
                if profile and profile.organization:
                    organization = profile.organization
            except Exception:
                pass

        if not organization:
            try:
                from apps.competitions.models import Practitioner
                practitioner = Practitioner.objects.filter(user=user).select_related('organization').first()
                if practitioner:
                    organization = getattr(practitioner, 'organization', None) or getattr(practitioner, 'club', None)
            except Exception:
                pass

        return organization

    def _get_coach_profile(self, user):
        """Get coach profile for the user."""
        try:
            from apps.competitions.models import CoachProfile, Practitioner
            practitioner = Practitioner.objects.filter(user=user).first()
            if practitioner:
                return CoachProfile.objects.filter(practitioner=practitioner).first()
        except Exception as e:
            print(f"Error getting coach profile: {e}")
        return None

    def _get_students(self, user, organization):
        """Get list of students under coach's supervision."""
        students = []
        try:
            from apps.competitions.models import Practitioner

            if organization:
                # Get all practitioners in the organization that the coach supervises
                # For now, get all practitioners in the organization
                practitioners_qs = Practitioner.objects.filter(
                    organization=organization,
                    is_active=True
                ).select_related('user').order_by('last_name', 'first_name')[:50]

                for p in practitioners_qs:
                    students.append({
                        'id': str(p.id),
                        'first_name': p.first_name or '',
                        'last_name': p.last_name or '',
                        'full_name': f"{p.first_name or ''} {p.last_name or ''}".strip(),
                        'email': p.email or (p.user.email if p.user else ''),
                        'phone': getattr(p, 'phone', '') or '',
                        'birth_date': p.birth_date.isoformat() if p.birth_date else None,
                        'grade': getattr(p, 'current_grade', {}).get('name', '') if hasattr(p, 'current_grade') else '',
                        'photo_url': getattr(p, 'photo_url', None) or getattr(p, 'avatar_url', None),
                        'status': 'active' if p.is_active else 'inactive',
                        'last_attendance': None,  # TODO: Get from attendance records
                    })
        except Exception as e:
            print(f"Error getting students: {e}")

        return {
            'total': len(students),
            'active': sum(1 for s in students if s['status'] == 'active'),
            'items': students[:20],  # Limit to 20 for initial load
        }

    def _get_disciplines(self, user, organization, coach_profile):
        """Get disciplines taught by the coach."""
        disciplines = []
        try:
            from apps.competitions.models.discipline import Discipline

            if organization:
                # Get organization's disciplines
                disciplines_qs = Discipline.objects.filter(
                    organization=organization,
                    is_active=True
                )

                for d in disciplines_qs:
                    disciplines.append({
                        'id': str(d.id),
                        'name': d.name,
                        'code': getattr(d, 'code', ''),
                        'description': getattr(d, 'description', ''),
                        'students_count': 0,  # TODO: Count students per discipline
                        'sessions_count': 0,  # TODO: Count sessions per discipline
                    })
        except Exception as e:
            print(f"Error getting disciplines: {e}")

        return {
            'total': len(disciplines),
            'items': disciplines,
        }

    def _get_sessions(self, user, organization):
        """Get coach's training sessions/schedule."""
        sessions = []
        try:
            from apps.competitions.models.event import Event, EventOccurrence
            from django.utils import timezone
            from datetime import timedelta

            if organization:
                # Get upcoming events/sessions for the organization
                now = timezone.now()
                week_ahead = now + timedelta(days=7)

                # Get regular events
                events_qs = Event.objects.filter(
                    organization=organization,
                    event_type__in=['training', 'course', 'session', 'class'],
                    start_date__gte=now.date(),
                    start_date__lte=week_ahead.date(),
                ).order_by('start_date', 'start_time')[:10]

                for e in events_qs:
                    sessions.append({
                        'id': str(e.id),
                        'title': e.title or e.name,
                        'type': e.event_type,
                        'date': e.start_date.isoformat() if e.start_date else None,
                        'start_time': e.start_time.strftime('%H:%M') if e.start_time else None,
                        'end_time': e.end_time.strftime('%H:%M') if e.end_time else None,
                        'location': e.location or '',
                        'participants_count': getattr(e, 'participants_count', 0),
                        'max_participants': getattr(e, 'max_participants', None),
                    })
        except Exception as e:
            print(f"Error getting sessions: {e}")

        return {
            'total': len(sessions),
            'this_week': len(sessions),
            'items': sessions,
        }

    def _get_programs(self, user, organization):
        """Get training programs managed by the coach."""
        programs = []
        # TODO: Implement when TrainingProgram model exists
        # For now, return sample data structure
        return {
            'total': len(programs),
            'items': programs,
        }

    def _get_statistics(self, user, organization, students_data):
        """Get coach statistics."""
        stats = {
            'students_count': students_data.get('total', 0),
            'active_students': students_data.get('active', 0),
            'sessions_this_month': 0,
            'sessions_this_week': 0,
            'attendance_rate': 0,
            'competitions_count': 0,
            'disciplines_count': 0,
        }

        try:
            from apps.competitions.models import Competition
            from django.utils import timezone
            from datetime import timedelta

            if organization:
                # Count competitions
                stats['competitions_count'] = Competition.objects.filter(
                    organizing_organization=organization
                ).count()

                # Count disciplines
                try:
                    from apps.competitions.models.discipline import Discipline
                    stats['disciplines_count'] = Discipline.objects.filter(
                        organization=organization,
                        is_active=True
                    ).count()
                except Exception:
                    pass

                # Count sessions this month
                try:
                    from apps.competitions.models.event import Event
                    now = timezone.now()
                    month_start = now.replace(day=1)
                    week_start = now - timedelta(days=now.weekday())

                    stats['sessions_this_month'] = Event.objects.filter(
                        organization=organization,
                        event_type__in=['training', 'course', 'session', 'class'],
                        start_date__gte=month_start.date(),
                    ).count()

                    stats['sessions_this_week'] = Event.objects.filter(
                        organization=organization,
                        event_type__in=['training', 'course', 'session', 'class'],
                        start_date__gte=week_start.date(),
                        start_date__lte=now.date(),
                    ).count()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error getting statistics: {e}")

        return stats

    def _get_finances(self, user, organization):
        """Get coach financial summary."""
        finances = {
            'balance': 0,
            'revenue_this_month': 0,
            'pending_payments': 0,
            'currency': 'EUR',
        }

        try:
            # Try to get finance data from the finance module
            from apps.finances.models import Transaction
            from django.utils import timezone
            from django.db.models import Sum

            if organization:
                now = timezone.now()
                month_start = now.replace(day=1)

                # Revenue this month
                revenue = Transaction.objects.filter(
                    organization=organization,
                    transaction_type='income',
                    date__gte=month_start,
                ).aggregate(total=Sum('amount'))

                finances['revenue_this_month'] = float(revenue.get('total') or 0)

                # Pending payments
                pending = Transaction.objects.filter(
                    organization=organization,
                    status='pending',
                ).aggregate(total=Sum('amount'))

                finances['pending_payments'] = float(pending.get('total') or 0)
        except Exception as e:
            print(f"Error getting finances: {e}")

        return finances

    def _get_upcoming_events(self, user, organization):
        """Get upcoming events for the coach."""
        events = []
        try:
            from apps.competitions.models.event import Event
            from django.utils import timezone

            if organization:
                now = timezone.now()
                events_qs = Event.objects.filter(
                    organization=organization,
                    start_date__gte=now.date(),
                ).order_by('start_date')[:5]

                for e in events_qs:
                    events.append({
                        'id': str(e.id),
                        'title': e.title or e.name,
                        'type': e.event_type,
                        'date': e.start_date.isoformat() if e.start_date else None,
                        'location': e.location or '',
                    })
        except Exception as e:
            print(f"Error getting events: {e}")

        return events

    def _get_upcoming_competitions(self, organization):
        """Get upcoming competitions."""
        competitions = []
        try:
            from apps.competitions.models import Competition
            from django.utils import timezone

            if organization:
                now = timezone.now()
                comps_qs = Competition.objects.filter(
                    organizing_organization=organization,
                    start_date__gte=now.date(),
                ).order_by('start_date')[:5]

                for c in comps_qs:
                    competitions.append({
                        'id': str(c.id),
                        'name': c.name,
                        'date': c.start_date.isoformat() if c.start_date else None,
                        'location': getattr(c, 'city', '') or getattr(c, 'location', '') or '',
                        'registrations_count': getattr(c, 'registrations_count', 0),
                    })
        except Exception as e:
            print(f"Error getting competitions: {e}")

        return competitions


class CoachStudentsAPIView(APIView):
    """
    API endpoint for Coach's students list with pagination.

    GET /api/v1/coach/students/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        page = int(request.query_params.get('page', 1))
        limit = int(request.query_params.get('limit', 20))
        search = request.query_params.get('search', '')

        students = []
        total = 0

        try:
            from apps.competitions.models import Practitioner, UserProfile

            # Get organization
            profile = UserProfile.objects.filter(user=user).select_related('organization').first()
            organization = profile.organization if profile else None

            if organization:
                qs = Practitioner.objects.filter(
                    organization=organization,
                    is_active=True
                ).select_related('user')

                if search:
                    qs = qs.filter(
                        models.Q(first_name__icontains=search) |
                        models.Q(last_name__icontains=search) |
                        models.Q(email__icontains=search)
                    )

                total = qs.count()
                offset = (page - 1) * limit
                practitioners = qs.order_by('last_name', 'first_name')[offset:offset + limit]

                for p in practitioners:
                    students.append({
                        'id': str(p.id),
                        'first_name': p.first_name or '',
                        'last_name': p.last_name or '',
                        'full_name': f"{p.first_name or ''} {p.last_name or ''}".strip(),
                        'email': p.email or (p.user.email if p.user else ''),
                        'phone': getattr(p, 'phone', '') or '',
                        'birth_date': p.birth_date.isoformat() if p.birth_date else None,
                        'photo_url': getattr(p, 'photo_url', None) or getattr(p, 'avatar_url', None),
                        'status': 'active' if p.is_active else 'inactive',
                    })
        except Exception as e:
            print(f"Error getting students: {e}")

        return Response({
            'students': students,
            'total': total,
            'page': page,
            'limit': limit,
            'has_more': (page * limit) < total,
        })


class CoachSessionsAPIView(APIView):
    """
    API endpoint for Coach's training sessions.

    GET /api/v1/coach/sessions/
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        user = request.user
        sessions = []

        try:
            from apps.competitions.models import UserProfile
            from apps.competitions.models.event import Event
            from django.utils import timezone
            from datetime import timedelta

            profile = UserProfile.objects.filter(user=user).select_related('organization').first()
            organization = profile.organization if profile else None

            if organization:
                now = timezone.now()
                # Get sessions for the next 30 days
                end_date = now + timedelta(days=30)

                events_qs = Event.objects.filter(
                    organization=organization,
                    event_type__in=['training', 'course', 'session', 'class'],
                    start_date__gte=now.date(),
                    start_date__lte=end_date.date(),
                ).order_by('start_date', 'start_time')

                for e in events_qs:
                    sessions.append({
                        'id': str(e.id),
                        'title': e.title or e.name,
                        'type': e.event_type,
                        'date': e.start_date.isoformat() if e.start_date else None,
                        'start_time': e.start_time.strftime('%H:%M') if e.start_time else None,
                        'end_time': e.end_time.strftime('%H:%M') if e.end_time else None,
                        'location': e.location or '',
                        'description': getattr(e, 'description', '') or '',
                        'participants_count': getattr(e, 'participants_count', 0),
                        'max_participants': getattr(e, 'max_participants', None),
                    })
        except Exception as e:
            print(f"Error getting sessions: {e}")

        return Response({
            'sessions': sessions,
            'total': len(sessions),
        })


class SubscriptionInfoView(APIView):
    """Mobile API endpoint returning subscription info for the current user's organization.

    GET /api/v1/subscription/info/

    Returns tier, member limits, pricing, and upgrade info.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get(self, request):
        from apps.competitions.utils.feature_control import get_user_organization
        from apps.finances.services.subscription_service import get_subscription_info
        from apps.finances.pricing_tiers import (
            get_market_tier_for_country, get_price_for_country,
        )

        organization = get_user_organization(request.user)
        info = get_subscription_info(organization)

        # Add pricing details based on org country
        country = ''
        if organization:
            country = getattr(organization, 'country', '') or ''
        market_tier = get_market_tier_for_country(country)
        price_yearly = float(get_price_for_country(country, 'yearly'))
        price_monthly = float(get_price_for_country(country, 'monthly'))

        return Response({
            'tier_name': info.get('tier_name', 'free'),
            'display_name': info.get('display_name', 'Free'),
            'is_free': info.get('is_free', True),
            'members_count': info.get('members_count', 0),
            'max_members': info.get('max_members', 10),
            'can_add_member': info.get('can_add_member', True),
            'remaining_slots': info.get('remaining_slots', 10),
            'is_at_limit': info.get('is_at_limit', False),
            'is_near_limit': info.get('is_near_limit', False),
            'pricing': {
                'market_tier': market_tier,
                'yearly_per_member': price_yearly,
                'monthly_per_member': price_monthly,
                'currency': 'EUR',
            },
            'upgrade_url': '/upgrade/',
        })