# competitions/permissions/__init__.py
"""
Module de gestion des permissions pour MartialComp.
Fournit des permissions granulaires pour les rôles organisationnels.
"""

from .definitions import (
    Permissions,
    PERMISSION_GROUPS,
    DEFAULT_ROLE_PERMISSIONS,
    PERMISSION_LABELS,
    get_permission_label,
    get_permissions_by_category,
)

from .decorators import (
    club_permission_required,
    any_permission_required,
    all_permissions_required,
    federation_permission_required,
)

__all__ = [
    # Classe de permissions
    'Permissions',

    # Groupes et configurations
    'PERMISSION_GROUPS',
    'DEFAULT_ROLE_PERMISSIONS',
    'PERMISSION_LABELS',

    # Fonctions utilitaires
    'get_permission_label',
    'get_permissions_by_category',

    # Décorateurs
    'club_permission_required',
    'any_permission_required',
    'all_permissions_required',
    'federation_permission_required',
]
