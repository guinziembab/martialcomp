import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ...models import Federation, Discipline  # Ajout de l'import de Discipline
from ...forms.onboarding import FederationCreationForm

logger = logging.getLogger(__name__)

@login_required
def handle_federation_creation(request):
    """Gestion de la création d'une fédération."""
    # Vérifier si l'utilisateur a un profil et le rôle approprié
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'federation_admin':
        messages.error(request, _("Accès non autorisé. Vous devez être administrateur de fédération."))
        return redirect('onboarding:role_selection')
    
    # Vérifier si l'utilisateur a déjà une fédération
    try:
        existing_federation = Federation.objects.filter(owner=request.user).first()
        if existing_federation:
            messages.info(request, _("Vous avez déjà créé une fédération."))
            # Mettre à jour l'étape dans le profil et la session
            request.user.profile.onboarding_step = 'final_setup'
            request.user.profile.save()
            request.session['onboarding_step'] = 'final_setup'
            return redirect('onboarding:final_setup')
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification de la fédération existante: {str(e)}")
        # Continuer le processus même en cas d'erreur
    
    # Récupérer toutes les disciplines actives
    disciplines = Discipline.objects.filter(is_active=True).order_by('name')
    
    if request.method == 'POST':
        form = FederationCreationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    federation = form.save(commit=False)
                    federation.owner = request.user
                    
                    # Traitement du logo si présent
                    if 'logo' in request.FILES:
                        from ...utils.upload import handle_federation_logo_upload
                        federation.logo = handle_federation_logo_upload(request.FILES['logo'], federation.name)
                    
                    federation.save()
                    
                    # Traiter les disciplines sélectionnées si le modèle Federation a un champ disciplines
                    if hasattr(Federation, 'disciplines') and 'disciplines' in request.POST:
                        discipline_ids = request.POST.getlist('disciplines')
                        for discipline_id in discipline_ids:
                            try:
                                discipline = Discipline.objects.get(id=discipline_id)
                                federation.disciplines.add(discipline)
                            except Discipline.DoesNotExist:
                                continue
                    
                    # Mise à jour du profil utilisateur
                    if hasattr(request.user, 'profile'):
                        # Les signaux post_save du modèle Federation gèrent automatiquement
                        # l'association avec FederationAdministrator, pas besoin d'assigner federation
                        request.user.profile.onboarding_step = 'final_setup'
                        request.user.profile.save()
                        
                        logger.info(f"Associated federation {federation.id} with owner {request.user.username}")
                    
                    messages.success(request, _("Votre fédération a été créée avec succès !"))
                    
                    # Passage à l'étape finale
                    request.session['onboarding_step'] = 'final_setup'
                    return redirect('onboarding:final_setup')
            except Exception as e:
                logger.error(f"Erreur lors de la création de la fédération: {str(e)}")
                messages.error(request, _("Une erreur est survenue lors de la création de la fédération."))
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = FederationCreationForm()
    
    # Passer les disciplines au contexte du template
    return render(request, 'competitions/onboarding/federation_creation.html', {
        'form': form,
        'step': 'federation',
        'current_step': 'federation',
        'disciplines': disciplines  # Ajouter les disciplines au contexte
    })