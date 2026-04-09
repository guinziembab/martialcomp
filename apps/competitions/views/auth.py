from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import resolve, Resolver404, reverse
from django.http import HttpResponseRedirect
from ..auth_forms import SignUpForm
from ..models import UserProfile
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils import timezone
import logging
# Importer correctement le signal
from ..models.users import create_user_profile
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def login_view(request):
    """Vue de connexion utilisateur."""
    # Rediriger si déjÃ  connecté
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('competitions:dashboard:index')
    
    # Préparer les informations de profil contextuel
    profile_info = None
    
    # Vérifier si nous sommes sur un sous-domaine d'organisation
    host = request.get_host().lower()
    if '.' in host and not host.startswith('www.') and 'martialcomp.com' in host:
        # Extraire le sous-domaine (par exemple: club-karate.martialcomp.com -> club-karate)
        subdomain = host.split('.')[0]
        
        # Essayer de trouver l'organisation correspondante
        try:
            from apps.multitenant.models import Tenant
            from apps.organizations.models import Organization
            
            # Trouver le tenant par slug (sous-domaine)
            tenant = Tenant.objects.filter(
                slug=subdomain,
                is_active=True
            ).first()
            
            if tenant:
                # Trouver l'organisation correspondante
                organization = Organization.objects.filter(
                    name=tenant.name,
                    is_active=True
                ).first()
                
                if organization:
                    profile_info = {
                        'role': f"Connexion Ã  {organization.name}",
                        'location': organization.address or "Lieu non spécifié",
                        'status': 'Actif' if organization.is_active else 'Inactif',
                        'status_class': 'active' if organization.is_active else 'inactive',
                        'valid_dates': None  # Peut Ãªtre étendu plus tard
                    }
        except ImportError:
            # Les modules ne sont pas disponibles
            pass
        except Exception:
            # Autres erreurs lors de la récupération de l'organisation
            pass
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Tentative d'authentification
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Récupérer l'URL de redirection
            next_url = request.POST.get('next')
            
            # Vérifier si next_url est sécurisé (non vide et interne au site)
            if next_url and not next_url.startswith('/'):
                next_url = None
                
            # Si aucune URL next ou URL invalide, rediriger vers le dashboard
            if not next_url:
                # Utiliser le système de nommage d'URL de Django au lieu d'un chemin en dur
                return redirect('competitions:dashboard:index')
            
            return redirect(next_url)
        else:
            messages.error(request, _("Identifiants invalides. Veuillez réessayer."))
    
    # Passer les informations de profil au template
    context = {
        'profile_info': profile_info
    }
    
    return render(request, 'registration/login.html', context)

def logout_view(request):
    """Vue de déconnexion utilisateur."""
    from django.utils import translation
    from django.conf import settings
    
    logout(request)
    messages.success(request, _("Vous êtes maintenant déconnecté."))
    
    # Obtenir la langue actuelle
    current_language = translation.get_language() or 'fr'
    
    # Rediriger vers la page d'accueil avec le préfixe de langue et le paramètre no_redirect
    return redirect(f'/{current_language}/?no_redirect=1')

@transaction.atomic
def signup_view(request):
    """Vue d'inscription utilisateur."""
    # Rediriger si déjÃ  connecté
    if hasattr(request, "user") and request.user.is_authenticated:
        return redirect('competitions:dashboard:index')
        
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                # Créer l'utilisateur avec les données du formulaire
                user = form.save()
                
                # S'assurer que l'utilisateur a un profil
                try:
                    # Vérifier si un profil existe déjÃ 
                    profile = UserProfile.objects.get(user=user)
                    
                    # Si le profil existe, mettre Ã  jour ses attributs
                    profile.role = 'spectator'
                    profile.onboarding_step = 'role_selection'
                    profile.onboarding_completed = False
                    profile.save()
                except UserProfile.DoesNotExist:
                    # Créer un nouveau profil si nécessaire
                    profile = UserProfile.objects.create(
                        user=user,
                        role='spectator',
                        onboarding_step='role_selection',
                        onboarding_completed=False
                    )
                
                # Connecter l'utilisateur avec backend spécifique
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Message de bienvenue
                messages.success(request, _("Compte créé avec succès ! Configurons maintenant votre profil."))
                
                # CORRECTION: Rediriger vers la page d'onboarding au lieu du dashboard
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Redirection de l'utilisateur {user.username} vers l'onboarding")
                
                # Rediriger vers la page de sélection de rÃ´le
                return redirect('competitions:onboarding:role_selection')
                    
            except IntegrityError as e:
                # Gérer spécifiquement l'erreur d'intégrité
                messages.error(request, _("Une erreur est survenue lors de la création du compte. Veuillez réessayer."))
                # Log l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur d'intégrité lors de la création du compte: {str(e)}")
                
            except Exception as e:
                # Gérer les autres exceptions
                messages.error(request, _("Une erreur inattendue est survenue. Veuillez réessayer."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la création du compte: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SignUpForm()
    
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_view(request):
    """Vue de profil utilisateur avec gestion de la modification."""
    user = request.user
    
    # S'assurer que l'utilisateur a un profil
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(
            user=user, 
            role='spectator',
            onboarding_step='role_selection',
            onboarding_completed=False
        )
    
    # Importer le formulaire de profil
    from ..forms.profile_forms import UserProfileForm
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, _("Votre profil a été mis Ã  jour avec succès !"))
                return redirect('profile')
            except Exception as e:
                messages.error(request, _("Une erreur est survenue lors de la mise Ã  jour de votre profil."))
                # Log l'erreur pour le débogage
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la mise Ã  jour du profil: {str(e)}")
        else:
            # Afficher les erreurs du formulaire
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = UserProfileForm(instance=profile, user=user)
    
    # Récupérer les organisations de l'utilisateur et leurs disciplines
    organizations = []
    discipline_ids = set()
    unique_disciplines = []
    
    # Organisation principale via le profil
    if profile.organization:
        organizations.append(profile.organization)
        for discipline in profile.organization.disciplines.all():
            if discipline.id not in discipline_ids:
                discipline_ids.add(discipline.id)
                unique_disciplines.append(discipline)
    
    # Organisations via OrganizationMember
    try:
        from apps.organizations.models import OrganizationMember
        memberships = OrganizationMember.objects.filter(
            user=user,
            is_active=True
        ).select_related('organization').prefetch_related('organization__disciplines')
        
        for membership in memberships:
            if membership.organization and membership.organization not in organizations:
                organizations.append(membership.organization)
                for discipline in membership.organization.disciplines.all():
                    if discipline.id not in discipline_ids:
                        discipline_ids.add(discipline.id)
                        unique_disciplines.append(discipline)
    except ImportError:
        pass
    
    context = {
        'user': user,
        'profile': profile,
        'form': form,
        'organizations': organizations,
        'disciplines': unique_disciplines,
    }
    
    return render(request, 'registration/profile.html', context)

@login_required
def password_change_view(request):
    """Vue de changement de mot de passe."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Importante pour maintenir la session utilisateur après changement de mot de passe
            update_session_auth_hash(request, user)
            messages.success(request, _("Votre mot de passe a été mis Ã  jour avec succès!"))
            return redirect('profile')
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'registration/password_change.html', {
        'form': form
    })


@login_required
def manage_organization_disciplines_view(request):
    """Vue pour gérer les disciplines de l'organisation de l'utilisateur."""
    user = request.user
    
    # Récupérer le profil de l'utilisateur
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        messages.error(request, _("Profil introuvable."))
        return redirect('profile')
    
    # Récupérer l'organisation principale
    organization = None
    if profile.organization:
        organization = profile.organization
    else:
        # Essayer de récupérer via OrganizationMember
        try:
            from apps.organizations.models import OrganizationMember
            membership = OrganizationMember.objects.filter(
                user=user,
                is_active=True
            ).first()
            if membership:
                organization = membership.organization
        except ImportError:
            pass
    
    if not organization:
        messages.error(request, _("Aucune organisation associée à votre compte."))
        return redirect('profile')
    
    # Vérifier les permissions
    has_permission = False
    try:
        from apps.organizations.models import OrganizationMember, OrganizationRole
        membership = OrganizationMember.objects.filter(
            user=user,
            organization=organization,
            is_active=True
        ).first()
        
        if membership:
            # Vérifier si l'utilisateur peut modifier l'organisation
            has_permission = (
                membership.role in [OrganizationRole.OWNER, OrganizationRole.ADMIN, OrganizationRole.MANAGER] or
                membership.can_edit_organization
            )
        
        # Si pas de membership mais que l'organisation a été créée par l'utilisateur
        if not has_permission and organization.created_by == user:
            has_permission = True
    except ImportError:
        # Si le module n'est pas disponible, on autorise si l'utilisateur a créé l'organisation
        has_permission = organization.created_by == user
    
    if not has_permission:
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour modifier les disciplines de cette organisation."))
        return redirect('profile')
    
    # Importer le formulaire
    from ..forms.profile_forms import OrganizationDisciplinesForm
    
    if request.method == 'POST':
        form = OrganizationDisciplinesForm(request.POST, organization=organization)
        if form.is_valid():
            try:
                # Mettre à jour les disciplines de l'organisation
                organization.disciplines.set(form.cleaned_data['disciplines'])
                messages.success(request, _("Les disciplines ont été mises à jour avec succès !"))
                return redirect('profile')
            except Exception as e:
                messages.error(request, _("Une erreur est survenue lors de la mise à jour des disciplines."))
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Erreur lors de la mise à jour des disciplines: {str(e)}")
        else:
            messages.error(request, _("Veuillez corriger les erreurs ci-dessous."))
    else:
        form = OrganizationDisciplinesForm(organization=organization)
    
    context = {
        'form': form,
        'organization': organization,
    }
    
    return render(request, 'registration/manage_disciplines.html', context)


def sso_login_view(request):
    """
    Vue SSO pour permettre la connexion automatique depuis l'application mobile.

    Cette vue consomme un token SSO à usage unique généré par l'API mobile
    et crée une session Django pour l'utilisateur.
    """
    import sys

    token = request.GET.get('token')

    if not token:
        messages.error(request, _("Token SSO manquant."))
        return redirect('account_login')

    try:
        from api_auth.models import SSOToken

        # Chercher le token
        sso_token = SSOToken.objects.filter(token=token).first()

        if not sso_token:
            print(f"SSO: Token invalide ou introuvable: {token[:10]}...", file=sys.stderr)
            messages.error(request, _("Token SSO invalide."))
            return redirect('account_login')

        # Vérifier si le token est valide
        if sso_token.used:
            print(f"SSO: Token déjà utilisé: {sso_token.id}", file=sys.stderr)
            messages.error(request, _("Ce lien de connexion a déjà été utilisé."))
            return redirect('account_login')

        if sso_token.is_expired:
            print(f"SSO: Token expiré: {sso_token.id}", file=sys.stderr)
            messages.error(request, _("Ce lien de connexion a expiré."))
            return redirect('account_login')

        # Token valide - connecter l'utilisateur
        user = sso_token.user

        # Connecter l'utilisateur AVANT de consommer le token
        # (si login() échoue, le token reste utilisable)
        try:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            print(f"SSO: login() réussi pour {user.username}", file=sys.stderr)
        except Exception as login_error:
            print(f"SSO: login() ÉCHOUÉ pour {user.username}: {login_error}", file=sys.stderr)
            messages.error(request, _("Une erreur est survenue lors de la connexion."))
            return redirect('account_login')

        # Marquer le token comme utilisé seulement après login réussi
        sso_token.consume()

        # Forcer la sauvegarde de la session
        request.session.save()
        print(f"SSO: Session sauvegardée, session_key={request.session.session_key}", file=sys.stderr)

        # Propager la langue depuis l'app mobile vers la session Django
        language = getattr(sso_token, 'language', None) or 'fr'
        from django.conf import settings as django_settings
        from django.utils import translation
        valid_langs = [code for code, name in django_settings.LANGUAGES]
        if language not in valid_langs:
            language = 'fr'

        translation.activate(language)
        # Django 4.2 : la clé de session pour la langue est '_language'
        request.session['_language'] = language
        request.session.save()
        print(f"SSO: Langue synchronisée: {language}", file=sys.stderr)

        # Rediriger vers l'URL demandée ou le dashboard par défaut
        redirect_url = sso_token.redirect_url or f'/{language}/competitions/dashboard/'

        # Vérifier que l'URL est sécurisée (interne)
        if not redirect_url.startswith('/'):
            redirect_url = f'/{language}/competitions/dashboard/'

        print(f"SSO: Redirection vers {redirect_url}", file=sys.stderr)

        # Construire la réponse de redirection manuellement pour s'assurer
        # que le cookie de session est bien inclus
        response = HttpResponseRedirect(redirect_url)

        # Forcer le cookie de session dans la réponse
        session_cookie_name = django_settings.SESSION_COOKIE_NAME
        session_cookie_age = django_settings.SESSION_COOKIE_AGE
        session_cookie_domain = django_settings.SESSION_COOKIE_DOMAIN
        session_cookie_secure = django_settings.SESSION_COOKIE_SECURE
        session_cookie_httponly = django_settings.SESSION_COOKIE_HTTPONLY
        session_cookie_samesite = getattr(django_settings, 'SESSION_COOKIE_SAMESITE', 'Lax')

        response.set_cookie(
            session_cookie_name,
            request.session.session_key,
            max_age=session_cookie_age,
            domain=session_cookie_domain,
            secure=session_cookie_secure,
            httponly=session_cookie_httponly,
            samesite=session_cookie_samesite,
        )

        # Poser le cookie django_language pour synchroniser la langue mobile → web
        lang_cookie_name = getattr(django_settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
        response.set_cookie(
            lang_cookie_name,
            language,
            max_age=getattr(django_settings, 'LANGUAGE_COOKIE_AGE', session_cookie_age),
            domain=getattr(django_settings, 'LANGUAGE_COOKIE_DOMAIN', session_cookie_domain),
            path=getattr(django_settings, 'LANGUAGE_COOKIE_PATH', '/'),
            secure=getattr(django_settings, 'LANGUAGE_COOKIE_SECURE', session_cookie_secure),
            httponly=getattr(django_settings, 'LANGUAGE_COOKIE_HTTPONLY', False),
            samesite=getattr(django_settings, 'LANGUAGE_COOKIE_SAMESITE', 'Lax'),
        )

        print(f"SSO: Cookies session + langue ({language}) ajoutés", file=sys.stderr)

        return response

    except ImportError:
        print("SSO: Module api_auth non disponible", file=sys.stderr)
        messages.error(request, _("Fonctionnalité SSO non disponible."))
        return redirect('account_login')
    except Exception as e:
        import traceback
        print(f"SSO: Erreur inattendue: {e}\n{traceback.format_exc()}", file=sys.stderr)
        messages.error(request, _("Une erreur est survenue lors de la connexion."))
        return redirect('account_login')

