from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import OrganisateurNonMembre
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

def onboarding_organisateur_non_membre(request):
    # Affiche la page d'accueil d'onboarding
    return render(request, 'onboarding/organisateur_non_membre_welcome.html')

@login_required
def dashboard_organisateur_non_membre(request):
    # Affiche le dashboard dédié
    profil = OrganisateurNonMembre.objects.get(user=request.user)
    return render(request, 'dashboard/organisateur_non_membre_dashboard.html', {'user': request.user, 'profil': profil}) 
