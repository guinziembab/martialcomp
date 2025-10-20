from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from ...models import UserProfile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def dashboard_pro(request):
    """Dashboard pour les coachs professionnels."""
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.role != 'coach':
            messages.error(request, _("Vous n'avez pas les droits d'accès à cette page."))
            return redirect('competitions:dashboard')
        
        # Logique du dashboard pro
        context = {
            # Ajoutez ici les données nécessaires
        }
        
        return render(request, 'competitions/dashboard/pro.html', context)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil utilisateur non trouvé. Veuillez contacter l'administrateur."))
        return redirect('welcome')
