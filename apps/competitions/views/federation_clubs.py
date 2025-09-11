from django.core.exceptions import PermissionDenied
# 1. Fichier de vue - competitions/views/federation_clubs.py
# --------------------------------------------------------------

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required

from apps.competitions.models import Federation, Club, Discipline, Practitioner
from apps.competitions.forms import ClubAffiliationForm  # Créez ce formulaire si nécessaire
from apps.competitions.utils.decorators import federation_admin_by_param_required
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
@federation_admin_by_param_required(federation_param='federation_id')
def manage_clubs(request, federation_id):
    """Vue pour gérer les clubs affiliés Ã  une fédération."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        from apps.organizations.models import Organization
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:dashboard:index')
    
    # Récupérer les organisations affiliées de type club
    from apps.organizations.models import Affiliation
    affiliated_org_ids = Affiliation.objects.filter(
        parent_organization=federation_org,
        is_active=True
    ).values_list('child_organization_id', flat=True)
    
    # Récupérer les clubs associés Ã  ces organisations
    affiliated_clubs = Club.objects.filter(
        organization_id__in=affiliated_org_ids
    ).order_by('name')
    
    # Récupérer les statistiques
    # Les praticiens sont liés aux clubs via organization
    affiliated_club_org_ids = affiliated_clubs.values_list('organization_id', flat=True)
    total_practitioners = Practitioner.objects.filter(
        organization_id__in=affiliated_club_org_ids
    ).count()
    
    # Récupérer les villes uniques et compter seulement celles qui sont non vides
    cities = affiliated_clubs.values_list('city', flat=True).distinct()
    cities_count = len([city for city in cities if city])
    
    # Récupérer toutes les disciplines pour les filtres
    disciplines = get_organization_queryset(Discipline, self.request.user).order_by('name')
    
    # Traitement de la suppression d'un club si demandé
    if request.method == 'POST' and 'club_id' in request.POST:
        club_id = request.POST.get('club_id')
        try:
            club = Club.objects.get(id=club_id)
            if club.organization and club.organization.id in affiliated_org_ids:
                # Désactiver l'affiliation
                Affiliation.objects.filter(
                    parent_organization=federation_org,
                    child_organization=club.organization
                ).update(is_active=False)
                
                messages.success(request, _("Le club {} a été retiré avec succès de votre fédération.").format(club.name))
                return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
            else:
                messages.error(request, _("Ce club n'est pas affilié Ã  votre fédération."))
        except Club.DoesNotExist:
            messages.error(request, _("Club introuvable."))
    
    context = {
        'federation': federation,
        'affiliated_clubs': affiliated_clubs,
        'total_practitioners': total_practitioners,
        'cities_count': cities_count,
        'disciplines': disciplines,
    }
    
    # Utiliser le template spécifique pour cette vue
    return render(request, 'competitions/federations/manage_clubs.html', context)

@login_required
@federation_admin_by_param_required(federation_param='federation_id')
def add_club_to_federation(request, federation_id):
    """Vue pour ajouter un club Ã  une fédération."""
    federation = get_object_or_404(Federation, id=federation_id)
    
    # Récupérer l'organisation de la fédération
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        from apps.organizations.models import Organization
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
    
    if request.method == 'POST':
        # Deux cas possibles : sélection d'un club existant ou création d'un nouveau club
        if 'existing_club' in request.POST:
            # Affilier un club existant
            club_id = request.POST.get('existing_club')
            try:
                club = Club.objects.get(id=club_id)
                
                # Vérifier si le club a une organisation
                if not club.organization:
                    messages.error(request, _("Ce club n'a pas d'organisation associée."))
                    return redirect('competitions:federations:add_club', federation_id=federation.id)
                
                # Vérifier si le club est déjÃ  affilié Ã  cette fédération
                from apps.organizations.models import Affiliation
                if Affiliation.objects.filter(
                    parent_organization=federation_org,
                    child_organization=club.organization,
                    is_active=True
                ).exists():
                    messages.warning(request, _("Ce club est déjÃ  affilié Ã  votre fédération."))
                else:
                    # Créer l'affiliation
                    from datetime import date
                    Affiliation.objects.create(
                        parent_organization=federation_org,
                        child_organization=club.organization,
                        affiliation_type='member',
                        start_date=date.today(),
                        is_active=True
                    )
                    messages.success(request, _("Le club {} a été affilié avec succès Ã  votre fédération.").format(club.name))
                return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
            except Club.DoesNotExist:
                messages.error(request, _("Club introuvable."))
        else:
            # Créer un nouveau club
            form = ClubAffiliationForm(request.POST, request.FILES)
            if form.is_valid():
                club = form.save(commit=False)
                # Si l'utilisateur est un responsable de club, l'affecter comme propriétaire
                if hasattr(request.user, 'profile') and request.user.profile.role == 'club_manager':
                    club.owner = request.user
                club.save()
                
                # Sauvegarder les relations ManyToMany
                form.save_m2m()
                
                # Créer l'affiliation avec la fédération
                if club.organization:
                    from apps.organizations.models import Affiliation
                    from datetime import date
                    Affiliation.objects.create(
                        parent_organization=federation_org,
                        child_organization=club.organization,
                        affiliation_type='member',
                        start_date=date.today(),
                        is_active=True
                    )
                
                messages.success(request, _("Le club {} a été créé et affilié avec succès Ã  votre fédération.").format(club.name))
                return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
    else:
        # Afficher le formulaire vide
        form = ClubAffiliationForm()
    
    # Récupérer les clubs non affiliés
    from apps.organizations.models import Affiliation
    
    # Récupérer les IDs des organisations déjÃ  affiliées Ã  cette fédération
    affiliated_org_ids = Affiliation.objects.filter(
        parent_organization=federation_org,
        is_active=True
    ).values_list('child_organization_id', flat=True)
    
    # Récupérer les clubs qui ne sont pas déjÃ  affiliés
    unaffiliated_clubs = Club.objects.filter(
        organization__isnull=False
    ).exclude(
        organization_id__in=affiliated_org_ids
    )
    
    context = {
        'federation': federation,
        'form': form,
        'unaffiliated_clubs': unaffiliated_clubs,
    }
    
    return render(request, 'competitions/federations/add_club.html', context)

@login_required
@federation_admin_by_param_required(federation_param='federation_id')
def remove_club_from_federation(request, federation_id, club_id):
    """Vue pour retirer un club d'une fédération."""
    federation = get_object_or_404(Federation, id=federation_id)
    club = get_object_or_404(Club, id=club_id)
    
    # Récupérer l'organisation de la fédération
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        from apps.organizations.models import Organization
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    if not federation_org:
        messages.error(request, _("La fédération n'a pas d'organisation associée."))
        return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
    
    # Vérifier que le club est bien affilié Ã  cette fédération
    from apps.organizations.models import Affiliation
    affiliation = Affiliation.objects.filter(
        parent_organization=federation_org,
        child_organization=club.organization,
        is_active=True
    ).first()
    
    if not affiliation:
        messages.error(request, _("Ce club n'est pas affilié Ã  votre fédération."))
        return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
    
    if request.method == 'POST':
        # Désactiver l'affiliation
        affiliation.is_active = False
        affiliation.save()
        messages.success(request, _("Le club {} a été retiré avec succès de votre fédération.").format(club.name))
        return redirect('competitions:federations:manage_clubs', federation_id=federation.id)
    
    context = {
        'federation': federation,
        'club': club,
    }
    
    return render(request, 'competitions/federations/confirm_remove_club.html', context)

