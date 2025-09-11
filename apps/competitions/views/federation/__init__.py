from django.core.exceptions import PermissionDenied
# Utilisez les noms exacts des fonctions telles qu'elles sont définies
from .licences import (
    licences_list,  # avec un 's'
    licence_create, # sans 's'
    licence_edit,   # sans 's', et 'edit' au lieu de 'update'
    licence_delete  # sans 's'
)
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# Définir __all__ avec les noms corrects
__all__ = [
    'licences_list', 'licence_create', 'licence_edit', 'licence_delete',
    # Autres noms...
]
