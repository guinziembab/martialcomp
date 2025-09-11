from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@login_required
def handle_external_organizer_profile(request):
    """Vue dâ€™onboarding pour le profil Organisateur non-membre."""
    if request.method == 'POST':
        # Récupérer les champs du formulaire
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        organisation = request.POST.get('organisation')
        telephone = request.POST.get('telephone')
        # Ici, tu peux ajouter la logique de sauvegarde ou de validation
        messages.success(request, _("Profil organisateur non-membre enregistré !"))
        # Marquer lâ€™onboarding comme terminé ou passer Ã  lâ€™étape suivante
        profile = request.user.profile
        profile.role = 'external_organizer'
        profile.onboarding_completed = True
        profile.onboarding_step = 'completed'
        profile.save()
        return redirect('/competitions/dashboard/external-organizer/')
    return render(request, 'competitions/onboarding/external_organizer_profile.html', {}) 
