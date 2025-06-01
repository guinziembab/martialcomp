from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from datetime import datetime, timedelta
from collections import defaultdict

from ...models import (
    UserProfile, Practitioner, CompetitionRegistration, Competition, 
    PractitionerDiscipline, CompetitionCategory, Membership, License
)
from ...models.scoring_results import CompetitionResult
from ...models.training import TrainingSession, TrainingReservation, Attendance
from ...forms.practitioners import PractitionerForm

# Importer PractitionerGrade depuis l'application grades
try:
    from grades.models import PractitionerGrade, Grade
except ImportError:
    PractitionerGrade = None
    Grade = None

# Importer les modèles d'événements et notifications
try:
    from ...models.event import Event, EventParticipant
    from ...models.notifications import Notification
except ImportError:
    Event = None
    EventParticipant = None
    Notification = None

# Importer les modèles d'entraînement
try:
    from ...models.training import TrainingSession, TrainingReservation, Attendance
except ImportError:
    TrainingSession = None
    TrainingReservation = None
    Attendance = None


@login_required
def participant_dashboard_enhanced(request):
    """Dashboard amélioré pour les participants avec plus d'informations."""
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
        
        # Nouvelles statistiques
        total_score = 0
        average_rank = 0
        best_rank = None
        disciplines_stats = {}
        training_stats = {
            'total_sessions': 0,
            'this_month': 0,
            'attendance_rate': 0,
            'upcoming_sessions': []
        }
        membership_status = None
        license_status = None
        
        # Statistiques des événements
        upcoming_events = []
        
        # Notifications récentes
        recent_notifications = []
        
        # Statistiques par année
        yearly_stats = defaultdict(lambda: {
            'competitions': 0,
            'medals': 0,
            'average_rank': 0,
            'best_rank': None
        })
        
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
            
            # Get medals count and detailed results
            results = CompetitionResult.objects.filter(
                practitioner__in=practitioners
            ).select_related('competition', 'category')
            
            medals_count = results.filter(rank__lte=3).count()
            
            # Calculate average rank and best rank
            if results.exists():
                ranks = [r.rank for r in results if r.rank]
                if ranks:
                    average_rank = sum(ranks) / len(ranks)
                    best_rank = min(ranks)
            
            # Get recent results
            recent_results = results.order_by('-date')[:5]
            
            # Calculate total score
            total_score = results.aggregate(total=Sum('score'))['total'] or 0
            
            # Get available competitions
            registered_competition_ids = all_registrations.values_list('competition_id', flat=True)
            available_competitions = Competition.objects.filter(
                registration_deadline__gte=today,
                start_date__gte=today
            ).exclude(id__in=registered_competition_ids).select_related('discipline')[:5]
            
            # Statistiques par discipline
            for practitioner in practitioners:
                disciplines = practitioner.disciplines.all()
                for discipline in disciplines:
                    discipline_results = results.filter(
                        competition__discipline=discipline
                    )
                    
                    discipline_medals = discipline_results.filter(rank__lte=3).count()
                    discipline_participations = all_registrations.filter(
                        competition__discipline=discipline,
                        status='approved'
                    ).count()
                    
                    disciplines_stats[discipline.name] = {
                        'participations': discipline_participations,
                        'medals': discipline_medals,
                        'win_rate': (discipline_medals / discipline_participations * 100) if discipline_participations > 0 else 0
                    }
            
            # Membership et license status
            try:
                membership_status = Membership.objects.filter(
                    practitioner__in=practitioners,
                    is_active=True,
                    end_date__gte=today
                ).first()
                
                license_status = License.objects.filter(
                    practitioner__in=practitioners,
                    is_active=True,
                    expiry_date__gte=today
                ).first()
            except:
                pass
            
            # Training statistics
            if TrainingSession and TrainingReservation:
                try:
                    # Toutes les réservations d'entraînement
                    all_reservations = TrainingReservation.objects.filter(
                        practitioner__in=practitioners
                    )
                    
                    training_stats['total_sessions'] = all_reservations.count()
                    
                    # Sessions ce mois-ci
                    first_day_of_month = today.replace(day=1)
                    training_stats['this_month'] = all_reservations.filter(
                        date__gte=first_day_of_month
                    ).count()
                    
                    # Taux de présence
                    if Attendance:
                        total_attended = Attendance.objects.filter(
                            practitioner__in=practitioners,
                            status='present'
                        ).count()
                        
                        if training_stats['total_sessions'] > 0:
                            training_stats['attendance_rate'] = (total_attended / training_stats['total_sessions']) * 100
                    
                    # Prochaines sessions
                    training_stats['upcoming_sessions'] = all_reservations.filter(
                        date__gte=today
                    ).select_related('training_slot', 'training_slot__discipline').order_by('date')[:3]
                except:
                    pass
            
            # Upcoming events
            if Event and EventParticipant:
                try:
                    event_participations = EventParticipant.objects.filter(
                        practitioner__in=practitioners,
                        event__start_date__gte=today
                    ).select_related('event')
                    
                    upcoming_events = [ep.event for ep in event_participations[:3]]
                except:
                    pass
            
            # Recent notifications
            if Notification:
                try:
                    recent_notifications = Notification.objects.filter(
                        user=request.user,
                        is_read=False
                    ).order_by('-created_at')[:5]
                except:
                    pass
            
            # Statistiques par année
            for result in results:
                year = result.date.year
                yearly_stats[year]['competitions'] += 1
                if result.rank and result.rank <= 3:
                    yearly_stats[year]['medals'] += 1
                if result.rank:
                    if yearly_stats[year]['best_rank'] is None or result.rank < yearly_stats[year]['best_rank']:
                        yearly_stats[year]['best_rank'] = result.rank
            
            # Calculer les moyennes par année
            for year, stats in yearly_stats.items():
                year_results = results.filter(date__year=year)
                ranks = [r.rank for r in year_results if r.rank]
                if ranks:
                    stats['average_rank'] = sum(ranks) / len(ranks)
        
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
            
            # Nouvelles données
            'total_score': total_score,
            'average_rank': round(average_rank, 1) if average_rank else None,
            'best_rank': best_rank,
            'disciplines_stats': disciplines_stats,
            'training_stats': training_stats,
            'membership_status': membership_status,
            'license_status': license_status,
            'upcoming_events': upcoming_events,
            'recent_notifications': recent_notifications,
            'yearly_stats': dict(yearly_stats),
            
            # Données de graphiques
            'chart_labels': list(yearly_stats.keys()),
            'competitions_data': [stats['competitions'] for stats in yearly_stats.values()],
            'medals_data': [stats['medals'] for stats in yearly_stats.values()],
        }
        
        return render(request, 'competitions/dashboard/participant_enhanced.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')