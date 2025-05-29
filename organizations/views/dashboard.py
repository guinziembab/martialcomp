"""
Vue du tableau de bord des organisations.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from ..models import OrganizationMember, OrganizationRole


@login_required
def organization_dashboard(request):
    """Vue pour le tableau de bord des organisations de l'utilisateur."""
    # Récupérer les organisations dont l'utilisateur est membre
    memberships = OrganizationMember.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('organization')
    
    # Séparer par rôle
    organizations_by_role = {
        'owner': [],
        'admin': [],
        'manager': [],
        'other': []
    }
    
    for membership in memberships:
        org = membership.organization
        if membership.role == OrganizationRole.OWNER:
            organizations_by_role['owner'].append(org)
        elif membership.role == OrganizationRole.ADMIN:
            organizations_by_role['admin'].append(org)
        elif membership.role == OrganizationRole.MANAGER:
            organizations_by_role['manager'].append(org)
        else:
            organizations_by_role['other'].append(org)
    
    # Récupérer les invitations en attente si applicable
    # (à implémenter si un système d'invitation est ajouté)
    
    return render(request, 'organizations/dashboard.html', {
        'organizations_by_role': organizations_by_role,
        'total_organizations': sum(len(orgs) for orgs in organizations_by_role.values()),
    })