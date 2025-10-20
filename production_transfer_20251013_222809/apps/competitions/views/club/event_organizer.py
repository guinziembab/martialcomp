"""
Interface professionnelle pour l'organisation d'événements sportifs
Vue complète pour les clubs/organisations qui hébergent des compétitions
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Count, Q, Sum, Avg
from django.http import JsonResponse
from datetime import datetime, timedelta
import json

from ...models import Competition, Event, CompetitionCategory, CompetitionRegistration
from ...models import Practitioner, Judge
from apps.finances.models import Invoice, PaymentAttempt, Transaction
from apps.core.isolation import get_organization_queryset


@login_required
def event_organizer_dashboard(request):
    """
    Dashboard professionnel pour l'organisation d'événements sportifs
    Interface complète de gestion : inscriptions, paiements, planning, suivi temps réel
    """
    
    # Récupérer l'organisation/club de l'utilisateur
    from ...utils.permission_helpers import get_user_club
    club = get_user_club(request)
    
    if not club:
        try:
            messages.error(request, _("Vous devez être responsable d'organisation pour accéder à cette interface."))
        except:
            pass
        return redirect('competitions:dashboard:club')
    
    organization = club.organization or getattr(club, 'as_organization', None)
    if not organization:
        try:
            messages.warning(request, _("Configuration d'organisation requise pour organiser des événements."))
        except:
            pass
        return redirect('competitions:club:competitions')
    
    # Date actuelle pour les calculs
    now = timezone.now()
    today = now.date()
    
    # === ÉVÉNEMENTS ORGANISÉS PAR CETTE ORGANISATION ===
    
    # Compétitions en cours d'organisation
    ongoing_competitions = Competition.objects.filter(
        organizing_organization=organization,
        status__in=['draft', 'published', 'ongoing'],
        end_date__gte=today
    ).order_by('start_date')
    
    # Événements génériques organisés
    ongoing_events = Event.objects.filter(
        organization=organization,
        start_date__gte=today,
        is_archived=False
    ).order_by('start_date')
    
    # Événements terminés récemment (pour les analyses)
    recent_completed = Competition.objects.filter(
        organizing_organization=organization,
        status='completed',
        end_date__gte=today - timedelta(days=90)
    ).order_by('-end_date')[:5]
    
    # === STATISTIQUES GLOBALES ===
    
    # Statistiques des inscriptions
    total_registrations = CompetitionRegistration.objects.filter(
        competition__organizing_organization=organization,
        competition__start_date__gte=today
    ).count()
    
    confirmed_registrations = CompetitionRegistration.objects.filter(
        competition__organizing_organization=organization,
        competition__start_date__gte=today,
        status='confirmed'
    ).count()
    
    pending_registrations = CompetitionRegistration.objects.filter(
        competition__organizing_organization=organization,
        competition__start_date__gte=today,
        status='pending'
    ).count()
    
    # Statistiques financières
    financial_stats = get_financial_overview(organization, today)
    
    # === DONNÉES DÉTAILLÉES PAR ÉVÉNEMENT ===
    
    event_details = {}
    
    # Analyser chaque compétition
    for competition in ongoing_competitions:
        registrations = CompetitionRegistration.objects.filter(
            competition=competition
        ).select_related('practitioner')
        
        categories = CompetitionCategory.objects.filter(
            competition=competition
        ).annotate(participant_count=Count('registrations'))
        
        # Revenus prévisionnels
        expected_revenue = calculate_expected_revenue(competition, registrations)
        
        # Statut de préparation
        preparation_status = assess_preparation_status(competition, categories, registrations)
        
        event_details[competition.id] = {
            'competition': competition,
            'registrations': registrations,
            'categories': categories,
            'stats': {
                'total_participants': registrations.count(),
                'confirmed_participants': registrations.filter(status='confirmed').count(),
                'pending_participants': registrations.filter(status='pending').count(),
                'categories_count': categories.count(),
                'expected_revenue': expected_revenue,
                'preparation_score': preparation_status['score'],
                'preparation_issues': preparation_status['issues']
            }
        }
    
    # Analyser les événements génériques
    for event in ongoing_events:
        try:
            from ...models import EventParticipant
            participants = EventParticipant.objects.filter(event=event)
            
            event_details[f"event_{event.id}"] = {
                'event': event,
                'participants': participants,
                'stats': {
                    'total_participants': participants.count(),
                    'confirmed_participants': participants.filter(status='confirmed').count(),
                    'revenue': participants.aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
                }
            }
        except ImportError:
            # Modèle EventParticipant non disponible
            event_details[f"event_{event.id}"] = {
                'event': event,
                'participants': [],
                'stats': {
                    'total_participants': 0,
                    'confirmed_participants': 0,
                    'revenue': 0
                }
            }
    
    # === ALERTES ET NOTIFICATIONS ===
    alerts = generate_organizer_alerts(organization, event_details, today)
    
    # === ACTIVITÉ RÉCENTE ===
    recent_activity = get_recent_activity(organization, today)
    
    # === INDICATEURS CLÉS DE PERFORMANCE ===
    kpi_data = calculate_kpis(organization, event_details, today)
    
    context = {
        'club': club,
        'organization': organization,
        'ongoing_competitions': ongoing_competitions,
        'ongoing_events': ongoing_events,
        'recent_completed': recent_completed,
        'event_details': event_details,
        'stats': {
            'total_registrations': total_registrations,
            'confirmed_registrations': confirmed_registrations,
            'pending_registrations': pending_registrations,
        },
        'financial_stats': financial_stats,
        'alerts': alerts,
        'recent_activity': recent_activity,
        'kpi_data': kpi_data,
        'current_section': 'event_organizer',
        'page_title': _("Organisation d'Événements"),
    }
    
    return render(request, 'competitions/club/event_organizer_dashboard.html', context)


def get_financial_overview(organization, today):
    """Calculer les statistiques financières pour l'organisation"""
    try:
        from django.contrib.contenttypes.models import ContentType
        
        # Obtenir le ContentType de l'organisation
        ct = ContentType.objects.get_for_model(organization.__class__)
        
        # Revenus des inscriptions aux événements
        event_revenue = 0
        try:
            from ...models import EventParticipant
            event_revenue = EventParticipant.objects.filter(
                event__organization=organization,
                event__start_date__gte=today,
                payment_status='paid'
            ).aggregate(Sum('payment_amount'))['payment_amount__sum'] or 0
        except ImportError:
            pass
        
        # Factures émises
        invoices_issued = Invoice.objects.filter(
            issuer_content_type=ct,
            issuer_object_id=organization.id,
            created_at__gte=today - timedelta(days=30)
        ).count()
        
        total_invoiced = Invoice.objects.filter(
            issuer_content_type=ct,
            issuer_object_id=organization.id,
            status='issued'
        ).aggregate(Sum('total'))['total__sum'] or 0
        
        pending_payments = PaymentAttempt.objects.filter(
            transaction__category__name__icontains='competition',
            created_at__gte=today - timedelta(days=30),
            status='pending'
        ).count()
        
        return {
            'event_revenue': event_revenue,
            'invoices_issued': invoices_issued,
            'total_invoiced': total_invoiced,
            'pending_payments': pending_payments,
            'currency': 'EUR'  # TODO: Get from organization settings
        }
        
    except Exception as e:
        return {
            'event_revenue': 0,
            'invoices_issued': 0,
            'total_invoiced': 0,
            'pending_payments': 0,
            'currency': 'EUR'
        }


def calculate_expected_revenue(competition, registrations):
    """Calculer les revenus prévisionnels d'une compétition"""
    # TODO: Implémenter le calcul basé sur les frais d'inscription
    # Pour le moment, estimation simple
    base_fee = 25.0  # Frais d'inscription moyen
    return registrations.count() * base_fee


def assess_preparation_status(competition, categories, registrations):
    """Évaluer l'état de préparation d'une compétition"""
    issues = []
    score = 100
    
    # Vérifier les catégories
    if not categories.exists():
        issues.append(_("Aucune catégorie définie"))
        score -= 30
    
    # Vérifier les inscriptions
    if registrations.count() == 0:
        issues.append(_("Aucune inscription"))
        score -= 25
    elif registrations.filter(status='pending').count() > registrations.count() * 0.5:
        issues.append(_("Trop d'inscriptions en attente"))
        score -= 15
    
    # Vérifier la planification
    days_until = (competition.start_date - timezone.now().date()).days
    if days_until < 7 and not categories.exists():
        issues.append(_("Planification tardive"))
        score -= 20
    
    # Vérifier les juges
    # TODO: Ajouter vérification des juges assignés
    
    return {
        'score': max(0, score),
        'issues': issues
    }


def generate_organizer_alerts(organization, event_details, today):
    """Générer les alertes pour l'organisateur"""
    alerts = []
    
    for event_id, details in event_details.items():
        if 'competition' in details:
            comp = details['competition']
            stats = details['stats']
            
            # Alerte: Peu d'inscriptions
            if comp.start_date - today <= timedelta(days=14) and stats['total_participants'] < 10:
                alerts.append({
                    'type': 'warning',
                    'title': f"Peu d'inscriptions - {comp.name}",
                    'message': f"Seulement {stats['total_participants']} participant(s) inscrit(s)",
                    'action_url': f"/competitions/{comp.id}/manage/"
                })
            
            # Alerte: Inscriptions en attente
            if stats['pending_participants'] > 0:
                alerts.append({
                    'type': 'info', 
                    'title': f"Inscriptions à traiter - {comp.name}",
                    'message': f"{stats['pending_participants']} inscription(s) en attente de confirmation",
                    'action_url': f"/competitions/{comp.id}/registrations/"
                })
            
            # Alerte: Préparation incomplète
            if stats['preparation_score'] < 80:
                alerts.append({
                    'type': 'danger',
                    'title': f"Préparation incomplète - {comp.name}",
                    'message': f"Score de préparation: {stats['preparation_score']}%",
                    'action_url': f"/competitions/{comp.id}/setup/"
                })
    
    return alerts[:10]  # Limiter à 10 alertes


def get_recent_activity(organization, today):
    """Obtenir l'activité récente de l'organisation"""
    activities = []
    
    # Nouvelles inscriptions (derniers 7 jours)
    recent_registrations = CompetitionRegistration.objects.filter(
        competition__organizing_organization=organization,
        registration_date__gte=today - timedelta(days=7)
    ).select_related('competition', 'practitioner').order_by('-registration_date')[:10]
    
    for reg in recent_registrations:
        activities.append({
            'type': 'registration',
            'timestamp': reg.registration_date,
            'title': f"Nouvelle inscription - {reg.competition.title}",
            'description': f"{reg.practitioner.full_name}",
            'icon': 'fas fa-user-plus'
        })
    
    # Tri par date décroissante
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:15]


def calculate_kpis(organization, event_details, today):
    """Calculer les indicateurs clés de performance"""
    
    total_events = len(event_details)
    total_participants = sum(d['stats']['total_participants'] for d in event_details.values())
    
    # Taux de confirmation moyen
    if total_participants > 0:
        confirmed_participants = sum(d['stats']['confirmed_participants'] for d in event_details.values())
        confirmation_rate = (confirmed_participants / total_participants) * 100
    else:
        confirmation_rate = 0
    
    # Revenus prévisionnels totaux
    total_expected_revenue = sum(
        d['stats'].get('expected_revenue', 0) for d in event_details.values() 
        if 'competition' in d
    )
    
    return {
        'total_events': total_events,
        'total_participants': total_participants,
        'confirmation_rate': confirmation_rate,
        'expected_revenue': total_expected_revenue,
        'events_this_month': len([
            d for d in event_details.values() 
            if ('competition' in d and d['competition'].start_date.month == today.month) or
               ('event' in d and d['event'].start_date.month == today.month)
        ])
    }


@login_required
def competition_management_detail(request, competition_id):
    """
    Interface de gestion détaillée d'une compétition spécifique
    """
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier les permissions
    from ...utils.permission_helpers import get_user_club
    club = get_user_club(request)
    
    if not club or not (club.organization == competition.organizing_organization):
        messages.error(request, _("Vous n'avez pas les permissions pour gérer cette compétition."))
        return redirect('competitions:club:event_organizer')
    
    # Données détaillées pour la gestion
    categories = CompetitionCategory.objects.filter(
        competition=competition
    ).annotate(participant_count=Count('registrations'))
    
    registrations = CompetitionRegistration.objects.filter(
        competition=competition
    ).select_related('practitioner').order_by('registration_date')
    
    # Statistiques financières
    financial_overview = get_competition_financial_data(competition)
    
    # Planning et organisation
    schedule_data = get_competition_schedule_data(competition)
    
    context = {
        'competition': competition,
        'categories': categories,
        'registrations': registrations,
        'financial_overview': financial_overview,
        'schedule_data': schedule_data,
        'page_title': f"Gestion - {competition.title}",
    }
    
    return render(request, 'competitions/club/competition_management_detail.html', context)


def get_competition_financial_data(competition):
    """Obtenir les données financières d'une compétition"""
    # TODO: Implémenter le calcul financier détaillé
    return {
        'total_revenue': 0,
        'pending_payments': 0,
        'expenses': 0,
        'net_profit': 0
    }


def get_competition_schedule_data(competition):
    """Obtenir les données de planning d'une compétition"""
    # TODO: Implémenter la récupération du planning
    return {
        'tatamis': 0,
        'time_slots': [],
        'judge_assignments': []
    }