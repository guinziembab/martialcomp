from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from apps.competitions.models import Federation, Club
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def federation_clubs_debug(request, federation_id):
    """Vue de debug pour analyser les clubs d'une fédération."""
    federation = get_object_or_404(Federation, id=federation_id, owner=request.user)
    
    # Récupérer l'organisation de la fédération
    from apps.organizations.models import Organization, Affiliation
    if hasattr(federation, 'organization') and federation.organization:
        federation_org = federation.organization
    else:
        federation_org = Organization.objects.filter(old_federation_id=federation.id).first()
    
    print(f"DEBUG: Federation {federation.name} (ID: {federation.id})")
    print(f"DEBUG: Federation organization: {federation_org}")
    
    # Récupérer les organisations affiliées de type club
    affiliated_org_ids = []
    if federation_org:
        affiliations = Affiliation.objects.filter(
            parent_organization=federation_org,
            is_active=True
        )
        affiliated_org_ids = list(affiliations.values_list('child_organization_id', flat=True))
        print(f"DEBUG: Found {len(affiliated_org_ids)} affiliated organizations")
        for affiliation in affiliations:
            print(f"  - Affiliation: {affiliation.child_organization.name} (ID: {affiliation.child_organization_id})")
    
    # Récupérer tous les clubs pour comparaison
    all_clubs = get_organization_queryset(Club, self.request.user)
    print(f"DEBUG: Total clubs in database: {all_clubs.count()}")
    
    # Récupérer les clubs associés à ces organisations
    clubs = Club.objects.filter(organization_id__in=affiliated_org_ids).order_by('name')
    print(f"DEBUG: Clubs found with organization_id in {affiliated_org_ids}: {clubs.count()}")
    
    # Essayer une autre approche - clubs sans filtre d'organisation
    clubs_by_federation = Club.objects.filter(federation=federation) if hasattr(Club, 'federation') else []
    
    # Récupérer les disciplines disponibles pour les filtres
    disciplines = clubs.values_list('disciplines__name', flat=True).distinct()
    
    # Calculer des statistiques
    total_practitioners = sum(club.practitioners.count() for club in clubs)
    cities_count = clubs.values_list('city', flat=True).distinct().count()
    
    context = {
        'federation': federation,
        'federation_org': federation_org,
        'clubs': clubs,
        'affiliated_clubs': clubs,  # Alias pour le template
        'all_clubs': all_clubs,
        'clubs_by_federation': clubs_by_federation,
        'disciplines': disciplines,
        'total_practitioners': total_practitioners,
        'cities_count': cities_count,
        'affiliated_org_ids': affiliated_org_ids,
        'stats': {
            'clubs_count': clubs.count(),
            'practitioners_count': total_practitioners,
            'cities_count': cities_count,
        }
    }
    
    return render(request, 'competitions/federations/clubs_debug.html', context)