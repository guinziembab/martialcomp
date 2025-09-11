from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def manager_dashboard(request):
  """Vue pour le dashboard manager"""

  context = {
  'page_title': _('Dashboard Manager'),
  'section': 'manager',
  'user': request.user,
  'user_role': getattr(request.user.profile, 'role', 'unknown') if hasattr(request.user, 'profile') else 'unknown'
  }

  # Toujours afficher le template, jamais de redirection
  return render(request, 'competitions/dashboard/manager.html', context)
