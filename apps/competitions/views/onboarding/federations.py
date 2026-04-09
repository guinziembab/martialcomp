from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.conf import settings

from ...models import Federation, Discipline
from ...forms.onboarding import FederationCreationForm

logger = logging.getLogger(__name__)


def create_federation_user(request):
    """
    Fonction de compatibilité - redirige vers handle_federation_creation
    """
    # Éviter la double exécution en vérifiant si c'est déjà un POST
    if request.method == 'POST':
        return handle_federation_creation(request)
    else:
        return handle_federation_creation(request)


@login_required
def handle_federation_creation(request):
    """Gestion de la création d'une fédération."""
    import time
    timestamp = time.time()
    logger.info(f"=== FEDERATION CREATION START [{timestamp}] - User: {request.user.username}, Method: {request.method} ===")
    
    # Si l'onboarding est déjà terminé (ex: via application mobile), rediriger
    if hasattr(request.user, 'profile') and getattr(request.user.profile, 'onboarding_completed', False):
        messages.info(request, _("Votre compte est déjà configuré."))
        return redirect('competitions:dashboard:federation')

    # Vérifier si une fédération existe déjà (PRIORITÉ ABSOLUE)
    existing_federation = Federation.objects.filter(owner=request.user).first()
    if existing_federation:
        logger.info(f"=== EXISTING FEDERATION FOUND [{timestamp}] - ID: {existing_federation.id} ===")
        messages.info(request, _("Vous avez déjà une fédération. Configuration terminée."))
        request.user.profile.onboarding_step = 'completed'
        request.user.profile.onboarding_completed = True
        request.user.profile.save()
        if 'onboarding_step' in request.session:
            del request.session['onboarding_step']
        return redirect('competitions:dashboard:federation', federation_id=existing_federation.id)
    
    # PROTECTION CONTRE LA DOUBLE EXÉCUTION - APRÈS VÉRIFICATION EXISTENCE
    if request.method == 'POST':
        if 'federation_creation_in_progress' in request.session:
            logger.warning(f"=== DOUBLE EXECUTION DETECTED [{timestamp}] - Redirecting ===")
            return redirect('competitions:dashboard:federations')
        
        # Marquer la création en cours IMMÉDIATEMENT
        request.session['federation_creation_in_progress'] = True
        logger.info(f"=== CREATION MARKED IN PROGRESS [{timestamp}] ===")

    # Vérifier si l'utilisateur a un profil
    if not hasattr(request.user, 'profile'):
        # Créer un profil temporaire pour permettre la création de fédération
        from ...models import UserProfile
        profile = UserProfile.objects.create(
            user=request.user,
            role='federation_admin',
            onboarding_step='federation'
        )
        logger.info(f"Created temporary profile for user {request.user.username}")
    
    # Vérifier le rôle seulement si ce n'est pas une création de fédération
    if request.method == 'GET' and request.user.profile.role != 'federation_admin':
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

            # Utiliser l'URL dashboard:federations au lieu de federations:federation_dashboard
            return redirect('competitions:dashboard:federations')
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification de la fédération existante: {str(e)}")
        # Continuer le processus même en cas d'erreur

    disciplines = Discipline.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        logger.info(f"=== POST REQUEST DETECTED [{timestamp}] ===")
        
        form = FederationCreationForm(request.POST, request.FILES)
        if form.is_valid():
            logger.info(f"=== FORM VALID [{timestamp}] - Creating federation ===")
            logger.info(f"=== FORM DATA [{timestamp}]: {form.cleaned_data} ===")
            try:
                with transaction.atomic():
                    federation = form.save(commit=False)
                    federation.owner = request.user

                    if 'logo' in request.FILES:
                        try:
                            from ...utils.upload import handle_federation_logo_upload
                            federation.logo = handle_federation_logo_upload(request.FILES['logo'], federation.name)
                        except ImportError:
                            # Si la fonction n'existe pas, sauvegarder directement
                            federation.logo = request.FILES['logo']

                    federation.save()

                    # CORRECTION CRITIQUE: Vérifier et forcer la sauvegarde de l'owner
                    # Car le form.save(commit=False) peut perdre des champs non inclus dans le form
                    if not federation.owner_id:
                        logger.warning(f"=== OWNER NOT SAVED [{timestamp}] - Forcing save ===")
                        federation.owner = request.user
                        federation.save(update_fields=['owner'])

                    # Double vérification après sauvegarde
                    federation.refresh_from_db()
                    logger.info(f"=== FEDERATION SAVED [{timestamp}] - ID: {federation.id}, Owner ID: {federation.owner_id} ===")

                    if not federation.owner_id:
                        # Dernier recours: mise à jour directe en base
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute(
                                "UPDATE competitions_federation SET owner_id = %s WHERE id = %s",
                                [request.user.id, federation.id]
                            )
                        logger.warning(f"=== FORCED OWNER UPDATE VIA SQL [{timestamp}] ===")

                    # Créer automatiquement un enregistrement FederationAdministrator
                    try:
                        from ...models import FederationAdministrator
                        fed_admin, created = FederationAdministrator.objects.get_or_create(
                            federation=federation,
                            user=request.user,
                            defaults={
                                'role': 'owner',
                                'is_primary': True
                            }
                        )
                        if created:
                            logger.info(f"=== FEDERATION ADMINISTRATOR CREATED [{timestamp}] for user {request.user.username} ===")
                        else:
                            logger.info(f"=== FEDERATION ADMINISTRATOR ALREADY EXISTS [{timestamp}] for user {request.user.username} ===")
                    except Exception as admin_error:
                        logger.warning(f"=== FEDERATION ADMINISTRATOR CREATION ERROR [{timestamp}]: {admin_error} ===")
                        # Continuer malgré l'erreur - l'owner est déjà défini

                    # Ajouter les disciplines sélectionnées
                    if 'disciplines' in request.POST:
                        discipline_ids = request.POST.getlist('disciplines')
                        for discipline_id in discipline_ids:
                            try:
                                discipline = Discipline.objects.get(id=discipline_id)
                                federation.disciplines.add(discipline)
                            except Discipline.DoesNotExist:
                                logger.warning(f"Discipline with id {discipline_id} not found")
                                continue

                    # Mettre à jour le profil utilisateur
                    if hasattr(request.user, 'profile'):
                        # S'assurer que le rôle est bien défini
                        if request.user.profile.role != 'federation_admin':
                            request.user.profile.role = 'federation_admin'
                            logger.info(f"Updated user {request.user.username} role to federation_admin")
                        
                        request.user.profile.onboarding_step = 'completed'
                        request.user.profile.onboarding_completed = True
                        request.user.profile.save()

                        logger.info(f"Associated federation {federation.id} with owner {request.user.username}")
                    else:
                        # Créer un profil UserProfile si il n'existe pas
                        from ...models import UserProfile
                        profile = UserProfile.objects.create(
                            user=request.user,
                            role='federation_admin',
                            onboarding_step='completed',
                            onboarding_completed=True
                        )
                        logger.info(f"Created UserProfile for user {request.user.username}")

                    # Nettoyer la session
                    if 'onboarding_step' in request.session:
                        del request.session['onboarding_step']

                    # Nettoyer la session
                    if 'onboarding_step' in request.session:
                        del request.session['onboarding_step']
                    if 'federation_creation_in_progress' in request.session:
                        del request.session['federation_creation_in_progress']

                    # VÉRIFICATION FINALE: S'assurer que l'owner est bien l'utilisateur connecté
                    federation.refresh_from_db()
                    if federation.owner_id != request.user.id:
                        logger.error(f"=== CRITICAL: Owner mismatch after creation [{timestamp}] - Expected: {request.user.id}, Got: {federation.owner_id} ===")
                        # Forcer la correction
                        Federation.objects.filter(id=federation.id).update(owner_id=request.user.id)
                        logger.info(f"=== FORCED OWNER CORRECTION [{timestamp}] ===")

                    # Stocker l'ID de la fédération créée dans la session pour référence
                    request.session['user_federation_id'] = federation.id
                    request.session['last_created_federation_id'] = federation.id

                    messages.success(request, _("Votre fédération a été créée avec succès ! Configuration terminée."))
                    logger.info(f"=== FEDERATION CREATED SUCCESSFULLY [{timestamp}] - ID: {federation.id}, Owner: {request.user.id} ===")

                    # Redirection directe vers le dashboard de CETTE fédération
                    return redirect('competitions:dashboard:federation', federation_id=federation.id)

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                logger.error(f"=== FEDERATION CREATION ERROR [{timestamp}]: {str(e)} ===")
                logger.error(f"=== TRACEBACK [{timestamp}]: {error_details} ===")

                # Nettoyer le flag de session en cas d'erreur
                if 'federation_creation_in_progress' in request.session:
                    del request.session['federation_creation_in_progress']

                # IMPORTANT: Vérifier si la fédération a quand même été créée malgré l'erreur
                created_federation = Federation.objects.filter(owner=request.user).first()
                if created_federation:
                    # La fédération existe, rediriger vers le dashboard
                    logger.info(f"=== FEDERATION EXISTS DESPITE ERROR [{timestamp}] - ID: {created_federation.id} ===")
                    messages.success(request, _("Votre fédération a été créée avec succès !"))
                    return redirect('competitions:dashboard:federation', federation_id=created_federation.id)

                messages.error(request, _("Une erreur est survenue lors de la création de la fédération."))
                # Afficher les détails de l'erreur en mode debug
                if settings.DEBUG:
                    messages.error(request, f"Détails de l'erreur: {str(e)}")
                    messages.error(request, f"Traceback: {error_details}")
        else:
            # Afficher les erreurs de validation du formulaire
            logger.warning(f"=== FORM INVALID [{timestamp}]: {form.errors} ===")
            logger.warning(f"=== FORM DATA [{timestamp}]: {request.POST} ===")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
                    logger.warning(f"Field {field} error: {error}")
    else:
        form = FederationCreationForm()

    return render(request, 'competitions/onboarding/federation_creation.html', {
        'form': form,
        'step': 'federation',
        'current_step': 'federation',
        'disciplines': disciplines
    })
