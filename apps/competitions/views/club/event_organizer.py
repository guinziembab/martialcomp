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
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta, time
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
    from django.urls import reverse
    alerts = []

    for event_id, details in event_details.items():
        if 'competition' in details:
            comp = details['competition']
            stats = details['stats']

            manage_url = reverse('competitions:club:competition_management_detail', kwargs={'competition_id': comp.id})

            # Alerte: Peu d'inscriptions
            if comp.start_date - today <= timedelta(days=14) and stats['total_participants'] < 10:
                alerts.append({
                    'type': 'warning',
                    'title': f"Peu d'inscriptions - {comp.title}",
                    'message': f"Seulement {stats['total_participants']} participant(s) inscrit(s)",
                    'action_url': manage_url
                })

            # Alerte: Inscriptions en attente
            if stats['pending_participants'] > 0:
                alerts.append({
                    'type': 'info',
                    'title': f"Inscriptions à traiter - {comp.title}",
                    'message': f"{stats['pending_participants']} inscription(s) en attente de confirmation",
                    'action_url': manage_url
                })

            # Alerte: Préparation incomplète
            if stats['preparation_score'] < 80:
                alerts.append({
                    'type': 'danger',
                    'title': f"Préparation incomplète - {comp.title}",
                    'message': f"Score de préparation: {stats['preparation_score']}%",
                    'action_url': manage_url
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
    
    # Récupérer les clubs pour les filtres
    clubs = set()
    for reg in registrations:
        if reg.practitioner.club:
            clubs.add(reg.practitioner.club)
    
    # Statistiques financières
    financial_overview = get_competition_financial_data(competition)
    
    # Planning et organisation
    schedule_data = get_competition_schedule_data(competition)
    
    # Générer l'URL publique de la compétition
    from django.urls import reverse
    try:
        # Essayer d'abord l'URL dans le namespace competitions:competitions
        competition_public_url = request.build_absolute_uri(
            reverse('competitions:competitions:detail', kwargs={'pk': competition.id})
        )
    except Exception:
        # Fallback: construire l'URL manuellement
        competition_public_url = request.build_absolute_uri(
            f'/{request.LANGUAGE_CODE}/competitions/{competition.id}/'
        )

    # Lien d'inscription directe pour les responsables de clubs
    try:
        competition_registration_url = request.build_absolute_uri(
            reverse('competitions:club:competition_registration_form', kwargs={'competition_id': competition.id})
        )
    except Exception:
        competition_registration_url = request.build_absolute_uri(
            f'/{request.LANGUAGE_CODE}/competitions/club/competition-registration/{competition.id}/'
        )

    # Récupérer les juges pour cette compétition
    technical_judges = []
    combat_referees = []

    try:
        from ...models import TechnicalJudge

        assigned_technical_judges = TechnicalJudge.objects.filter(
            competition=competition
        ).select_related('judge', 'judge__practitioner', 'judge__practitioner__organization')

        for tech_judge in assigned_technical_judges:
            judge = tech_judge.judge
            if judge and judge.active:
                judge_data = {
                    'id': judge.id,
                    'practitioner': judge.practitioner,
                    'name': judge.practitioner.full_name if judge.practitioner else str(judge),
                    'qualification_level_display': judge.get_qualification_level_display() if hasattr(judge, 'get_qualification_level_display') else '',
                    'years_experience': getattr(judge, 'years_experience', 0),
                    'is_adhoc': False,
                    'is_technical_judge': getattr(judge, 'is_technical_judge', True),
                    'is_combat_referee': getattr(judge, 'is_combat_referee', False),
                }
                if getattr(judge, 'is_technical_judge', True):
                    technical_judges.append(judge_data.copy())
                if getattr(judge, 'is_combat_referee', False):
                    combat_referees.append(judge_data.copy())
    except (ImportError, Exception):
        pass

    try:
        from ...models import AdHocJudge
        if AdHocJudge is not None:
            adhoc_tech_judges = AdHocJudge.objects.filter(
                competition=competition,
                judge_type='technical_judge',
                status='active'
            ).select_related('practitioner', 'practitioner__organization')

            for adhoc in adhoc_tech_judges:
                technical_judges.append({
                    'id': f'adhoc_{adhoc.id}',
                    'practitioner': adhoc.practitioner,
                    'name': adhoc.practitioner.full_name if adhoc.practitioner else adhoc.name,
                    'qualification_level_display': adhoc.get_experience_level_display() if hasattr(adhoc, 'get_experience_level_display') else '',
                    'years_experience': 0,
                    'is_adhoc': True,
                })

            adhoc_referees = AdHocJudge.objects.filter(
                competition=competition,
                judge_type__in=['combat_referee', 'assistant_referee'],
                status='active'
            ).select_related('practitioner', 'practitioner__organization')

            for adhoc in adhoc_referees:
                combat_referees.append({
                    'id': f'adhoc_{adhoc.id}',
                    'practitioner': adhoc.practitioner,
                    'name': adhoc.practitioner.full_name if adhoc.practitioner else adhoc.name,
                    'qualification_level_display': adhoc.get_experience_level_display() if hasattr(adhoc, 'get_experience_level_display') else '',
                    'is_adhoc': True,
                })
    except (ImportError, Exception):
        pass

    context = {
        'competition': competition,
        'categories': categories,
        'registrations': registrations,
        'clubs': list(clubs),
        'financial_overview': financial_overview,
        'schedule_data': schedule_data,
        'page_title': f"Gestion - {competition.title}",
        'competition_public_url': competition_public_url,
        'competition_registration_url': competition_registration_url,
        'technical_judges': technical_judges,
        'combat_referees': combat_referees,
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


@login_required
@require_POST
def save_competition_schedule(request, competition_id):
    """
    API pour sauvegarder le planning des catégories par aire/tatami.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # Vérifier les permissions
    from ...utils.permission_helpers import get_user_club
    club = get_user_club(request)

    if not club or not (club.organization == competition.organizing_organization):
        return JsonResponse({
            'success': False,
            "message": "Vous n'avez pas les permissions pour modifier cette compétition."
        }, status=403)

    try:
        data = json.loads(request.body)
        config = data.get('config', {})
        areas = data.get('areas', {})

        # Parser l'heure de début
        start_time_str = config.get('startTime', '08:00')
        try:
            start_hour, start_minute = map(int, start_time_str.split(':'))
        except (ValueError, AttributeError):
            start_hour, start_minute = 8, 0

        duration_per_slot = config.get('durationPerSlot', 5)
        pause_between = config.get('pauseBetweenCategories', 5)

        # Réinitialiser toutes les catégories de cette compétition
        CompetitionCategory.objects.filter(competition=competition).update(
            assigned_tatami=None,
            schedule_order=None,
            estimated_start_time=None
        )

        categories_updated = 0

        # Traiter chaque aire
        for area_key, category_ids in areas.items():
            try:
                tatami_num = int(area_key.replace('area', ''))
            except ValueError:
                continue

            current_minutes = start_hour * 60 + start_minute

            for order, category_id in enumerate(category_ids, start=1):
                try:
                    category = CompetitionCategory.objects.get(
                        id=category_id,
                        competition=competition
                    )

                    registrations_count = category.registrations.count()
                    duration = max(registrations_count * duration_per_slot, 5)

                    est_hour = current_minutes // 60
                    est_minute = current_minutes % 60
                    estimated_start = time(est_hour, est_minute) if est_hour < 24 else None

                    category.assigned_tatami = tatami_num
                    category.schedule_order = order
                    category.estimated_start_time = estimated_start
                    category.estimated_duration = duration
                    category.save(update_fields=[
                        'assigned_tatami', 'schedule_order',
                        'estimated_start_time', 'estimated_duration'
                    ])

                    categories_updated += 1
                    current_minutes += duration + pause_between

                except CompetitionCategory.DoesNotExist:
                    continue

        return JsonResponse({
            'success': True,
            'message': 'Planning sauvegardé avec succès.',
            'categories_updated': categories_updated
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Données JSON invalides.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_POST
def toggle_category_completed(request, competition_id, category_id):
    """
    API pour marquer/démarquer une catégorie comme terminée.
    """
    competition = get_object_or_404(Competition, id=competition_id)

    # Vérifier les permissions
    from ...utils.permission_helpers import get_user_club
    club = get_user_club(request)

    if not club or not (club.organization == competition.organizing_organization):
        return JsonResponse({
            'success': False,
            'message': "Vous n'avez pas les permissions pour modifier cette compétition."
        }, status=403)

    try:
        category = CompetitionCategory.objects.get(
            id=category_id,
            competition=competition
        )

        # Toggle l'état
        category.is_completed = not category.is_completed
        category.save(update_fields=['is_completed'])

        return JsonResponse({
            'success': True,
            'is_completed': category.is_completed,
            'message': 'Catégorie marquée comme terminée.' if category.is_completed else 'Catégorie marquée comme en cours.'
        })

    except CompetitionCategory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Catégorie non trouvée.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
