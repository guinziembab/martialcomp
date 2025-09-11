from django.core.exceptions import PermissionDenied
"""
Package pour les vues de l'application des organisations.
"""
# Importer les vues des différents modules pour les rendre disponibles directement
from .organizations import (
    OrganizationListView,
    OrganizationDetailView,
    OrganizationCreateView,
    OrganizationUpdateView,
    OrganizationDeleteView
)

from .affiliations import (
    AffiliationCreateView,
    AffiliationUpdateView,
    delete_affiliation
)

from .members import (
    OrganizationMemberListView,
    OrganizationMemberCreateView,
    OrganizationMemberUpdateView,
    delete_member,
    transfer_ownership
)

from .api import (
    api_get_organizations,
    api_get_user_organizations
)

from .dashboard import (
    organization_dashboard
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Fonctions de vue pour les URLs
def organization_list(request):
    """Vue pour la liste des organisations."""
    view = OrganizationListView()
    view.request = request
    return view.dispatch(request)

def organization_create(request):
    """Vue pour créer une organisation."""
    view = OrganizationCreateView()
    view.request = request
    return view.dispatch(request)

def organization_detail(request, pk):
    """Vue pour afficher une organisation."""
    view = OrganizationDetailView()
    view.request = request
    view.kwargs = {'pk': pk}
    return view.dispatch(request)

def organization_edit(request, pk):
    """Vue pour modifier une organisation."""
    view = OrganizationUpdateView()
    view.request = request
    view.kwargs = {'pk': pk}
    return view.dispatch(request)

def organization_delete(request, pk):
    """Vue pour supprimer une organisation."""
    view = OrganizationDeleteView()
    view.request = request
    view.kwargs = {'pk': pk}
    return view.dispatch(request)
