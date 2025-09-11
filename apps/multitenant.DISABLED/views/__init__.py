from django.core.exceptions import PermissionDenied
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

# This file makes the views directory a Python package