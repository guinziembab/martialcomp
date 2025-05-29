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
from ...models.scoring_results import CompetitionResult
from ...forms.practitioners import PractitionerForm
# Importer PractitionerGrade depuis l'application grades
try:
    from grades.models import PractitionerGrade
except ImportError:
    # Définir une classe stub en cas d'échec d'importation
    class PractitionerGrade:
        @classmethod
        def objects(cls):
            from django.db.models.query import QuerySet
            return QuerySet().none()

# Essai d'importation du modèle Grade depuis l'application grades
try:
    from grades.models import Grade
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
    from finances.models import Payment, Invoice
except ImportError:
    Payment = None
    Invoice = None

# Import shop models 
try:
    from shop.models import Order
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
            
            # Count pending registrations
            pending_registrations_count = all_registrations.filter(status='pending').count()
            
            # Get upcoming competitions for this user
            today = timezone.now().date()
            upcoming_registrations = all_registrations.filter(
                competition__start_date__gte=today,
                status='approved'
            ).prefetch_related('categories').order_by('competition__start_date')[:5]
            
            upcoming_competitions_count = upcoming_registrations.count()
            
            # Get participations count (past and upcoming approved registrations)
            participations_count = all_registrations.filter(status='approved').count()
            
            # Get results and calculate scores
            results = CompetitionResult.objects.filter(
                practitioner__in=practitioners
            ).select_related('competition', 'category')
            
            # Get medals count
            medals_count = results.filter(rank__lte=3).count()
            
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
            
            # Get available competitions
            registered_competition_ids = all_registrations.values_list('competition_id', flat=True)
            available_competitions = Competition.objects.filter(
                registration_deadline__gte=today,
                start_date__gte=today
            ).exclude(id__in=registered_competition_ids).select_related('discipline')[:5]
            
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
        
        context = {
            'practitioners': practitioners,
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
        }
        
        return render(request, 'competitions/dashboard/participant.html', context)
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
        
        return render(request, 'competitions/dashboard/participant_competitions.html', context)
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
    """Résultats du participant."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'participant':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard:index')
        
        # Get practitioners for this user
        practitioners = Practitioner.objects.filter(user=request.user)
        
        # Get specific practitioner if ID is provided
        practitioner_id = request.GET.get('id')
        selected_practitioner = None
        
        if practitioner_id and practitioners.filter(id=practitioner_id).exists():
            selected_practitioner = get_object_or_404(Practitioner, id=practitioner_id)
            results = CompetitionResult.objects.filter(
                practitioner=selected_practitioner
            ).select_related('competition', 'category').order_by('-date')
        else:
            # Get results for all practitioners
            results = CompetitionResult.objects.filter(
                practitioner__in=practitioners
            ).select_related('competition', 'category', 'practitioner').order_by('-date')
        
        # Filter results by competition name if search parameter is provided
        search_query = request.GET.get('q')
        if search_query:
            results = results.filter(
                Q(competition__title__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(results, 10)
        page_number = request.GET.get('page')
        results_page = paginator.get_page(page_number)
        
        context = {
            'practitioners': practitioners,
            'selected_practitioner': selected_practitioner,
            'results': results_page,
            'search_query': search_query
        }
        
        return render(request, 'competitions/dashboard/participant_results.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')