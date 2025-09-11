"""
Module pour la gestion des inscriptions aux compétitions.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

# Importation de notre helper de permission personnalisé
from apps.competitions.utils.permission_helpers import manual_permission_check, get_user_club

from apps.competitions.utils.decorators import club_required, federation_or_club_required
from apps.competitions.models import (
    Practitioner, 
    CompetitionRegistration, 
    Competition, 
    Club, 
    Federation,
    Discipline
)
from apps.competitions.forms import CompetitionRegistrationForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset
# La fonction get_user_club est déjÃ  importée de notre helper

import logging
logger = logging.getLogger(__name__)

@login_required
def registrations_list(request):
    """Liste des inscriptions aux compétitions pour le club."""
    # Récupérer le club de l'utilisateur
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        practitioners = Practitioner.objects.none()
    else:
        # Récupérer tous les pratiquants du club
        practitioners = Practitioner.objects.filter(organization=club_organization)
    
    # Récupérer toutes les inscriptions des pratiquants du club
    registrations = CompetitionRegistration.objects.filter(
        practitioner__in=practitioners
    ).select_related('competition', 'practitioner')
    
    # Filtre par statut
    status_filter = request.GET.get('status')
    if status_filter:
        registrations = registrations.filter(status=status_filter)
    
    # Filtre par compétition
    competition_filter = request.GET.get('competition_id')
    if competition_filter:
        registrations = registrations.filter(competition_id=competition_filter)
    
    # Filtre par pratiquant
    practitioner_filter = request.GET.get('practitioner_id')
    if practitioner_filter:
        registrations = registrations.filter(practitioner_id=practitioner_filter)
    
    # Récupérer la liste des compétitions pour le filtre
    competitions = Competition.objects.filter(
        id__in=registrations.values_list('competition_id', flat=True).distinct()
    )
    
    return render(request, 'competitions/club/registrations.html', {
        'registrations': registrations,
        'club': club,
        'competitions': competitions,
        'practitioners': practitioners,
        'status_choices': [
            ('pending', _('En attente')),
            ('approved', _('Approuvée')),
            ('rejected', _('Rejetée')),
        ],
        'current_status': status_filter,
        'current_competition': competition_filter,
        'current_practitioner': practitioner_filter,
    })

@login_required
def select_practitioner_for_registration(request, competition_id):
    """Sélectionne un pratiquant pour l'inscrire Ã  une compétition."""
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        practitioners = Practitioner.objects.none()
    else:
        # Récupérer uniquement les pratiquants du club
        practitioners = Practitioner.objects.filter(organization=club_organization).order_by('last_name', 'first_name')
    
    # Identifier les pratiquants déjÃ  inscrits
    registered_ids = CompetitionRegistration.objects.filter(
        competition=competition,
        practitioner__organization=club_organization if club_organization else None
    ).values_list('practitioner_id', flat=True)
    
    return render(request, 'competitions/club/select_practitioner.html', {
        'competition': competition,
        'practitioners': practitioners,
        'registered_ids': registered_ids,
        'club': club,
        'is_federation_admin': False
    })

@login_required
def register_practitioner(request, competition_id, practitioner_id=None):
    """Inscription d'un pratiquant Ã  une compétition."""
    # Vérifier manuellement si l'utilisateur a les permissions nécessaires
    club = get_user_club(request)
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    # Déterminer si l'utilisateur est responsable de club ou de fédération
    is_federation_admin = hasattr(request, 'federation') and request.federation
    is_club_manager = hasattr(request, 'club') and request.club
    
    club = None
    if is_club_manager:
        club = request.club
    elif is_federation_admin:
        # Si c'est un admin de fédération sans club spécifié
        if 'club_id' in request.GET:
            # Permettre Ã  l'admin de fédération de sélectionner un club
            try:
                club = get_object_or_404(Club, pk=request.GET['club_id'], federation=request.federation)
            except (ValueError, Club.DoesNotExist):
                messages.error(request, _("Club non trouvé ou non affilié Ã  votre fédération."))
                return redirect('competitions:federations:select_club', competition_id=competition_id)
        else:
            # Rediriger vers une page de sélection de club si aucun n'est spécifié
            return redirect('competitions:federations:select_club', competition_id=competition_id)
    
    if not club:
        messages.error(request, _("Veuillez sélectionner un club valide."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer la compétition
    try:
        competition = get_object_or_404(Competition, pk=competition_id)
    except (ValueError, Competition.DoesNotExist):
        messages.error(request, _("Compétition non trouvée."))
        if is_club_manager:
            return redirect('competitions:club:available_competitions')
        else:
            return redirect('competitions:federations:competitions')
    
    # Vérifier si la compétition accepte toujours les inscriptions
    now = timezone.now().date()
    if competition.registration_deadline and competition.registration_deadline < now:
        messages.error(request, _("La date limite d'inscription Ã  cette compétition est dépassée."))
        if is_club_manager:
            return redirect('competitions:club:available_competitions')
        else:
            return redirect('competitions:federations:competitions')
    
    if hasattr(competition, 'status') and competition.status not in ['published', 'open']:
        messages.error(request, _("Cette compétition n'accepte pas les inscriptions actuellement."))
        if is_club_manager:
            return redirect('competitions:club:available_competitions')
        else:
            return redirect('competitions:federations:competitions')
    
    # Si aucun pratiquant n'est spécifié, afficher la liste pour sélection
    if practitioner_id is None:
        # Vérifier si le club a une organisation associée
        club_organization = club.organization or getattr(club, 'as_organization', None)
        
        if not club_organization:
            messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
            practitioners = Practitioner.objects.none()
        else:
            practitioners = Practitioner.objects.filter(organization=club_organization).order_by('last_name', 'first_name')
        
        # Identifier les pratiquants déjÃ  inscrits
        registered_ids = CompetitionRegistration.objects.filter(
            competition=competition,
            practitioner__organization=club_organization if club_organization else None
        ).values_list('practitioner_id', flat=True)
        
        template = 'competitions/federation/select_practitioner.html' if is_federation_admin else 'competitions/club/select_practitioner.html'
        
        return render(request, template, {
            'competition': competition,
            'practitioners': practitioners,
            'registered_ids': registered_ids,
            'club': club,
            'is_federation_admin': is_federation_admin
        })
    
    # Récupérer le pratiquant
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    try:
        practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=club_organization)
    except (ValueError, Practitioner.DoesNotExist):
        messages.error(request, _("Pratiquant non trouvé dans le club sélectionné."))
        if is_club_manager:
            return redirect('competitions:club:available_competitions')
        else:
            return redirect('competitions:federations:select_club', competition_id=competition_id)
    
    # Vérifier l'éligibilité du pratiquant pour cette compétition
    eligibility_message = None
    
    # Utiliser la méthode check_eligibility si elle existe
    if hasattr(competition, 'check_eligibility'):
        try:
            is_eligible, reasons = competition.check_eligibility(practitioner)
            if not is_eligible and reasons:
                eligibility_message = ", ".join(reasons)
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification d'éligibilité: {str(e)}")
    # Sinon, vérifier manuellement mais prudemment avec getattr
    elif hasattr(practitioner, 'is_eligible_for_competition'):
        try:
            # Utiliser la méthode du pratiquant de façon sécurisée
            is_eligible = practitioner.is_eligible_for_competition(competition)
            if not is_eligible:
                eligibility_message = _("Ce pratiquant ne remplit pas les critères d'éligibilité pour cette compétition.")
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification d'éligibilité: {str(e)}")
    
    if eligibility_message:
        messages.warning(request, eligibility_message)
    
    # Vérifier si le pratiquant est déjÃ  inscrit
    existing_registration = CompetitionRegistration.objects.filter(
        practitioner=practitioner,
        competition=competition
    ).first()
    
    if request.method == 'POST':
        # Utiliser le formulaire d'inscription
        form = CompetitionRegistrationForm(
            request.POST, 
            instance=existing_registration,
            competition=competition
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    registration = form.save(commit=False)
                    registration.practitioner = practitioner
                    registration.competition = competition
                    
                    # Si c'est une nouvelle inscription, définir la date d'inscription
                    if not existing_registration:
                        registration.registration_date = timezone.now()
                        registration.status = 'pending'  # Statut par défaut
                    
                    registration.save()
                    
                    # Sauvegarder les relations ManyToMany
                    form.save_m2m()
                    
                    messages.success(request, _("Inscription de {} enregistrée avec succès.").format(practitioner.full_name))
                    # Rediriger vers la liste des inscriptions appropriée
                    if is_club_manager:
                        return redirect('competitions:club:registrations_list')
                    else:
                        return redirect('competitions:federations:registrations', club_id=club.id)
            except Exception as e:
                logger.error(f"Erreur d'inscription: {str(e)}", exc_info=True)
                messages.error(request, _("Une erreur est survenue lors de l'enregistrement de l'inscription: {}").format(str(e)))
        else:
            # Afficher les erreurs spécifiques du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Créer un nouveau formulaire
        form = CompetitionRegistrationForm(
            instance=existing_registration,
            competition=competition,
            initial={
                'practitioner': practitioner,
                'competition': competition
            }
        )
    
    # Contextualiser pour le template
    context = {
        'form': form,
        'competition': competition,
        'practitioner': practitioner,
        'is_edit': existing_registration is not None,
        'existing_registration': existing_registration,
        'club': club,
        'is_federation_admin': is_federation_admin
    }
    
    template = 'competitions/federation/registration_form.html' if is_federation_admin else 'competitions/club/registration_form.html'
    
    return render(request, template, context)

@login_required
def available_competitions(request):
    """
    Affiche les compétitions disponibles pour inscription.
    Cette vue est accessible Ã  la fois pour les responsables de club et les administrateurs de fédération.
    Filtre les compétitions selon les disciplines du club.
    """
    # Déterminer si l'utilisateur est administrateur de fédération ou responsable de club
    user_role = getattr(request.user, 'role', None)
    
    club = None
    federation = None
    
    if user_role == 'club_manager':
        club = get_user_club(request)
        if not club:
            messages.error(request, _("Vous devez Ãªtre associé Ã  un club pour accéder Ã  cette page."))
            return redirect('competitions:dashboard:index')
    elif user_role == 'federation_admin':
        # Pour les admins de fédération, ajouter un champ pour sélectionner un club
        federation = Federation.objects.filter(owner=request.user).first()
        if not federation:
            messages.error(request, _("Fédération non trouvée."))
            return redirect('competitions:dashboard:index')
        
        # Si un club est spécifié dans l'URL
        club_id = request.GET.get('club_id')
        if club_id:
            try:
                club = Club.objects.get(id=club_id, federation=federation)
            except Club.DoesNotExist:
                messages.error(request, _("Club non trouvé ou non affilié Ã  votre fédération."))
                return redirect('competitions:dashboard:index')
    else:
        messages.error(request, _("Vous n'avez pas les droits nécessaires pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    # Si utilisateur est admin de fédération et aucun club n'est sélectionné
    if user_role == 'federation_admin' and not club:
        # Récupérer tous les clubs affiliés Ã  la fédération
        clubs = Club.objects.filter(federation=federation).order_by('name')
        
        # Récupérer toutes les compétitions Ã  venir (pour la liste)
        now = timezone.now().date()
        competitions = Competition.objects.filter(
            end_date__gte=now,
            status='published'
        ).order_by('start_date')
        
        return render(request, 'competitions/federations/select_club_for_registration.html', {
            'competitions': competitions,
            'clubs': clubs,
            'federation': federation
        })
    
    # Ã€ ce stade, nous avons un club (soit directement pour club_manager, soit sélectionné pour federation_admin)
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les disciplines du club
    club_disciplines = club.disciplines.all()
    
    # Récupérer toutes les compétitions Ã  venir filtrées par discipline
    now = timezone.now().date()
    competitions = Competition.objects.filter(
        end_date__gte=now,
        status='published'
    ).order_by('start_date')
    
    # Appliquer le filtrage automatique par discipline/fédération
    from apps.competitions.utils.discipline_filtering import filter_queryset_by_discipline_federation
    competitions = filter_queryset_by_discipline_federation(competitions, request.user)
    
    # Récupérer les inscriptions existantes du club en une seule requÃªte
    existing_registrations = CompetitionRegistration.objects.filter(
        practitioner__organization=club_organization
    ).values_list('competition_id', flat=True).distinct()
    
    # Filtres supplémentaires
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        # Vérifier que la discipline appartient bien aux disciplines du club
        try:
            discipline = Discipline.objects.get(id=discipline_id)
            if discipline in club_disciplines:
                competitions = competitions.filter(discipline_id=discipline_id)
            else:
                messages.warning(request, _("La discipline sélectionnée ne fait pas partie des disciplines de votre club."))
        except Discipline.DoesNotExist:
            pass
    
    competition_type = request.GET.get('type')
    if competition_type:
        competitions = competitions.filter(competition_types__name__icontains=competition_type)
    
    # Ajoutez cette gestion de la recherche
    search_query = request.GET.get('q')
    if search_query:
        competitions = competitions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(address__icontains=search_query)
        )
    
    # Disciplines pour le filtre - limitées aux disciplines du club
    disciplines = club_disciplines.order_by('name')
    
    # Pagination (optionnel)
    from django.core.paginator import Paginator
    paginator = Paginator(competitions, 10)  # 10 compétitions par page
    page_number = request.GET.get('page')
    competitions_page = paginator.get_page(page_number)
    
    return render(request, 'competitions/club/available_competitions.html', {
        'competitions': competitions_page,
        'club': club,
        'existing_registrations': existing_registrations,
        'is_federation_admin': user_role == 'federation_admin',
        'disciplines': disciplines,  # Maintenant filtrées selon le club
        'selected_discipline': discipline_id,
        'selected_type': competition_type,
        'search_query': search_query,
        'total_competitions': competitions.count(),
    })

def get_user_club(request):
    """
    Fonction utilitaire pour récupérer le club de l'utilisateur.
    Essaie différentes méthodes pour trouver le club associé.
    """
    # Essayer d'abord avec l'attribut direct
    if hasattr(request.user, 'club') and request.user.club:
        return request.user.club
    
    # Essayer ensuite avec le profil utilisateur
    if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
        return request.user.profile.club
    
    # Enfin, chercher le club dont l'utilisateur est propriétaire
    return Club.objects.filter(owner=request.user).first()

@login_required
def register_multiple_practitioners(request, competition_id):
    """Inscription de plusieurs pratiquants Ã  une compétition."""
    # Vérifier manuellement si l'utilisateur a les permissions nécessaires
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard')
    
    # Récupérer la compétition
    try:
        competition = get_object_or_404(Competition, pk=competition_id)
    except (ValueError, Competition.DoesNotExist):
        messages.error(request, _("Compétition non trouvée."))
        return redirect('competitions:club:available_competitions')
    
    # Vérifier si la compétition accepte toujours les inscriptions
    now = timezone.now().date()
    if competition.registration_deadline and competition.registration_deadline < now:
        messages.error(request, _("La date limite d'inscription Ã  cette compétition est dépassée."))
        return redirect('competitions:club:available_competitions')
    
    if hasattr(competition, 'status') and competition.status not in ['published', 'open']:
        messages.error(request, _("Cette compétition n'accepte pas les inscriptions actuellement."))
        return redirect('competitions:club:available_competitions')
    
    # Traiter l'inscription multiple
    if request.method == 'POST':
        practitioner_ids = request.POST.getlist('practitioners')
        
        if not practitioner_ids:
            messages.warning(request, _("Aucun pratiquant sélectionné."))
            return redirect('competitions:club:register_practitioner', competition_id=competition.id)
        
        success_count = 0
        error_count = 0
        already_registered = 0
        
        for practitioner_id in practitioner_ids:
            try:
                # Vérifier si le club a une organisation associée
                club_organization = club.organization or getattr(club, 'as_organization', None)
                if not club_organization:
                    # Passer Ã  l'itération suivante sans erreur
                    error_count += 1
                    continue
                    
                practitioner = get_object_or_404(Practitioner, pk=practitioner_id, organization=club_organization)
                
                # Vérifier si déjÃ  inscrit
                existing = CompetitionRegistration.objects.filter(
                    competition=competition,
                    practitioner=practitioner
                ).exists()
                
                if existing:
                    already_registered += 1
                    continue
                
                # Vérifier l'éligibilité en utilisant getattr pour éviter les erreurs d'attribut
                is_eligible = True
                reason = ""
                
                # Utiliser la méthode check_eligibility si elle existe
                if hasattr(competition, 'check_eligibility'):
                    try:
                        is_eligible, reasons = competition.check_eligibility(practitioner)
                        if not is_eligible and reasons:
                            reason = "; ".join(reasons)
                    except Exception as e:
                        logger.warning(f"Erreur lors de la vérification d'éligibilité: {str(e)}")
                        # Continuer malgré l'erreur
                
                # Sinon, vérifier manuellement mais prudemment avec getattr
                elif hasattr(practitioner, 'is_eligible_for_competition'):
                    try:
                        # Utiliser la méthode du pratiquant de façon sécurisée
                        is_eligible = practitioner.is_eligible_for_competition(competition)
                    except Exception as e:
                        logger.warning(f"Erreur lors de la vérification d'éligibilité: {str(e)}")
                        # Continuer malgré l'erreur
                
                # Créer l'inscription mÃªme si non éligible mais avec un avertissement
                if not is_eligible:
                    logger.warning(f"Pratiquant {practitioner.full_name} inscrit malgré inéligibilité: {reason}")
                
                # Créer l'inscription
                CompetitionRegistration.objects.create(
                    competition=competition,
                    practitioner=practitioner,
                    registration_date=timezone.now(),
                    status='pending'
                )
                success_count += 1
            except Exception as e:
                # Continuer avec les autres pratiquants en cas d'erreur
                error_count += 1
                logger.error(f"Erreur d'inscription du pratiquant {practitioner_id}: {str(e)}", exc_info=True)
        
        if success_count > 0:
            messages.success(request, _("{} pratiquant(s) inscrit(s) avec succès Ã  {}.").format(
                success_count, competition.title
            ))
        if already_registered > 0:
            messages.info(request, _("{} pratiquant(s) étaient déjÃ  inscrits.").format(already_registered))
        if error_count > 0:
            messages.warning(request, _("{} erreur(s) lors de l'inscription.").format(error_count))
        
        return redirect('competitions:club:registrations_list')
    
    # Si méthode GET, rediriger vers la page de sélection
    return redirect('competitions:club:register_practitioner', competition_id=competition.id)

@login_required
def competition_registration_form(request, competition_id):
    """Page d'inscription des pratiquants Ã  une compétition avec sélection multiple"""
    # Vérifier manuellement si l'utilisateur a les permissions nécessaires
    club = get_user_club(request)
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    competition = get_object_or_404(Competition, id=competition_id)
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        practitioners = Practitioner.objects.none()
    else:
        # Récupérer tous les pratiquants du club
        practitioners = Practitioner.objects.filter(organization=club_organization).order_by('last_name', 'first_name')
    
    # Récupérer les types de compétition disponibles
    competition_types = competition.competition_types.all()
    
    # Récupérer les inscriptions existantes
    existing_registrations = CompetitionRegistration.objects.filter(
        competition=competition,
        practitioner__organization=club_organization if club_organization else None
    )
    
    # Créer un dictionnaire des pratiquants déjÃ  inscrits et leurs types
    registered_practitioners = {}
    for reg in existing_registrations:
        if reg.practitioner_id not in registered_practitioners:
            registered_practitioners[reg.practitioner_id] = set()
        for comp_type in reg.competition_types.all():
            registered_practitioners[reg.practitioner_id].add(comp_type.id)
    
    if request.method == 'POST':
        # Traiter l'inscription en masse
        practitioners_ids = request.POST.getlist('practitioners')
        competition_type_ids = request.POST.getlist('competition_types')
        
        if not practitioners_ids:
            messages.warning(request, _("Aucun pratiquant sélectionné."))
            return redirect(request.path)
        
        if not competition_type_ids and competition_types.exists():
            messages.warning(request, _("Veuillez sélectionner au moins un type de compétition."))
            return redirect(request.path)
        
        count = 0
        errors = 0
        for practitioner_id in practitioners_ids:
            try:
                # Vérifier si le club a une organisation associée
                club_organization = club.organization or getattr(club, 'as_organization', None)
                if not club_organization:
                    # Passer Ã  l'itération suivante sans erreur
                    errors += 1
                    continue
                    
                practitioner = get_object_or_404(Practitioner, id=practitioner_id, organization=club_organization)
                
                # Vérifier si déjÃ  inscrit
                registration, created = CompetitionRegistration.objects.get_or_create(
                    competition=competition,
                    practitioner=practitioner,
                    defaults={
                        'registration_date': timezone.now(),
                        'status': 'pending'
                    }
                )
                
                # Mettre Ã  jour les types de compétition
                if competition_type_ids:
                    registration.competition_types.set(competition_type_ids)
                
                count += 1
            except Exception as e:
                errors += 1
                logger.error(f"Erreur pour {practitioner_id}: {str(e)}", exc_info=True)
                messages.error(request, f"Erreur pour {practitioner_id}: {str(e)}")
        
        messages.success(request, f"{count} pratiquant(s) inscrit(s) avec succès Ã  {competition.title}")
        if errors > 0:
            messages.warning(request, _("{} erreur(s) lors de l'inscription.").format(errors))
        
        return redirect('competitions:club:registrations_list')
    
    context = {
        'competition': competition,
        'practitioners': practitioners,
        'competition_types': competition_types,
        'registered_practitioners': registered_practitioners,
        'club': club,
    }
    
    return render(request, 'competitions/club/competition_registration_form.html', context)

@login_required
def club_bulk_registration(request):
    """Vue principale pour l'inscription de masse."""
    # Vérifier manuellement si l'utilisateur a les permissions nécessaires
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard')
    
    # Récupérer toutes les compétitions Ã  venir
    now = timezone.now().date()
    competitions = Competition.objects.filter(
        start_date__gte=now,
        status__in=['published', 'open']
    ).order_by('start_date')
    
    # Filtres
    discipline_id = request.GET.get('discipline')
    if discipline_id:
        competitions = competitions.filter(discipline_id=discipline_id)
    
    # Disciplines pour le filtre - Correction de l'import
    disciplines = Discipline.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'competitions/club/bulk_registration.html', {
        'club': club,
        'competitions': competitions,
        'disciplines': disciplines,
        'selected_discipline': discipline_id,
    })

@login_required
@require_POST
def cancel_registration(request, registration_id):
    """Annule une inscription Ã  une compétition."""
    # Vérifier manuellement si l'utilisateur a les permissions nécessaires
    club = get_user_club(request)
    
    if not club:
        messages.error(request, _("Vous devez Ãªtre responsable de club pour accéder Ã  cette page."))
        return redirect('competitions:dashboard')
    
    # Vérifier si le club a une organisation associée
    club_organization = club.organization or getattr(club, 'as_organization', None)
    
    if not club_organization:
        messages.warning(request, _("Aucune organisation associée trouvée pour ce club."))
        return redirect('competitions:dashboard')
    
    try:
        # Vérifier que l'inscription appartient bien Ã  un pratiquant du club
        registration = get_object_or_404(
            CompetitionRegistration, 
            id=registration_id,
            practitioner__organization=club_organization
        )
        
        practitioner_name = registration.practitioner.full_name
        competition_name = registration.competition.title
        
        registration.delete()
        
        messages.success(request, _("L'inscription de {} Ã  {} a été annulée.").format(
            practitioner_name, competition_name
        ))
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de l'inscription {registration_id}: {str(e)}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de l'annulation: {}").format(str(e)))
    
    return redirect('competitions:club:registrations_list')

