from django.core.exceptions import PermissionDenied
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _, get_language
from django.urls import reverse, NoReverseMatch

from ...models import UserProfile
from ...forms.onboarding import RoleSelectionForm
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)


def _get_lang_prefix():
    """Retourne le préfixe de langue pour les URLs."""
    lang = get_language() or 'fr'
    if lang not in ['fr', 'en', 'es', 'de', 'it', 'pt']:
        lang = 'fr'
    return f'/{lang}'


@login_required
def handle_role_selection(request):
    """Gestion de la sélection du rôle dans le processus d'onboarding."""
    try:
        # Récupérer ou créer le profil utilisateur
        try:
            profile = UserProfile.objects.get(user=request.user)
            if getattr(profile, 'onboarding_completed', False):
                messages.info(request, _("Votre compte est déjà configuré."))
                role = getattr(profile, 'role', 'spectator')
                lang_prefix = _get_lang_prefix()

                # Redirection en fonction du rôle avec préfixe de langue
                if role == 'club_manager':
                    return redirect(f'{lang_prefix}/competitions/dashboard/club/')
                elif role == 'federation_admin':
                    return redirect(f'{lang_prefix}/competitions/dashboard/federation/')
                elif role == 'judge':
                    return redirect(f'{lang_prefix}/competitions/dashboard/referee/')
                elif role == 'participant':
                    return redirect(f'{lang_prefix}/competitions/dashboard/participant/')
                elif role == 'coach':
                    return redirect(f'{lang_prefix}/competitions/dashboard/coach/')
                else:
                    return redirect(f'{lang_prefix}/competitions/dashboard/')
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(
                user=request.user,
                role='spectator',
                onboarding_step='role_selection'
            )
            logger.info(f"Profil créé pour utilisateur {request.user.username}")

        # Traitement du formulaire POST
        if request.method == 'POST':
            form = RoleSelectionForm(request.POST)
            if form.is_valid():
                role = form.cleaned_data['role']
                profile.role = role

                # Étapes d'onboarding selon le rôle
                steps = {
                    'federation_admin': 'federation',
                    'club_manager': 'club_creation',
                    'judge': 'judge_profile',
                    'coach': 'coach_profile_simplified',
                    'participant': 'participant_profile',
                    'external_organizer': 'external_organizer_profile',
                    'spectator': 'final_setup'
                }

                next_step = steps.get(role, 'final_setup')
                profile.onboarding_step = next_step
                profile.save()
                request.session['onboarding_step'] = next_step

                route_name = f"competitions:onboarding:{next_step}"
                fallback_url = f"/competitions/onboarding/{next_step.replace('_', '/')}/"

                try:
                    return redirect(route_name)
                except NoReverseMatch:
                    return redirect(fallback_url)

                messages.success(request, _("Rôle sélectionné avec succès."))
                logger.info(f"Utilisateur {request.user.username} a sélectionné le rôle : {role}")
            else:
                messages.error(request, _("Rôle invalide sélectionné."))
        else:
            form = RoleSelectionForm()

        context = {
            'form': form,
            'step': 'role_selection',
            'current_step': 'role_selection',
            'profile': profile,
            'available_roles': [
                {
                    'key': 'participant',
                    'name': _('Participant'),
                    'description': _('Je participe aux compétitions'),
                    'icon': 'fas fa-user-ninja'
                },
                {
                    'key': 'club_manager',
                    'name': _('Gestionnaire de club'),
                    'description': _('Je gère un club'),
                    'icon': 'fas fa-users-cog'
                },
                {
                    'key': 'judge',
                    'name': _('Juge/Arbitre'),
                    'description': _('Je juge les compétitions'),
                    'icon': 'fas fa-gavel'
                },
                {
                    'key': 'coach',
                    'name': _('Entraîneur'),
                    'description': _('J’entraîne des pratiquants'),
                    'icon': 'fas fa-chalkboard-teacher'
                },
                {
                    'key': 'federation_admin',
                    'name': _('Administrateur fédération'),
                    'description': _('Je gère une fédération'),
                    'icon': 'fas fa-building'
                },
                {
                    'key': 'external_organizer',
                    'name': _('Organisateur externe'),
                    'description': _('J’organise des événements'),
                    'icon': 'fas fa-calendar-alt'
                },
                {
                    'key': 'spectator',
                    'name': _('Spectateur'),
                    'description': _('Je regarde les compétitions'),
                    'icon': 'fas fa-eye'
                },
            ]
        }

        return render(request, 'competitions/onboarding/role_selection.html', context)

    except Exception as e:
        logger.error(f"Erreur dans handle_role_selection: {e}", exc_info=True)
        messages.error(request, _("Une erreur est survenue lors de la sélection du rôle."))
        try:
            # Vérifier si l'utilisateur a un profil avec onboarding terminé
            profile = UserProfile.objects.filter(user=request.user).first()
            lang_prefix = _get_lang_prefix()
            if profile and getattr(profile, 'onboarding_completed', False):
                role = getattr(profile, 'role', 'spectator')
                if role == 'club_manager':
                    return redirect(f'{lang_prefix}/competitions/dashboard/club/')
                elif role == 'federation_admin':
                    return redirect(f'{lang_prefix}/competitions/dashboard/federation/')
                else:
                    return redirect(f'{lang_prefix}/competitions/dashboard/')
            # Sinon rediriger vers la page d'accueil
            return redirect(f'{lang_prefix}/')
        except Exception:
            return redirect('/fr/')
