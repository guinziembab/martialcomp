"""
Points d'API pour les organisations.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from ..models import Organization, OrganizationMember


@login_required
@require_GET
def api_get_organizations(request):
    """API pour récupérer les organisations."""
    # Paramètres de filtrage
    org_type = request.GET.get('type')
    search_query = request.GET.get('q')
    
    # Construire la requête
    queryset = Organization.objects.filter(is_active=True)
    
    if org_type:
        queryset = queryset.filter(organization_type=org_type)
    
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(short_name__icontains=search_query)
        )
    
    # Limiter le nombre de résultats
    limit = int(request.GET.get('limit', 20))
    queryset = queryset[:limit]
    
    # Construire la réponse
    organizations = []
    for org in queryset:
        organizations.append({
            'id': org.id,
            'name': org.name,
            'short_name': org.short_name,
            'type': org.organization_type,
            'type_display': org.get_organization_type_display(),
            'country': org.country,
            'city': org.city,
        })
    
    return JsonResponse({'organizations': organizations})


@login_required
@require_GET
def api_get_user_organizations(request):
    """API pour récupérer les organisations de l'utilisateur."""
    # Récupérer les organisations dont l'utilisateur est membre
    memberships = OrganizationMember.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization')
    
    # Construire la réponse
    organizations = []
    for membership in memberships:
        org = membership.organization
        organizations.append({
            'id': org.id,
            'name': org.name,
            'role': membership.role,
            'role_display': membership.get_role_display(),
            'type': org.organization_type,
            'type_display': org.get_organization_type_display(),
            'can_edit': membership.can_edit_organization,
            'can_manage_members': membership.can_manage_members,
            'can_manage_competitions': membership.can_manage_competitions,
        })
    
    return JsonResponse({'organizations': organizations})