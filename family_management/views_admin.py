"""
Vues administratives pour la gestion familiale centralisée.
Inclut les inscriptions groupées, paiements familiaux, etc.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.db import models
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from datetime import datetime, timedelta
import json

from .models import Family, FamilyMember, FamilyEvent, FamilyPaymentGroup
from .services import FamilyRegistrationService, FamilyPaymentService, FamilyEventService
from .permissions import family_management_required, family_access_required
from competitions.models import Practitioner, Competition, CompetitionRegistration


@login_required
@family_management_required
def family_group_registration(request, family_id):
    """
    Vue pour les inscriptions groupées d'une famille à des compétitions.
    """
    family = request.family  # Ajouté par le décorateur
    
    # Récupérer les compétitions disponibles
    available_competitions = Competition.objects.filter(
        is_open_for_registration=True,
        registration_end_date__gte=timezone.now().date()
    ).order_by('start_date')
    
    # Récupérer les membres pratiquants de la famille
    family_practitioners = family.get_practitioners()
    
    # Statistiques des inscriptions
    recent_registrations = CompetitionRegistration.objects.filter(
        practitioner__in=family_practitioners,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).select_related('competition', 'practitioner')
    
    context = {
        'family': family,
        'available_competitions': available_competitions,
        'family_practitioners': family_practitioners,
        'recent_registrations': recent_registrations,
        'total_practitioners': len(family_practitioners),
    }
    
    return render(request, 'family_management/group_registration.html', context)


@login_required
@family_management_required
@require_POST
def process_group_registration(request, family_id):
    """
    Traite une inscription groupée à une compétition.
    """
    family = request.family
    
    try:
        # Récupérer les données du formulaire
        competition_id = request.POST.get('competition_id')
        selected_members = request.POST.getlist('selected_members')
        notes = request.POST.get('notes', '')
        
        if not competition_id:
            return JsonResponse({'error': 'Competition ID required'}, status=400)
        
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Utiliser le service d'inscription
        results = FamilyRegistrationService.register_family_to_competition(
            family=family,
            competition=competition,
            selected_members=selected_members,
            registered_by=request.user,
            notes=notes
        )
        
        if results['success']:
            messages.success(
                request, 
                _("Inscription groupée réussie: %(count)d membres inscrits") % {
                    'count': results['registered_count']
                }
            )
            
            # Ajouter les détails sur les coûts
            if results['total_cost'] > 0:
                messages.info(
                    request,
                    _("Coût total: %(cost)s€") % {'cost': results['total_cost']}
                )
        else:
            messages.error(request, _("Aucune inscription n'a pu être effectuée"))
        
        # Afficher les erreurs individuelles
        for error in results['errors']:
            messages.warning(request, error)
        
        return JsonResponse({
            'success': results['success'],
            'registered_count': results.get('registered_count', 0),
            'total_cost': str(results['total_cost']),
            'errors': results['errors']
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@family_access_required
@require_GET
def check_competition_eligibility(request, family_id):
    """
    API pour vérifier l'éligibilité des membres de la famille pour une compétition.
    """
    family = request.family
    competition_id = request.GET.get('competition_id')
    
    if not competition_id:
        return JsonResponse({'error': 'Competition ID required'}, status=400)
    
    try:
        competition = get_object_or_404(Competition, id=competition_id)
        
        eligibility = FamilyRegistrationService.get_family_competition_eligibility(
            family, competition
        )
        
        # Formater les données pour le frontend
        data = {
            'competition': {
                'id': competition.id,
                'name': competition.name,
                'registration_fee': str(getattr(competition, 'registration_fee', 0))
            },
            'eligible': [
                {
                    'id': p.id,
                    'name': p.full_name,
                    'age': p.age,
                    'grade': p.grade_display
                }
                for p in eligibility['eligible']
            ],
            'ineligible': [
                {
                    'id': p.id,
                    'name': p.full_name,
                    'reason': 'Non éligible'  # TODO: Ajouter les raisons détaillées
                }
                for p in eligibility['ineligible']
            ],
            'already_registered': [
                {
                    'id': p.id,
                    'name': p.full_name
                }
                for p in eligibility['already_registered']
            ]
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@family_access_required
def family_payment_center(request, family_id):
    """
    Centre de gestion des paiements familiaux.
    """
    family = request.family
    
    # Récupérer les groupes de paiements
    payment_groups = family.payment_groups.all().order_by('-created_at')
    
    # Filtres
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'pending':
        payment_groups = payment_groups.filter(is_paid=False)
    elif status_filter == 'paid':
        payment_groups = payment_groups.filter(is_paid=True)
    
    # Pagination
    paginator = Paginator(payment_groups, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Résumé financier
    financial_summary = FamilyPaymentService.get_family_financial_summary(family)
    
    context = {
        'family': family,
        'page_obj': page_obj,
        'financial_summary': financial_summary,
        'status_filter': status_filter,
        'can_manage_payments': request.user == family.primary_responsible or 
                              family.members.filter(
                                  user=request.user, 
                                  can_make_payments=True
                              ).exists(),
    }
    
    return render(request, 'family_management/payment_center.html', context)


@login_required
@family_management_required
@require_POST
def create_payment_group(request, family_id):
    """
    Crée un nouveau groupe de paiement familial.
    """
    family = request.family
    
    try:
        data = json.loads(request.body)
        description = data.get('description')
        items = data.get('items', [])
        
        if not description:
            return JsonResponse({'error': 'Description required'}, status=400)
        
        payment_group = FamilyPaymentService.create_family_payment_group(
            family=family,
            description=description,
            items=items,
            created_by=request.user
        )
        
        return JsonResponse({
            'success': True,
            'payment_group_id': payment_group.id,
            'total_amount': str(payment_group.total_amount)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@family_management_required
@require_POST
def process_payment(request, family_id, payment_group_id):
    """
    Traite un paiement pour un groupe familial.
    """
    family = request.family
    payment_group = get_object_or_404(FamilyPaymentGroup, id=payment_group_id, family=family)
    
    if payment_group.is_paid:
        return JsonResponse({'error': 'Payment already processed'}, status=400)
    
    try:
        data = json.loads(request.body)
        payment_method = data.get('payment_method', 'stripe')
        payment_data = data.get('payment_data', {})
        
        result = FamilyPaymentService.process_family_payment(
            payment_group=payment_group,
            payment_method=payment_method,
            payment_data=payment_data
        )
        
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@family_management_required
def family_event_management(request, family_id):
    """
    Gestion des événements familiaux.
    """
    family = request.family
    
    # Récupérer les événements
    upcoming_events = FamilyEvent.objects.filter(
        family=family,
        start_date__gte=timezone.now()
    ).order_by('start_date')
    
    past_events = FamilyEvent.objects.filter(
        family=family,
        start_date__lt=timezone.now()
    ).order_by('-start_date')[:10]
    
    # Membres de la famille pour sélection
    family_members = family.members.filter(is_active=True)
    
    context = {
        'family': family,
        'upcoming_events': upcoming_events,
        'past_events': past_events,
        'family_members': family_members,
    }
    
    return render(request, 'family_management/event_management.html', context)


@login_required
@family_management_required
@require_POST
def create_family_event(request, family_id):
    """
    Crée un nouvel événement familial.
    """
    family = request.family
    
    try:
        data = json.loads(request.body)
        
        title = data.get('title')
        start_date = datetime.fromisoformat(data.get('start_date'))
        end_date = data.get('end_date')
        if end_date:
            end_date = datetime.fromisoformat(end_date)
        
        description = data.get('description', '')
        location = data.get('location', '')
        concerned_members = data.get('concerned_members', [])
        
        if not title:
            return JsonResponse({'error': 'Title required'}, status=400)
        
        event = FamilyEventService.create_family_event(
            family=family,
            title=title,
            start_date=start_date,
            end_date=end_date,
            description=description,
            location=location,
            created_by=request.user,
            concerned_members=concerned_members
        )
        
        # Envoyer des notifications
        FamilyEventService.notify_family_members(
            family=family,
            event=event,
            notification_type='event_created'
        )
        
        return JsonResponse({
            'success': True,
            'event_id': event.id,
            'message': _("Événement créé avec succès")
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@family_access_required
def family_statistics(request, family_id):
    """
    Vue des statistiques familiales.
    """
    family = request.family
    
    # Statistiques générales
    members = family.get_all_members()
    practitioners = family.get_practitioners()
    
    # Statistiques des compétitions
    competition_stats = CompetitionRegistration.objects.filter(
        practitioner__in=practitioners
    ).aggregate(
        total_competitions=Count('id'),
        this_year=Count('id', filter=Q(created_at__year=timezone.now().year))
    )
    
    # Statistiques financières
    financial_stats = FamilyPaymentService.get_family_financial_summary(family)
    
    # Événements récents
    recent_events = FamilyEvent.objects.filter(
        family=family,
        start_date__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    stats = {
        'total_members': members.count(),
        'total_practitioners': len(practitioners),
        'total_children': members.filter(role='child').count(),
        'total_parents': members.filter(role__in=['parent', 'guardian']).count(),
        'competitions_stats': competition_stats,
        'financial_stats': financial_stats,
        'recent_events': recent_events,
    }
    
    context = {
        'family': family,
        'stats': stats,
    }
    
    return render(request, 'family_management/family_statistics.html', context)


@login_required
@family_management_required
def export_family_data(request, family_id):
    """
    Exporte les données familiales (CSV, PDF, etc.).
    """
    family = request.family
    export_format = request.GET.get('format', 'csv')
    
    # TODO: Implémenter l'export selon le format demandé
    
    if export_format == 'csv':
        # Générer un CSV avec les données familiales
        pass
    elif export_format == 'pdf':
        # Générer un PDF avec rapport familial
        pass
    
    return JsonResponse({'error': 'Export functionality not implemented yet'}, status=501)