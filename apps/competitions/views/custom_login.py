from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.middleware.csrf import get_token
from django.urls import reverse
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme
from apps.core.isolation import OrganizationIsolationMixin, get_organization_queryset

@ensure_csrf_cookie
@csrf_protect  
@require_http_methods(["GET", "POST"])
def custom_login_view(request):
    """Vue de connexion professionnelle :
    - GET : affiche le template account/login.html (sauf si ?show_login=1, alors redirige vers accueil avec modale)
    - POST : traite la connexion comme avant
    """
    if request.method == "GET":
        if request.GET.get('show_login') == '1':
            return redirect(f"{reverse('welcome')}?show_login=1")
        get_token(request)
        next_url = request.GET.get('next', '')
        return render(request, 'account/login.html', {'next': next_url})
    
    elif request.method == "POST":
        # DEBUG: Log des informations CSRF
        import logging
        logger = logging.getLogger(__name__)
        if getattr(settings, 'DEBUG', False):
            logger.warning(f'CSRF token reçu: {request.POST.get("csrfmiddlewaretoken", "MANQUANT")}')
            logger.warning(f'CSRF cookie: {request.META.get("CSRF_COOKIE", "MANQUANT")}')
            logger.warning(f'Utilisateur: {request.POST.get("login", "MANQUANT")}')
        # Traiter la connexion
        username = request.POST.get('login', '')
        password = request.POST.get('password', '')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)

                    # Vérifier si une URL "next" est demandée (ex: lien d'inscription partagé)
                    next_url = request.POST.get('next') or request.GET.get('next', '')
                    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                        return redirect(next_url)

                    # Sinon, redirection selon le rôle
                    try:
                        from apps.competitions.models.users import UserProfile
                        profile = UserProfile.objects.get(user=user)

                        if profile.onboarding_completed:
                            # Redirection dashboard selon le rôle
                            role_map_names = {
                                'manager': 'competitions:dashboard:manager',
                                'club_manager': 'competitions:dashboard:club',
                                'participant': 'competitions:dashboard:participant',
                                'coach': 'competitions:dashboard:coach',
                                'referee': 'competitions:dashboard:referee',
                                'external_organizer': 'competitions:dashboard:external_organizer',
                                'spectator': 'competitions:dashboard:spectator'
                            }
                            role_key = str(profile.role).lower().strip()
                            if role_key == 'federation_admin':
                                from apps.competitions.models import Federation
                                federation = Federation.objects.filter(owner=user).first() or Federation.objects.filter(administrators__user=user).first()
                                if federation:
                                    return redirect(reverse('competitions:federations:federation_dashboard', kwargs={'federation_id': federation.id}))
                                else:
                                    return redirect(reverse('competitions:federations:list'))
                            else:
                                return redirect(reverse(role_map_names.get(role_key, 'competitions:dashboard:spectator')))
                        else:
                            # Redirection onboarding
                            return redirect(reverse('competitions:onboarding:role_selection'))

                    except:
                        # Fallback vers spectator
                        return redirect(reverse('competitions:dashboard:spectator'))
                else:
                    messages.error(request, _("Votre compte est désactivé."))
            else:
                messages.error(request, _("Nom d'utilisateur ou mot de passe incorrect."))
        else:
            messages.error(request, _("Veuillez remplir tous les champs."))
        
        # En cas d'erreur, retour vers welcome avec modal
        return redirect(f"{reverse('welcome')}?show_login=1&error=1")


