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