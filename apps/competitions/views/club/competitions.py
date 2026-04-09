# competitions/views/club/competitions.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied

from ...models import Club, Competition, CompetitionRegistration
from ...utils.decorators import club_required
from apps.competitions.utils.permission_helpers import manual_permission_check
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
from apps.competitions.utils.organization_discipline_filtering import (
    filter_competitions_by_org_disciplines,
    filter_practitioners_by_org_disciplines,
    filter_judges_by_org_disciplines,
    get_organization_disciplines
)


@login_required
@manual_permission_check('club.manage_competitions')
def club_competitions(request):
    """
    Affiche les compétitions auxquelles le club est inscrit ou qu'il organise.
    Cette vue centralise toutes les compétitions liées au club.
    """
    club = getattr(request, 'club', None)
    if not club:
        club = Club.objects.filter(owner=request.user).first()
        
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Obtenir la date actuelle
    now = timezone.now().date()
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        upcoming_competitions = Competition.objects.none()
        past_competitions = Competition.objects.none()
    else:
        # Compétitions futures (à venir) - Filtrer par disciplines de l'organisation
        base_competitions = filter_competitions_by_org_disciplines(club_organization)
        # Ajouter aussi les compétitions où des pratiquants de l'organisation sont inscrits
        practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
        practitioner_competitions = Competition.objects.filter(
            registrations__practitioner__in=practitioners_qs
        ).distinct()
        
        upcoming_competitions = (base_competitions | practitioner_competitions).filter(
            end_date__gte=now
        ).distinct().order_by('start_date')
        
        # Compétitions passées
        past_competitions = (base_competitions | practitioner_competitions).filter(
            end_date__lt=now
        ).distinct().order_by('-start_date')
    
    # Nombre de participants par compétition
    competition_stats = {}
    for comp in list(upcoming_competitions) + list(past_competitions):
        if not club_organization:
            participants_count = 0
        else:
            # Filtrer les participants par disciplines de l'organisation
            practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
            participants_count = CompetitionRegistration.objects.filter(
                competition=comp,
                practitioner__in=practitioners_qs,
                is_competitor=True
            ).count()
        
        competition_stats[comp.id] = {
            'participants_count': participants_count
        }
    
    context = {
        'club': club,
        'upcoming_competitions': upcoming_competitions,
        'past_competitions': past_competitions,
        'competition_stats': competition_stats,
        'current_section': 'competitions',  # Pour marquer l'élément actif dans le menu
    }
    
    return render(request, 'competitions/club/competitions.html', context)


@login_required
@manual_permission_check('club.manage_competitions')
def club_competition_detail(request, competition_id):
    """
    Affiche les détails d'une compétition spécifique pour le club,
    y compris les pratiquants inscrits et leurs catégories.
    """
    # Obtenir le club de l'utilisateur
    club = getattr(request, 'club', None)
    if not club:
        club = Club.objects.filter(owner=request.user).first()
        
    if not club:
        messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        registrations = CompetitionRegistration.objects.none()
    else:
        # Récupérer les inscriptions des membres du club (filtrées par disciplines)
        practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
        registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner__in=practitioners_qs
        ).select_related('practitioner')
    
    context = {
        'club': club,
        'competition': competition,
        'registrations': registrations,
        'current_section': 'competitions',
    }
    
    return render(request, 'competitions/club/competition_detail.html', context)


@login_required
def competition_management_dashboard(request):
    """
    Interface avancée de gestion des compétitions avec :
    - Inscription des pratiquants
    - Affectation des juges
    - Vue des catégories
    - Drag & drop pour déplacer pratiquants entre catégories
    """
    club = getattr(request, 'club', None)
    if not club:
        club = Club.objects.filter(owner=request.user).first()
        
    if not club:
        # Si aucun club trouvé, essayer de créer ou rediriger vers une page appropriée
        try:
            messages.error(request, _("Vous devez être responsable de club pour accéder à cette page."))
        except:
            pass  # Ignorer si les messages ne fonctionnent pas
        return redirect('competitions:dashboard:club')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        try:
            messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        except:
            pass  # Ignorer si les messages ne fonctionnent pas
        return redirect('competitions:club:competitions')
    
    # Obtenir la date actuelle
    now = timezone.now().date()
    
    # Récupérer les compétitions disponibles pour inscription
    available_competitions = Competition.objects.filter(
        registration_start_date__lte=now,
        registration_end_date__gte=now,
        status='open'
    ).order_by('start_date')
    
    # Récupérer les pratiquants du club (filtrés par disciplines)
    from ...models import Practitioner
    practitioners = filter_practitioners_by_org_disciplines(club_organization).filter(
        is_active=True
    ).select_related('user')
    
    # Récupérer les juges disponibles (filtrés par disciplines)
    judges = []
    try:
        from ...models import Judge
        judges = filter_judges_by_org_disciplines(club_organization).filter(
            is_active=True
        ).select_related('practitioner')
    except ImportError:
        # Le modèle Judge n'existe pas
        judges = []
    
    # Récupérer les inscriptions existantes pour chaque compétition
    competition_data = {}
    for competition in available_competitions:
        # Catégories de la compétition
        categories = competition.categories.all().prefetch_related('registrations__practitioner')
        
        # Inscriptions existantes des pratiquants du club (filtrées par disciplines)
        practitioners_qs = filter_practitioners_by_org_disciplines(club_organization)
        registrations = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner__in=practitioners_qs
        ).select_related('practitioner', 'category')
        
        # Organiser les inscriptions par catégorie
        registrations_by_category = {}
        for registration in registrations:
            category_id = registration.category.id if registration.category else 'no_category'
            if category_id not in registrations_by_category:
                registrations_by_category[category_id] = []
            registrations_by_category[category_id].append(registration)
        
        # Pratiquants non inscrits
        registered_practitioner_ids = set(registrations.values_list('practitioner_id', flat=True))
        unregistered_practitioners = practitioners.exclude(id__in=registered_practitioner_ids)
        
        competition_data[competition.id] = {
            'competition': competition,
            'categories': categories,
            'registrations_by_category': registrations_by_category,
            'unregistered_practitioners': unregistered_practitioners,
            'total_registered': registrations.count()
        }
    
    context = {
        'club': club,
        'club_organization': club_organization,
        'available_competitions': available_competitions,
        'practitioners': practitioners,
        'judges': judges,
        'competition_data': competition_data,
        'current_section': 'competitions',
    }
    
    return render(request, 'competitions/club/competition_management.html', context)


@login_required
@manual_permission_check('club.manage_competitions')
def api_move_practitioner_category(request):
    """
    API pour déplacer un pratiquant entre catégories via drag & drop
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    try:
        practitioner_id = request.POST.get('practitioner_id')
        competition_id = request.POST.get('competition_id')
        category_id = request.POST.get('category_id')
        registration_id = request.POST.get('registration_id')  # Si déjà inscrit
        
        if not all([practitioner_id, competition_id]):
            return JsonResponse({'success': False, 'message': 'Paramètres manquants'})
        
        # Récupérer les objets
        from ...models import Practitioner, Competition, CompetitionCategory
        
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)
        competition = get_object_or_404(Competition, id=competition_id)
        
        # Vérifier les permissions
        club = getattr(request, 'club', None) or Club.objects.filter(owner=request.user).first()
        if not club or not (club.organization == practitioner.organization):
            return JsonResponse({'success': False, 'message': 'Permissions insuffisantes'})
        
        # Si category_id est 'unregistered', désinscrire
        if category_id == 'unregistered':
            if registration_id:
                existing_registration = CompetitionRegistration.objects.filter(
                    id=registration_id,
                    practitioner=practitioner,
                    competition=competition
                ).first()
                if existing_registration:
                    existing_registration.delete()
                    return JsonResponse({'success': True, 'message': 'Practitioner désinscrit'})
            return JsonResponse({'success': False, 'message': 'Aucune inscription trouvée'})
        
        # Sinon, inscrire dans la catégorie
        category = get_object_or_404(CompetitionCategory, id=category_id, competition=competition)
        
        # Supprimer l'ancienne inscription si elle existe
        if registration_id:
            CompetitionRegistration.objects.filter(
                id=registration_id,
                practitioner=practitioner,
                competition=competition
            ).delete()
        
        # Créer la nouvelle inscription
        registration, created = CompetitionRegistration.objects.get_or_create(
            practitioner=practitioner,
            competition=competition,
            defaults={
                'category': category,
                'is_competitor': True,
                'registration_date': timezone.now()
            }
        )
        
        if not created:
            registration.category = category
            registration.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Practitioner inscrit avec succès',
            'registration_id': registration.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


from django.http import JsonResponse

@login_required  
@manual_permission_check('club.manage_competitions')
def api_remove_registration(request):
    """
    API pour supprimer une inscription
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    try:
        registration_id = request.POST.get('registration_id')
        
        if not registration_id:
            return JsonResponse({'success': False, 'message': 'ID inscription manquant'})
        
        # Vérifier les permissions
        club = getattr(request, 'club', None) or Club.objects.filter(owner=request.user).first()
        
        registration = get_object_or_404(CompetitionRegistration, id=registration_id)
        
        if not club or not (club.organization == registration.practitioner.organization):
            return JsonResponse({'success': False, 'message': 'Permissions insuffisantes'})
        
        registration.delete()
        
        return JsonResponse({'success': True, 'message': 'Inscription supprimée'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})