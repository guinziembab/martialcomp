from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import Federation, Discipline
from ...forms.onboarding import FederationCreationForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)


@login_required
def handle_federation_creation(request):
    """Gestion de la création d'une fédération."""

    # Vérifier si l'utilisateur a un profil et le rôle approprié
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'federation_admin':
        messages.error(request, _("Accès non autorisé. Vous devez être administrateur de fédération."))
        return redirect('competitions:onboarding:role_selection')

    # Vérifier si l'utilisateur a déjà une fédération
    try:
        existing_federation = Federation.objects.filter(owner=request.user).first()
        if existing_federation:
            messages.info(request, _("Vous avez déjà une fédération. Redirection vers votre tableau de bord."))
            request.user.profile.onboarding_step = 'completed'
            request.user.profile.onboarding_completed = True
            request.user.profile.save()

            if 'onboarding_step' in request.session:
                del request.session['onboarding_step']

            return redirect('competitions:federations:federation_dashboard', federation_id=existing_federation.id)
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification de la fédération existante: {str(e)}")
        # Continuer le processus même en cas d'erreur

    disciplines = Discipline.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        form = FederationCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    federation = form.save(commit=False)
                    federation.owner = request.user

                    if 'logo' in request.FILES:
                        from ...utils.upload import handle_federation_logo_upload
                        federation.logo = handle_federation_logo_upload(request.FILES['logo'], federation.name)

                    federation.save()

                    if hasattr(Federation, 'disciplines') and 'disciplines' in request.POST:
                        discipline_ids = request.POST.getlist('disciplines')
                        for discipline_id in discipline_ids:
                            try:
                                discipline = Discipline.objects.get(id=discipline_id)
                                federation.disciplines.add(discipline)
                            except Discipline.DoesNotExist:
                                continue

                    if hasattr(request.user, 'profile'):
                        request.user.profile.onboarding_step = 'completed'
                        request.user.profile.onboarding_completed = True
                        request.user.profile.save()

                        logger.info(f"Associated federation {federation.id} with owner {request.user.username}")

                    if 'onboarding_step' in request.session:
                        del request.session['onboarding_step']

                    messages.success(request, _("Votre fédération a été créée avec succès ! Redirection vers le tableau de bord."))

                    return redirect('competitions:federations:federation_dashboard', federation_id=federation.id)

            except Exception as e:
                logger.error(f"Erreur lors de la création de la fédération: {str(e)}")
                messages.error(request, _("Une erreur est survenue lors de la création de la fédération."))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = FederationCreationForm()

    return render(request, 'competitions/onboarding/federation_creation.html', {
        'form': form,
        'step': 'federation',
        'current_step': 'federation',
        'disciplines': disciplines
    })
