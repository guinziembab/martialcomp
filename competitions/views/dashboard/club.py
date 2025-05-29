from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q
from django.db import models
import logging

from ...models import Club, Practitioner, Competition, CompetitionRegistration, Notification
from finances.models import PaymentAttempt, Invoice
from shop.models import Order

logger = logging.getLogger(__name__)

@login_required
def club_dashboard(request):
    """
    Tableau de bord pour les responsables de club.
    Affiche les statistiques et les informations relatives au club.
    """
    # Récupérer le club associé à l'utilisateur
    club = None
    
    # Essayer de récupérer le club depuis différentes sources possibles
    if hasattr(request.user, 'club') and request.user.club:
        club = request.user.club
    else:
        # Sinon, chercher un club dont l'utilisateur est propriétaire
        club = Club.objects.filter(owner=request.user).first()
    
    # Si aucun club n'est trouvé, rediriger vers la création de club
    if not club:
        messages.warning(request, _("Vous devez d'abord créer ou rejoindre un club pour accéder au tableau de bord."))
        
        # Essayer différentes URLs de redirection dans un ordre logique
        redirect_urls = [
            'competitions:clubs:create',
            'competitions:club:create',
            'competitions:onboarding:club_creation',
            'competitions:welcome'
        ]
        
        for url_name in redirect_urls:
            try:
                return redirect(url_name)
            except:
                continue
        
        # Fallback ultime si aucune URL ne fonctionne
        return redirect('/')
    
    # Récupérer les compétitions que ce club peut gérer
    competitions_to_manage = Competition.objects.none()
    
    if club:
        try:
            # Vérifier si le club a une organisation associée
            club_organization = club.organization or getattr(club, 'as_organization', None)
            
            if club_organization:
                # Récupérer les compétitions où l'organisation du club est organisatrice
                competitions_to_manage = Competition.objects.filter(
                    organizing_organization=club_organization
                ).distinct().select_related('discipline').prefetch_related('registrations', 'categories')
            else:
                logger.warning(f"Aucune organisation associée trouvée pour le club {club.name} (id={club.id})")
            
            # Si le modèle Competition a un champ manager, ajouter les compétitions où l'utilisateur est manager
            if hasattr(Competition, 'manager'):
                from django.db.models import Q
                competitions_to_manage = competitions_to_manage | Competition.objects.filter(
                    manager=request.user
                ).distinct()
            
            # Debug: Afficher le nombre de compétitions trouvées
            logger.info(f"Compétitions à gérer trouvées: {competitions_to_manage.count()}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des compétitions à gérer: {str(e)}")
            # Fallback simple - prendre uniquement les compétitions du club
            # Vérifier si le club a une organisation associée
            club_organization = club.organization or getattr(club, 'as_organization', None)
            
            if club_organization:
                competitions_to_manage = Competition.objects.filter(organizing_organization=club_organization)
            else:
                logger.warning(f"Aucune organisation associée trouvée pour le club {club.name} (id={club.id})")
    
    # Statistiques du club
    stats = {}
    
    # Date actuelle pour les calculs
    now = timezone.now().date()
    
    # Nombre total de pratiquants
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    if club_organization:
        stats['total_practitioners'] = Practitioner.objects.filter(organization=club_organization).count()
    else:
        logger.warning(f"Aucune organisation associée trouvée pour le club {club.name} (id={club.id})")
        stats['total_practitioners'] = 0
    
    # Récupérer les disciplines du club
    club_disciplines = club.disciplines.all()
    
    # Récupérer les compétitions organisées par le club
    # Utiliser organizing_organization avec l'organisation associée au club
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    club_competitions = Competition.objects.none()
    if club_organization:
        club_competitions = Competition.objects.filter(
            organizing_organization=club_organization  # Compétitions associées à l'organisation du club
        ).order_by('-start_date')
    
    stats['club_competitions'] = club_competitions.count()
    
    # Récupérer les compétitions à venir (où le club peut participer)
    upcoming_competitions = Competition.objects.filter(
        end_date__gte=now,
        status__in=['published', 'open']
    ).exclude(
        id__in=club_competitions.values_list('id', flat=True)  # Exclure les compétitions du club
    ).order_by('start_date')[:5]
    
    stats['upcoming_competitions'] = upcoming_competitions.count()
    
    # Nombre d'inscriptions actives (pratiquants de ce club inscrits à des compétitions à venir)
    if club_organization:
        active_registrations = CompetitionRegistration.objects.filter(
            practitioner__organization=club_organization,
            competition__end_date__gte=now
        )
    else:
        active_registrations = CompetitionRegistration.objects.none()
    stats['active_registrations'] = active_registrations.count()
    
    # Récupérer les inscriptions récentes pour l'onglet
    recent_registrations = active_registrations.order_by('-registration_date')[:5]
    
    # Nombre de juges/arbitres du club
    try:
        from ...models import Judge
        # Méthode 1: Utiliser le modèle Judge
        if club_organization:
            club_judges = Judge.objects.filter(practitioner__organization=club_organization)
        else:
            club_judges = Judge.objects.none()
        stats['judges_count'] = club_judges.count()
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des juges: {str(e)}")
        try:
            # Méthode 2: Utiliser les qualifications
            if club_organization:
                stats['judges_count'] = Practitioner.objects.filter(
                    organization=club_organization,
                    qualifications__isnull=False
                ).distinct().count()
            else:
                stats['judges_count'] = 0
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des qualifications: {str(e)}")
            # Fallback : compter les pratiquants marqués comme juges
            stats['judges_count'] = 0
    
    # Récupérer les 5 pratiquants les plus récemment ajoutés
    if club_organization:
        try:
            recent_practitioners = Practitioner.objects.filter(
                organization=club_organization
            ).order_by('-created_at', '-id')[:5]  # Utiliser created_at si disponible
        except Exception as e:
            logger.error(f"Erreur lors du tri par created_at: {str(e)}")
            recent_practitioners = Practitioner.objects.filter(
                organization=club_organization
            ).order_by('-id')[:5]  # Fallback sur id
    else:
        recent_practitioners = Practitioner.objects.none()
    
    # Récupérer les affectations des juges si disponible
    judge_assignments = []
    try:
        from ...models import JudgeAssignment
        if club_organization:
            judge_assignments = JudgeAssignment.objects.filter(
                registration__practitioner__organization=club_organization,
                category__competition__end_date__gte=now
            )
        else:
            judge_assignments = JudgeAssignment.objects.none().select_related(
            'registration__practitioner',
            'category__competition'
        ).order_by('category__competition__start_date')[:10]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des affectations: {str(e)}")
    
    # Messages d'information ou de débogage
    if not upcoming_competitions.exists():
        if not club_disciplines.exists():
            messages.info(
                request, 
                _("Votre club n'a pas encore de discipline assignée. Veuillez configurer les disciplines "
                  "pour voir les compétitions disponibles.")
            )
    
    if stats['total_practitioners'] == 0:
        messages.info(
            request,
            _("Vous n'avez pas encore de pratiquants dans votre club. Commencez par ajouter des membres.")
        )
    
    # Récupérer les paiements récents
    recent_payments = []
    try:
        from finances.models import PaymentAttempt
        # Obtenir les pratiquants du club
        if club_organization:
            club_practitioners = Practitioner.objects.filter(organization=club_organization)
            practitioner_users = set(club_practitioners.values_list('user_id', flat=True).distinct())
            
            # Obtenir les paiements récents pour les pratiquants du club
            recent_payments = PaymentAttempt.objects.filter(
                transaction__created_by__id__in=practitioner_users
            ).select_related('transaction', 'transaction__created_by', 'payment_method', 'transaction__category'
            ).order_by('-initiated_at')[:10]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paiements récents: {str(e)}")

    # Récupérer les sessions d'entraînement récentes
    recent_sessions = []
    attendance_stats = {}
    top_attendees = []
    try:
        from ...models import TrainingSession, Attendance
        from django.db.models import Count, Avg, F
        from datetime import timedelta
        
        # Sessions récentes du club
        recent_sessions = TrainingSession.objects.filter(
            training_slot__club=club,
            date__gte=now - timedelta(days=30)
        ).select_related('training_slot', 'training_slot__discipline', 'actual_instructor'
        ).order_by('-date')[:10]
        
        # Calculer les statistiques pour chaque session
        for session in recent_sessions:
            attendance_data = Attendance.objects.filter(session=session).aggregate(
                total_count=Count('id'),
                presents_count=Count('id', filter=Q(status='present')),
            )
            session.total_count = attendance_data['total_count']
            session.presents_count = attendance_data['presents_count']
            session.attendance_rate = (session.presents_count / session.total_count * 100) if session.total_count > 0 else 0
        
        # Statistiques globales
        month_start = now.replace(day=1)
        attendance_stats['month_sessions'] = TrainingSession.objects.filter(
            training_slot__club=club,
            date__gte=month_start
        ).count()
        
        attendance_stats['total_attendances'] = Attendance.objects.filter(
            session__training_slot__club=club,
            status='present'
        ).count()
        
        # Taux de présence moyen
        avg_rate = TrainingSession.objects.filter(
            training_slot__club=club,
            date__gte=now - timedelta(days=30)
        ).annotate(
            presents_count=Count('attendances', filter=Q(attendances__status='present')),
            total_count=Count('attendances')
        ).aggregate(
            avg_rate=Avg(F('presents_count') * 100.0 / F('total_count'))
        )
        attendance_stats['average_rate'] = avg_rate['avg_rate'] or 0
        
        # Top pratiquants assidus
        top_attendees = Attendance.objects.filter(
            session__training_slot__club=club,
            status='present',
            session__date__gte=now - timedelta(days=30)
        ).values('practitioner', 'practitioner__last_name', 'practitioner__first_name'
        ).annotate(attendance_count=Count('id')
        ).order_by('-attendance_count')[:5]
        
        # Ajouter le nom complet pour chaque pratiquant
        for attendee in top_attendees:
            attendee['practitioner'] = type('obj', (object,), {
                'full_name': f"{attendee['practitioner__first_name']} {attendee['practitioner__last_name']}"
            })
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données d'entraînement: {str(e)}")

    # Récupérer les commandes en ligne récentes
    recent_orders = []
    order_stats = {}
    try:
        from shop.models import Order
        from django.db.models import Sum
        
        # Commandes récentes du club
        recent_orders = Order.objects.filter(
            club=club
        ).select_related('user').order_by('-created_at')[:10]
        
        # Statistiques des commandes
        order_counts = Order.objects.filter(club=club).values('status').annotate(count=Count('id'))
        status_counts = {item['status']: item['count'] for item in order_counts}
        
        order_stats['total_orders'] = Order.objects.filter(club=club).count()
        order_stats['pending_orders'] = status_counts.get('pending', 0)
        order_stats['processing_orders'] = status_counts.get('processing', 0)
        
        # Chiffre d'affaires total
        revenue = Order.objects.filter(
            club=club,
            status__in=['delivered', 'shipped', 'processing']
        ).aggregate(total=Sum('total'))
        order_stats['total_revenue'] = revenue['total'] or 0
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des commandes: {str(e)}")

    # Récupérer les notifications récentes
    recent_notifications = []
    unread_count = 0
    try:
        from ...models import Notification
        
        # Toutes les notifications récentes
        recent_notifications = Notification.objects.filter(
            user=request.user,
            created_at__gte=now - timedelta(days=30)
        ).order_by('-created_at')[:10]
        
        # Nombre de notifications non lues
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des notifications: {str(e)}")

    # Récupérer les tickets de support récents
    recent_tickets = []
    ticket_stats = {}
    try:
        from ...models import SupportTicket
        
        # Tickets récents créés par les pratiquants du club
        if club_organization:
            club_practitioners = Practitioner.objects.filter(organization=club_organization)
            practitioner_users = set(club_practitioners.values_list('user_id', flat=True).distinct())
            
            recent_tickets = SupportTicket.objects.filter(
                user__id__in=practitioner_users
            ).order_by('-created_at')[:10]
            
            # Statistiques des tickets
            ticket_counts = SupportTicket.objects.filter(
                user__id__in=practitioner_users
            ).values('status').annotate(count=Count('id'))
            status_counts = {item['status']: item['count'] for item in ticket_counts}
            
            ticket_stats['total_tickets'] = SupportTicket.objects.filter(user__id__in=practitioner_users).count()
            ticket_stats['open_tickets'] = status_counts.get('open', 0)
            ticket_stats['in_progress_tickets'] = status_counts.get('in_progress', 0)
            ticket_stats['resolved_tickets'] = status_counts.get('resolved', 0)
            
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tickets de support: {str(e)}")

    # Préparer le contexte pour le template
    context = {
        'club': club,
        'stats': stats,
        'club_competitions': club_competitions,  # Les compétitions du club
        'upcoming_competitions': upcoming_competitions,  # Compétitions à venir
        'competitions_to_manage': competitions_to_manage,  # Compétitions à gérer (NOUVEAU)
        'recent_practitioners': recent_practitioners,
        'recent_registrations': recent_registrations,
        'club_disciplines': club_disciplines,
        'judge_assignments': judge_assignments,
        'recent_payments': recent_payments,  # Ajout des paiements récents
        'recent_sessions': recent_sessions,  # Ajout des sessions d'entraînement
        'attendance_stats': attendance_stats,  # Ajout des statistiques de présence
        'top_attendees': top_attendees,  # Ajout des pratiquants assidus
        'recent_orders': recent_orders,  # Ajout des commandes récentes
        'order_stats': order_stats,  # Ajout des statistiques de commandes
        'recent_notifications': recent_notifications,  # Ajout des notifications récentes
        'unread_count': unread_count,  # Ajout du nombre de notifications non lues
        'recent_tickets': recent_tickets,  # Ajout des tickets de support récents
        'ticket_stats': ticket_stats,  # Ajout des statistiques de tickets
        'current_date': now,
        'page_title': _("Tableau de bord du club"),
        'section': 'dashboard'
    }
    
    # Ajouter club_judges au contexte si disponible
    if 'club_judges' in locals():
        context['club_judges'] = club_judges
    
    return render(request, 'competitions/dashboard/club.html', context)