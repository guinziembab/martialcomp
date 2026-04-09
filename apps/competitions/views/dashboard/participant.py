from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from datetime import datetime, timedelta
from ...models import (
    UserProfile, Practitioner, CompetitionRegistration, Competition, 
    PractitionerDiscipline, CompetitionCategory
)
# Maintenant que le conflit a été résolu en renommant le modèle TechnicalPerformance 
# en TechnicalPerformanceResult dans scoring_results.py, nous pouvons importer directement
from ...models.scoring_results import CompetitionResult, RankingEntry
from ...models.technical_scoring import CompetitionRanking
from ...forms.practitioners import PractitionerForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
# Importer PractitionerGrade depuis l'application grades
try:
    from apps.grades.models import PractitionerGrade
except ImportError:
    # Définir une classe stub en cas d'échec d'importation
    class PractitionerGrade:
        @classmethod
        def objects(cls):
            from django.db.models.query import QuerySet
            return QuerySet().none()

# Essai d'importation du modèle Grade depuis l'application grades
try:
    from apps.grades.models import Grade
except ImportError:
    Grade = None

# Import membership and license models
try:
    from ...models.membership import Membership
except ImportError:
    Membership = None

try:
    from ...models.federation import License
except ImportError:
    License = None

# Import for events and notifications
try:
    from ...models.event import Event
except ImportError:
    Event = None

try:
    from ...models.notifications import Notification, NotificationRecipient
except ImportError:
    Notification = None
    NotificationRecipient = None

# Import training models
try:
    from ...models.trainings import Training, TrainingSession, TrainingAttendance
except ImportError:
    Training = None
    TrainingSession = None
    TrainingAttendance = None

# Import support ticket model
try:
    from ...models.support import SupportTicket
except ImportError:
    SupportTicket = None

# Import finance models
try:
    from apps.finances.models import Payment, Invoice
except ImportError:
    Payment = None
    Invoice = None

# Import shop models 
try:
    from apps.shop.models import Order
except ImportError:
    Order = None

@login_required
def participant_dashboard(request):
    """Dashboard pour les participants."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard:index')
        
        # Get practitioner profile linked to this user
        practitioners = Practitioner.objects.filter(user=request.user)
        
        # Initialize counters and lists
        upcoming_competitions_count = 0
        upcoming_registrations = []
        medals_count = 0
        participations_count = 0
        pending_registrations_count = 0
        recent_results = []
        available_competitions = []
        
        # Initialize new metrics
        total_score = 0
        average_score = 0
        number_of_results = 0
        discipline_stats = []
        membership_status = None
        license_status = None
        training_stats = {
            'total_sessions': 0,
            'this_month': 0,
            'last_week': 0,
            'disciplines': []
        }
        upcoming_events = []
        recent_notifications = []
        performance_by_month = []
        wins_by_discipline = []
        recent_payments = []
        recent_orders = []
        support_tickets = []
        payment_stats = {
            'total_amount': 0,
            'this_month': 0,
            'pending': 0
        }
        order_stats = {
            'total_orders': 0,
            'pending': 0,
            'completed': 0
        }
        
        if practitioners.exists():
            # If user has practitioner profiles, get all their registrations
            all_registrations = CompetitionRegistration.objects.filter(
                practitioner__in=practitioners
            ).select_related('competition')
            
            # Count pending registrations (only for upcoming competitions, not past ones)
            today = timezone.now().date()
            pending_registrations_count = all_registrations.filter(
                status='pending',
                competition__start_date__gte=today  # Only count pending for future competitions
            ).count()

            # Get upcoming competitions the user is registered for
            upcoming_registrations = all_registrations.filter(
                competition__start_date__gte=today,
                status='approved'
            ).prefetch_related('categories').order_by('competition__start_date')[:5]

            # Get ALL upcoming competitions in the practitioner's discipline(s)
            # Collect from multiple sources: PractitionerDiscipline, M2M disciplines, primary_discipline, org disciplines
            practitioner_discipline_ids = set(
                PractitionerDiscipline.objects.filter(
                    practitioner__in=practitioners
                ).values_list('discipline_id', flat=True)
            )
            for p in practitioners:
                # From M2M disciplines field
                if hasattr(p, 'disciplines'):
                    practitioner_discipline_ids.update(
                        p.disciplines.values_list('id', flat=True)
                    )
                # From primary_discipline
                if hasattr(p, 'primary_discipline_id') and p.primary_discipline_id:
                    practitioner_discipline_ids.add(p.primary_discipline_id)
                # Fallback: organization disciplines
                if not practitioner_discipline_ids and p.organization and hasattr(p.organization, 'disciplines'):
                    practitioner_discipline_ids.update(
                        p.organization.disciplines.values_list('id', flat=True)
                    )
            practitioner_discipline_ids = list(practitioner_discipline_ids)

            if practitioner_discipline_ids:
                discipline_upcoming_competitions = Competition.objects.filter(
                    start_date__gte=today,
                    discipline_id__in=practitioner_discipline_ids,
                    status__in=['active', 'published', 'open', 'registration_open']
                ).select_related('discipline').order_by('start_date')
            else:
                # Fallback: show all upcoming competitions
                discipline_upcoming_competitions = Competition.objects.filter(
                    start_date__gte=today,
                    status__in=['active', 'published', 'open', 'registration_open']
                ).select_related('discipline').order_by('start_date')

            upcoming_competitions_count = discipline_upcoming_competitions.count()

            # Build list with registration status for each competition
            registered_comp_ids = dict(
                all_registrations.filter(
                    competition__start_date__gte=today
                ).values_list('competition_id', 'status')
            )
            available_competitions = []
            for comp in discipline_upcoming_competitions[:6]:
                reg_status = registered_comp_ids.get(comp.id)
                available_competitions.append({
                    'competition': comp,
                    'registration_status': reg_status,
                    'is_registered': reg_status in ('approved', 'pending', 'confirmed'),
                })

            # Get participations count - Include:
            # 1. All approved registrations
            # 2. Registrations for past competitions (regardless of status, they participated)
            approved_count = all_registrations.filter(status='approved').count()
            past_competitions_count = all_registrations.filter(
                competition__end_date__lt=today
            ).exclude(status='rejected').count()
            # Take the max to avoid double counting
            participations_count = max(approved_count, past_competitions_count)
            
            # Get results and calculate scores
            results = CompetitionResult.objects.filter(
                practitioner__in=practitioners
            ).select_related('competition', 'category')
            
            # Get medals count from multiple sources:
            # 1. CompetitionResult with rank <= 3
            # 2. CompetitionResult with medal field
            # 3. RankingEntry with rank <= 3
            # 4. CompetitionRanking with rank <= 3 (main source for technical competitions)
            medals_by_rank = results.filter(rank__lte=3).count()
            medals_by_field = results.filter(
                medal__in=['gold', 'silver', 'bronze']
            ).count()

            # Check RankingEntry for medals
            ranking_medals = RankingEntry.objects.filter(
                practitioner__in=practitioners,
                rank__lte=3
            ).count()

            # Check CompetitionRanking for medals (technical competitions)
            competition_ranking_medals = CompetitionRanking.objects.filter(
                practitioner__in=practitioners,
                rank__lte=3
            ).count()

            # Take the maximum from all sources
            medals_count = max(
                medals_by_rank,
                medals_by_field,
                ranking_medals,
                competition_ranking_medals
            )
            
            # Calculate total and average scores
            score_data = results.aggregate(
                total=Sum('score'),
                average=Avg('score'),
                count=Count('id')
            )
            total_score = score_data['total'] or 0
            average_score = round(score_data['average'] or 0, 2)
            number_of_results = score_data['count'] or 0
            
            # Get recent results
            recent_results = results.order_by('-date')[:5]
            
            # Calculate statistics by discipline
            discipline_data = results.values('competition__discipline__name').annotate(
                competitions=Count('id'),
                average_score=Avg('score'),
                medals=Count('id', filter=Q(rank__lte=3)),
                wins=Count('id', filter=Q(rank=1))
            )
            
            discipline_stats = []
            for stat in discipline_data:
                if stat['competition__discipline__name']:
                    discipline_stats.append({
                        'name': stat['competition__discipline__name'],
                        'competitions': stat['competitions'],
                        'average_score': round(stat['average_score'] or 0, 2),
                        'medals': stat['medals'],
                        'wins': stat['wins']
                    })
            
            # Get membership status
            if Membership:
                try:
                    today = timezone.now().date()
                    membership = Membership.objects.filter(
                        practitioner__in=practitioners,
                        status='active',
                        start_date__lte=today,
                        end_date__gte=today
                    ).latest('start_date')
                    membership_status = {
                        'active': membership.is_active,
                        'end_date': membership.end_date,
                        'type': membership.membership_type
                    }
                except Membership.DoesNotExist:
                    membership_status = {'active': False}
            
            # Get license status
            if License:
                try:
                    today = timezone.now().date()
                    license = License.objects.filter(
                        practitioner__in=practitioners,
                        status='active',
                        expiry_date__gte=today
                    ).latest('issue_date')
                    license_status = {
                        'active': license.is_valid,
                        'expiry_date': license.expiry_date,
                        'number': license.license_number
                    }
                except License.DoesNotExist:
                    license_status = {'active': False}
            
            # Get training statistics
            if TrainingSession and TrainingAttendance:
                now = timezone.now()
                last_month = now - timedelta(days=30)
                last_week = now - timedelta(days=7)
                
                # Get attendance records for practitioner
                attendance_records = TrainingAttendance.objects.filter(
                    practitioner__in=practitioners
                ).select_related('session')
                
                training_stats['total_sessions'] = attendance_records.count()
                training_stats['this_month'] = attendance_records.filter(
                    session__date__gte=last_month
                ).count()
                training_stats['last_week'] = attendance_records.filter(
                    session__date__gte=last_week
                ).count()
                
                # Training by discipline
                training_discipline_data = attendance_records.values(
                    'session__title'
                ).annotate(
                    sessions=Count('id')
                )
                training_stats['disciplines'] = [
                    {
                        'name': td['session__title'] or 'Formation',
                        'sessions': td['sessions']
                    }
                    for td in training_discipline_data
                ][:5]  # Limit to top 5 disciplines
            
            # Get upcoming events
            if Event:
                upcoming_events = Event.objects.filter(
                    start_date__gte=today,
                    participants__user__in=[p.user for p in practitioners]
                ).order_by('start_date')[:5]
            
            # Get recent notifications
            if Notification and NotificationRecipient:
                try:
                    recent_notifications = []
                    notification_recipients = NotificationRecipient.objects.filter(
                        user=request.user
                    ).select_related('notification').order_by('-notification__created_at')[:5]
                    
                    for recipient in notification_recipients:
                        notification = recipient.notification
                        recent_notifications.append({
                            'title': notification.title,
                            'message': notification.message,
                            'level': notification.level,
                            'created_at': notification.created_at,
                            'is_read': recipient.read_at is not None
                        })
                except Exception:
                    recent_notifications = []
            
            # Calculate performance by month (last 12 months)
            current_date = timezone.now().date()
            performance_by_month = []
            for i in range(11, -1, -1):
                month_date = current_date - timedelta(days=30*i)
                month_results = results.filter(
                    date__year=month_date.year,
                    date__month=month_date.month
                )
                month_data = month_results.aggregate(
                    competitions=Count('id'),
                    average_score=Avg('score'),
                    medals=Count('id', filter=Q(rank__lte=3))
                )
                performance_by_month.append({
                    'month': month_date.strftime('%B %Y'),
                    'competitions': month_data['competitions'] or 0,
                    'average_score': round(month_data['average_score'] or 0, 2),
                    'medals': month_data['medals'] or 0
                })
            
            # Calculate wins by discipline for chart
            wins_by_discipline = results.filter(rank=1).values(
                'competition__discipline__name'
            ).annotate(
                wins=Count('id')
            )
            wins_by_discipline = [
                {
                    'discipline': item['competition__discipline__name'],
                    'wins': item['wins']
                }
                for item in wins_by_discipline if item['competition__discipline__name']
            ]
            
            # available_competitions is already built above (lines ~202-209) with registration status

            # Get recent payments data
            if Payment:
                try:
                    today = timezone.now()
                    last_month = today - timedelta(days=30)
                    
                    # Get all payments for this user
                    user_payments = Payment.objects.filter(payer=request.user)
                    
                    # Recent payments
                    recent_payments = user_payments.order_by('-payment_date')[:5]
                    
                    # Payment statistics
                    payment_stats['total_amount'] = user_payments.aggregate(
                        total=Sum('amount'))['total'] or 0
                    payment_stats['this_month'] = user_payments.filter(
                        payment_date__gte=last_month
                    ).aggregate(total=Sum('amount'))['total'] or 0
                    payment_stats['pending'] = user_payments.filter(
                        status='pending'
                    ).count()
                except Exception:
                    recent_payments = []
            
            # Get recent orders data
            if Order:
                try:
                    # Get all orders for this user
                    user_orders = Order.objects.filter(user=request.user)
                    
                    # Recent orders
                    recent_orders = user_orders.order_by('-created_at')[:5]
                    
                    # Order statistics
                    order_stats['total_orders'] = user_orders.count()
                    order_stats['pending'] = user_orders.filter(status='pending').count()
                    order_stats['completed'] = user_orders.filter(status='completed').count()
                except Exception:
                    recent_orders = []
            
            # Get support tickets
            if SupportTicket:
                try:
                    support_tickets = SupportTicket.objects.filter(
                        created_by=request.user
                    ).order_by('-created_at')[:5]
                except Exception:
                    support_tickets = []
        
        # PROMPT 7 - Vérifier si l'utilisateur a un profil juge technique actif
        has_judge_profile = False
        pending_judge_performances = 0
        if practitioners.exists():
            # Vérifier si au moins un des pratiquants a un profil juge technique actif
            try:
                from ...models.judges import Judge
                from ...services.judge_service import JudgeService

                # Vérifier les conditions PROMPT 7: is_technical_judge=True ET active=True
                judge = Judge.objects.filter(
                    practitioner__in=practitioners,
                    is_technical_judge=True,
                    active=True
                ).first()

                if judge:
                    has_judge_profile = True
                    # Récupérer le nombre de performances en attente pour le badge
                    pending_judge_performances = JudgeService.get_pending_performances_count(judge)
            except ImportError:
                pass
            except Exception:
                pass

        # Get main practitioner info for welcome header
        main_practitioner = None
        main_practitioner_grade = None
        main_practitioner_discipline = None

        if practitioners.exists():
            main_practitioner = practitioners.first()

            # Get current grade
            try:
                practitioner_discipline = PractitionerDiscipline.objects.filter(
                    practitioner=main_practitioner
                ).select_related('discipline', 'current_grade').first()

                if practitioner_discipline:
                    main_practitioner_discipline = practitioner_discipline.discipline
                    main_practitioner_grade = practitioner_discipline.current_grade
            except Exception:
                pass

        # PROMPT 1/5 - Grade Progression Data
        grade_eligibility = None
        if main_practitioner:
            try:
                from apps.competitions.services.grade_eligibility import GradeEligibilityService
                grade_eligibility = GradeEligibilityService.check_eligibility(
                    main_practitioner,
                    main_practitioner_discipline
                )
            except ImportError:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur calcul eligibilite grade: {e}")

        # PROMPT 4 - Calendrier unifié - Mini widget événements
        calendar_events = []
        if main_practitioner:
            try:
                from apps.competitions.services.calendar_service import CalendarService
                service = CalendarService(main_practitioner)
                today = timezone.now().date()
                end_date = today + timedelta(days=30)  # Prochains 30 jours
                events = service.get_events(
                    start_date=today,
                    end_date=end_date,
                    types=['competition', 'exam', 'club', 'deadline'],
                    include_registered_only=False
                )
                # Limiter à 6 événements pour le mini widget
                calendar_events = [event.to_dict() for event in events[:6]]
            except ImportError:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur chargement calendrier: {e}")

        # PROMPT 5 - Performance combat
        combat_performance = None
        if main_practitioner:
            try:
                from apps.competitions.services.competition_closure_service import CompetitionClosureService
                combat_performance = CompetitionClosureService.get_combat_performance(
                    main_practitioner,
                    competition=None  # Toutes les compétitions
                )
            except ImportError:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur chargement performance combat: {e}")

        context = {
            'practitioners': practitioners,
            'main_practitioner': main_practitioner,
            'main_practitioner_grade': main_practitioner_grade,
            'main_practitioner_discipline': main_practitioner_discipline,
            'upcoming_competitions_count': upcoming_competitions_count,
            'medals_count': medals_count,
            'participations_count': participations_count,
            'pending_registrations_count': pending_registrations_count,
            'upcoming_registrations': upcoming_registrations,
            'recent_results': recent_results,
            'available_competitions': available_competitions,
            'today': timezone.now().date().isoformat(),
            
            # New metrics
            'total_score': total_score,
            'average_score': average_score,
            'number_of_results': number_of_results,
            'discipline_stats': discipline_stats,
            'membership_status': membership_status,
            'license_status': license_status,
            'training_stats': training_stats,
            'upcoming_events': upcoming_events,
            'recent_notifications': recent_notifications,
            'performance_by_month': performance_by_month,
            'wins_by_discipline': wins_by_discipline,
            
            # Added tracking data
            'recent_payments': recent_payments,
            'recent_orders': recent_orders,
            'support_tickets': support_tickets,
            'payment_stats': payment_stats,
            'order_stats': order_stats,
            
            # Judge profile flag (PROMPT 7)
            'has_judge_profile': has_judge_profile,
            'pending_judge_performances': pending_judge_performances,

            # Grade progression (PROMPT 1/5)
            'grade_eligibility': grade_eligibility,

            # Calendrier unifié (PROMPT 4)
            'calendar_events': calendar_events,

            # Performance combat (PROMPT 5)
            'combat_performance': combat_performance,
        }
        
        return render(request, 'competitions/dashboard/participant_modern.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')

@login_required
def participant_competitions(request):
    """Liste des compétitions pour le participant."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard:index')
        
        # Get practitioner profiles for this user
        practitioners = Practitioner.objects.filter(user=request.user)
        
        today = timezone.now().date()
        
        # Initialize lists
        upcoming_registrations = []
        past_registrations = []
        pending_registrations = []
        available_competitions = []
        
        if practitioners.exists():
            # Get all registrations for this user's practitioners
            all_registrations = CompetitionRegistration.objects.filter(
                practitioner__in=practitioners
            ).select_related('competition', 'practitioner').prefetch_related('categories')
            
            # Get upcoming (approved) competitions
            upcoming_registrations = all_registrations.filter(
                competition__start_date__gte=today,
                status='approved'
            ).order_by('competition__start_date')
            
            # Get past competitions
            past_registrations = all_registrations.filter(
                competition__start_date__lt=today,
                status='approved'
            ).order_by('-competition__start_date')
            
            # Get pending registrations
            pending_registrations = all_registrations.filter(
                status='pending'
            ).order_by('competition__start_date')
            
            # Get available competitions
            registered_competition_ids = all_registrations.values_list('competition_id', flat=True)
            available_competitions = Competition.objects.filter(
                registration_deadline__gte=today,
                start_date__gte=today
            ).exclude(id__in=registered_competition_ids).select_related('discipline').order_by('start_date')
        
        # Pagination for available competitions
        paginator = Paginator(available_competitions, 10)
        page_number = request.GET.get('page')
        available_competitions_page = paginator.get_page(page_number)
        
        context = {
            'practitioners': practitioners,
            'upcoming_registrations': upcoming_registrations,
            'past_registrations': past_registrations,
            'pending_registrations': pending_registrations,
            'available_competitions': available_competitions_page,
            'today': today.isoformat()
        }
        
        return render(request, 'competitions/dashboard/participant_competitions_modern.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')

@login_required
def participant_profile(request):
    """Profil du participant."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard:index')
        
        # Get practitioners for this user
        practitioners = Practitioner.objects.filter(user=request.user)
        
        # Handle profile update if a specific practitioner is selected
        practitioner_id = request.GET.get('id')
        form = None
        selected_practitioner = None
        practitioner_disciplines = []
        grade_history = []
        
        if practitioner_id and practitioners.filter(id=practitioner_id).exists():
            selected_practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            
            if request.method == 'POST':
                form = PractitionerForm(request.POST, request.FILES, instance=selected_practitioner)
                if form.is_valid():
                    form.save()
                    messages.success(request, _("Profil mis à jour avec succès!"))
                    return redirect('competitions:dashboard:participant_profile')
            else:
                form = PractitionerForm(instance=selected_practitioner)
            
            # Get disciplines and grades for this practitioner
            practitioner_disciplines = PractitionerDiscipline.objects.filter(
                practitioner=selected_practitioner
            ).select_related('discipline', 'current_grade')
            
            # Get grade history
            grade_history = PractitionerGrade.objects.filter(
                practitioner=selected_practitioner
            ).select_related('grade').order_by('-date_obtained')
        
        context = {
            'practitioners': practitioners,
            'selected_practitioner': selected_practitioner,
            'form': form,
            'practitioner_disciplines': practitioner_disciplines,
            'grade_history': grade_history
        }
        
        return render(request, 'competitions/dashboard/participant_profile.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')

@login_required
def participant_results(request):
    """Résultats et palmarès du participant (Prompt 3)."""
    import json
    from django.http import HttpResponse
    from django.template.loader import render_to_string

    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard:index')

        # Check if PDF export is requested
        export_format = request.GET.get('export')

        # Get practitioners for this user
        practitioners = Practitioner.objects.filter(user=request.user)

        # Get specific practitioner if ID is provided
        practitioner_id = request.GET.get('id')
        selected_practitioner = None

        if practitioner_id and practitioners.filter(id=practitioner_id).exists():
            selected_practitioner = get_object_or_404(Practitioner, id=practitioner_id)
        elif practitioners.exists():
            selected_practitioner = practitioners.first()

        # Filtres
        year_filter = request.GET.get('year')
        discipline_filter = request.GET.get('discipline')
        search_query = request.GET.get('q')

        # Convert filters to appropriate types with error handling
        year = None
        discipline_id = None
        try:
            if year_filter and year_filter.isdigit():
                year = int(year_filter)
        except (ValueError, TypeError):
            pass
        try:
            if discipline_filter and discipline_filter.isdigit():
                discipline_id = int(discipline_filter)
        except (ValueError, TypeError):
            pass

        # Utiliser le ResultsService pour les données du palmarès
        results_data = None
        available_years = []
        available_disciplines = []

        if selected_practitioner:
            try:
                from apps.competitions.services.results_service import ResultsService

                # Get dashboard data
                results_data = ResultsService.get_dashboard_data(
                    selected_practitioner,
                    year=year,
                    discipline_id=discipline_id,
                    use_cache=True
                )

                # Get available filters
                available_years = ResultsService.get_years_with_results(selected_practitioner)
                available_disciplines = ResultsService.get_disciplines_with_results(selected_practitioner)

            except ImportError as e:
                import logging
                logging.getLogger(__name__).error(f"Import ResultsService failed: {e}")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Erreur ResultsService: {e}")

        # Fallback to basic query if ResultsService failed
        if results_data is None:
            results = CompetitionResult.objects.filter(
                practitioner=selected_practitioner
            ).select_related('competition', 'category').order_by('-competition__start_date') if selected_practitioner else CompetitionResult.objects.none()

            gold_medals = results.filter(rank=1).count()
            silver_medals = results.filter(rank=2).count()
            bronze_medals = results.filter(rank=3).count()
        else:
            # Use ResultsService data
            results = results_data.competition_history
            gold_medals = results_data.medals.gold
            silver_medals = results_data.medals.silver
            bronze_medals = results_data.medals.bronze

        # Apply search filter if provided
        if search_query and results_data:
            results = [
                r for r in results_data.competition_history
                if search_query.lower() in r.get('competition_name', '').lower() or
                   search_query.lower() in r.get('category_name', '').lower()
            ]

        # Pagination for competition history
        if isinstance(results, list):
            # Manual pagination for list
            page_size = 10
            page_number = int(request.GET.get('page', 1))
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            results_page = results[start_idx:end_idx]
            total_pages = (len(results) + page_size - 1) // page_size
            has_next = page_number < total_pages
            has_previous = page_number > 1
        else:
            # Django pagination
            paginator = Paginator(results, 10)
            page_number = request.GET.get('page')
            results_page = paginator.get_page(page_number)
            has_next = results_page.has_next()
            has_previous = results_page.has_previous()
            total_pages = paginator.num_pages

        # Prepare Chart.js data
        chart_data = {}
        if results_data:
            # Medals by discipline chart - always get ALL disciplines (no filter)
            # to show complete picture in the pie chart
            try:
                all_disciplines_data = ResultsService.get_points_by_discipline(
                    selected_practitioner, year=year  # Only filter by year, not discipline
                )
                chart_data['medals_by_discipline'] = {
                    'labels': [d.discipline_name for d in all_disciplines_data],
                    'data': [d.medals_count for d in all_disciplines_data],
                }
            except Exception:
                chart_data['medals_by_discipline'] = {'labels': [], 'data': []}

            # Points evolution chart (last 12 months)
            chart_data['points_evolution'] = {
                'labels': [r.month for r in results_data.ranking_evolution],
                'data': [r.points for r in results_data.ranking_evolution],
            }

            # Ranking evolution chart
            chart_data['ranking_evolution'] = {
                'labels': [r.month for r in results_data.ranking_evolution],
                'data': [r.rank for r in results_data.ranking_evolution],
            }

        context = {
            'practitioners': practitioners,
            'selected_practitioner': selected_practitioner,
            'results': results_page,
            'search_query': search_query,
            'gold_medals': gold_medals,
            'silver_medals': silver_medals,
            'bronze_medals': bronze_medals,

            # Prompt 3: Palmarès data
            'results_data': results_data,
            'medals_timeline': results_data.medals_timeline if results_data else [],
            'competition_stats': results_data.stats if results_data else None,
            'points_by_discipline': results_data.points_by_discipline if results_data else [],
            'grades_history': results_data.grades if results_data else [],

            # Filters
            'available_years': available_years,
            'available_disciplines': available_disciplines,
            'selected_year': year,
            'selected_discipline': discipline_id,

            # Pagination info
            'page_number': page_number,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_previous': has_previous,

            # Chart.js data (JSON serialized)
            'chart_data_json': json.dumps(chart_data),
        }

        # Handle PDF export
        if export_format == 'pdf' and selected_practitioner and results_data:
            # Get discipline and grade for PDF
            discipline = None
            current_grade = None
            try:
                practitioner_discipline = PractitionerDiscipline.objects.filter(
                    practitioner=selected_practitioner
                ).select_related('discipline', 'current_grade').first()
                if practitioner_discipline:
                    discipline = practitioner_discipline.discipline
                    current_grade = practitioner_discipline.current_grade
            except Exception:
                pass

            pdf_context = {
                'practitioner': selected_practitioner,
                'discipline': discipline,
                'current_grade': current_grade,
                'medals': results_data.medals,
                'stats': results_data.stats,
                'competition_history': results_data.competition_history,
                'grades': results_data.grades,
                'year': year,
                'generated_date': timezone.now(),
            }

            # Try to generate PDF with weasyprint or xhtml2pdf
            pdf_generated = False

            # Method 1: Try WeasyPrint
            try:
                from weasyprint import HTML
                html_string = render_to_string(
                    'competitions/dashboard/palmares_pdf.html',
                    pdf_context
                )
                html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
                pdf_file = html.write_pdf()

                response = HttpResponse(pdf_file, content_type='application/pdf')
                filename = f"palmares_{selected_practitioner.first_name}_{selected_practitioner.last_name}"
                if year:
                    filename += f"_{year}"
                filename += ".pdf"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except ImportError:
                pass
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"WeasyPrint error: {e}")

            # Method 2: Try xhtml2pdf
            if not pdf_generated:
                try:
                    from xhtml2pdf import pisa
                    from io import BytesIO

                    html_string = render_to_string(
                        'competitions/dashboard/palmares_pdf.html',
                        pdf_context
                    )
                    result = BytesIO()
                    pdf = pisa.pisaDocument(BytesIO(html_string.encode("UTF-8")), result)

                    if not pdf.err:
                        response = HttpResponse(result.getvalue(), content_type='application/pdf')
                        filename = f"palmares_{selected_practitioner.first_name}_{selected_practitioner.last_name}"
                        if year:
                            filename += f"_{year}"
                        filename += ".pdf"
                        response['Content-Disposition'] = f'attachment; filename="{filename}"'
                        return response
                except ImportError:
                    pass
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"xhtml2pdf error: {e}")

            # Fallback: Return HTML version with print instructions
            pdf_context['show_print_instructions'] = True
            return render(request, 'competitions/dashboard/palmares_pdf.html', pdf_context)

        return render(request, 'competitions/dashboard/participant_results.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')


@login_required
def update_participant_photo(request):
    """Met à jour la photo de profil du pratiquant."""
    if request.method != 'POST':
        messages.error(request, _("Méthode non autorisée."))
        return redirect('competitions:dashboard:participant')

    try:
        # Récupérer le profil utilisateur
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette fonctionnalité."))
            return redirect('competitions:dashboard:index')

        # Récupérer le practitioner principal de l'utilisateur
        practitioner = Practitioner.objects.filter(user=request.user).first()

        if not practitioner:
            messages.error(request, _("Profil pratiquant non trouvé."))
            return redirect('competitions:dashboard:participant')

        # Vérifier si l'utilisateur veut supprimer la photo
        remove_photo = request.POST.get('remove_photo')
        if remove_photo:
            # Supprimer la photo actuelle
            if practitioner.photo:
                practitioner.photo.delete(save=False)
                practitioner.photo = None
                practitioner.save()
                messages.success(request, _("Photo de profil supprimée avec succès."))
            return redirect('competitions:dashboard:participant')

        # Vérifier si une nouvelle photo a été envoyée
        new_photo = request.FILES.get('photo')
        if new_photo:
            # Vérifier la taille du fichier (max 5 Mo)
            if new_photo.size > 5 * 1024 * 1024:
                messages.error(request, _("La taille du fichier ne doit pas dépasser 5 Mo."))
                return redirect('competitions:dashboard:participant')

            # Vérifier le type du fichier
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if new_photo.content_type not in allowed_types:
                messages.error(request, _("Format de fichier non autorisé. Utilisez JPG, PNG, GIF ou WebP."))
                return redirect('competitions:dashboard:participant')

            # Supprimer l'ancienne photo si elle existe
            if practitioner.photo:
                practitioner.photo.delete(save=False)

            # Enregistrer la nouvelle photo
            practitioner.photo = new_photo
            practitioner.save()
            messages.success(request, _("Photo de profil mise à jour avec succès."))
        else:
            messages.info(request, _("Aucune photo sélectionnée."))

        return redirect('competitions:dashboard:participant')

    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé."))
        return redirect('welcome')
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la mise à jour de la photo: {str(e)}")
        messages.error(request, _("Une erreur est survenue lors de la mise à jour de la photo."))
        return redirect('competitions:dashboard:participant')


@login_required
def participant_calendar(request):
    """
    Page calendrier unifié pour le participant (Prompt 4).
    Affiche un calendrier FullCalendar avec tous les événements:
    - Compétitions
    - Examens de grade
    - Événements du club
    - Deadlines d'inscription
    """
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard:index')

        # Get practitioner profile
        practitioners = Practitioner.objects.filter(user=request.user)
        main_practitioner = practitioners.first()

        # Get disciplines for filter
        disciplines = []
        if main_practitioner:
            try:
                from ...models import Discipline
                practitioner_disciplines = PractitionerDiscipline.objects.filter(
                    practitioner=main_practitioner
                ).select_related('discipline')
                disciplines = [pd.discipline for pd in practitioner_disciplines if pd.discipline]
            except Exception:
                pass

        context = {
            'practitioner': main_practitioner,
            'practitioners': practitioners,
            'disciplines': disciplines,
            'page_title': _("Mon calendrier"),
        }

        return render(request, 'competitions/dashboard/participant_calendar.html', context)

    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')
