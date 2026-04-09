# competitions/utils/decorators.py
from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseForbidden, Http404
from django.core.exceptions import PermissionDenied
from django.conf import settings
from ..models import Federation
from django.contrib.auth.decorators import user_passes_test


# Import des modèles de manière absolue pour éviter les importations circulaires
from apps.competitions.models import Club, Federation, FederationAdministrator

def club_required(view_func):
    """
    Décorateur qui vérifie si l'utilisateur est associé Ã  un club.
    Le club est ajouté Ã  l'objet request comme attribut 'club'.
    Redirige vers le tableau de bord si aucun club n'est trouvé.
    
    Utilisation:
    @login_required
    @club_required
    def ma_vue(request, *args, **kwargs):
        # Le club est accessible via request.club
        club = request.club
        ...
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Récupérer le club de l'utilisateur
        club = None
        
        # Méthode 1: Vérifie si l'utilisateur a un attribut club et que c'est un objet Club
        if hasattr(request.user, 'club') and request.user.club and isinstance(request.user.club, Club):
            club = request.user.club
        
        # Méthode 2: Vérifie si l'utilisateur est propriétaire d'un club
        else:
            club = Club.objects.filter(owner=request.user).first()
        
        # Méthode 3: Vérifie si l'utilisateur est affilié Ã  un club via son profil
        if not club and hasattr(request.user, 'profile') and hasattr(request.user.profile, 'club'):
            club = request.user.profile.club
        
        # Si aucun club n'est trouvé, afficher un message d'erreur et rediriger
        if not club:
            messages.error(request, _(
                "Vous devez Ãªtre responsable de club pour accéder Ã  cette page. "
                "Veuillez créer un club ou contacter un administrateur pour Ãªtre associé Ã  un club existant."
            ))
            # Rediriger vers création de club si disponible
            try:
                from django.urls import reverse
                return redirect('competitions:onboarding:club')
            except:
                return redirect('competitions:dashboard:index')
        
        # Ajouter le club Ã  l'objet request au lieu de le passer comme paramètre
        request.club = club
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def federation_required(view_func):
    """
    Décorateur qui vérifie si l'utilisateur est associé Ã  une fédération,
    soit comme propriétaire, soit comme administrateur.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
            
        try:
            # Si c'est un admin système avec is_staff, pas de restrictions
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)
            
            # Récupérer le profil utilisateur
            if not hasattr(request.user, 'userprofile'):
                messages.error(request, _("Profil utilisateur introuvable."))
                return redirect('competitions:dashboard:index')
                
            profile = request.user.userprofile
                
            # Pour les admins fédération
            if profile.role == 'federation_admin':
                # Vérification si l'ID de fédération est dans les kwargs
                federation_id = kwargs.get('federation_id') or kwargs.get('pk')
                
                # 1. Essayer de trouver une fédération dont l'utilisateur est propriétaire
                user_federations = Federation.objects.filter(owner=request.user)
                
                # 2. Si aucune trouvée, vérifier les fédérations dont l'utilisateur est administrateur
                if not user_federations.exists():
                    # Utiliser FederationAdministrator pour trouver les fédérations administrées
                    admin_federations = Federation.objects.filter(
                        administrators__user=request.user,
                        administrators__is_primary=True
                    )
                    
                    if admin_federations.exists():
                        user_federations = admin_federations
                
                # Si aucune fédération trouvée, rediriger vers la création
                if not user_federations.exists():
                    messages.warning(request, _("Vous devez d'abord créer votre fédération."))
                    return redirect('competitions:onboarding:federation')
                
                # Utiliser la première fédération trouvée ou celle spécifiée par l'ID
                if federation_id:
                    try:
                        federation = user_federations.get(id=federation_id)
                    except Federation.DoesNotExist:
                        messages.error(request, _("Vous n'avez pas accès Ã  cette fédération."))
                        return HttpResponseForbidden(_("Accès non autorisé"))
                else:
                    federation = user_federations.first()
                
                # Ajouter la fédération Ã  la requÃªte
                request.federation = federation
                
                # Ajouter la discipline si disponible
                if hasattr(federation, 'discipline'):
                    request.discipline = federation.discipline
                
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, _("Vous n'avez pas le rÃ´le requis."))
                return redirect('competitions:dashboard:index')
                
        except Exception as e:
            import logging
            logger = logging.getLogger('django')
            logger.error(f"Erreur dans federation_required: {str(e)}", exc_info=True)
            
            messages.error(request, _("Une erreur est survenue: {}").format(str(e)))
            return redirect('competitions:dashboard:index')
            
    return _wrapped_view


def federation_or_club_required(view_func):
    """
    Décorateur qui vérifie si l'utilisateur est responsable de club ou de fédération.
    S'il est responsable de club, ajoute club Ã  request.
    S'il est responsable de fédération, ajoute federation Ã  request.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Vérifier si l'utilisateur est responsable de club
        club = Club.objects.filter(owner=request.user).first()
        if club:
            request.club = club
            return view_func(request, *args, **kwargs)
        
        # Vérifier si l'utilisateur est responsable de fédération
        federation = Federation.objects.filter(owner=request.user).first()
        if federation:
            request.federation = federation
            return view_func(request, *args, **kwargs)
        
        # Si ni l'un ni l'autre, refuser l'accès
        messages.error(request, _("Vous devez Ãªtre responsable de club ou de fédération pour accéder Ã  cette page."))
        return redirect('competitions:dashboard:index')
    
    return _wrapped_view


def federation_admin_by_param_required(federation_param='federation_id'):
    """
    Décorateur qui vérifie que l'utilisateur est administrateur de la fédération spécifiée par un paramètre d'URL.
    
    Args:
        federation_param: Le nom du paramètre d'URL qui contient l'ID de la fédération
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            federation_id = kwargs.get(federation_param)
            
            try:
                federation = Federation.objects.get(pk=federation_id)
            except Federation.DoesNotExist:
                raise Http404("Fédération non trouvée.")
            
            if not hasattr(request.user, 'is_federation_admin') or not request.user.is_federation_admin(federation):
                raise PermissionDenied("Vous n'Ãªtes pas administrateur de cette fédération.")
            
            # Ajouter la fédération Ã  la requÃªte pour éviter de la requÃªter Ã  nouveau
            request.federation = federation
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def club_admin_required(club_param='club_id'):
    """
    Décorateur qui vérifie que l'utilisateur est administrateur du club spécifié.
    
    Args:
        club_param: Le nom du paramètre d'URL qui contient l'ID du club
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            club_id = kwargs.get(club_param)
            
            try:
                club = Club.objects.get(pk=club_id)
            except Club.DoesNotExist:
                raise Http404("Club non trouvé.")
            
            if not hasattr(request.user, 'is_club_admin') or not request.user.is_club_admin(club):
                raise PermissionDenied("Vous n'Ãªtes pas administrateur de ce club.")
            
            # Ajouter le club Ã  la requÃªte pour éviter de le requÃªter Ã  nouveau
            request.club = club
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def manager_required(view_func):
    """
    Decorateur qui verifie si l'utilisateur est un manager de competition.
    Redirige vers la page de connexion si l'utilisateur n'est pas connecte
    ou vers le tableau de bord s'il n'a pas les permissions necessaires.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        # Si superuser ou staff, toujours autoriser
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        # Verifier si l'utilisateur a le role de manager via l'attribut direct
        if hasattr(request.user, 'role') and request.user.role in ['admin', 'manager', 'federation_admin', 'club_manager']:
            return view_func(request, *args, **kwargs)

        # Verifier via UserProfile
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            if hasattr(profile, 'role') and profile.role in ['admin', 'manager', 'federation_admin', 'club_manager', 'club_owner']:
                return view_func(request, *args, **kwargs)

        # Verifier si l'utilisateur est proprietaire d'un club ou d'une federation
        if Club.objects.filter(owner=request.user).exists():
            return view_func(request, *args, **kwargs)

        if Federation.objects.filter(owner=request.user).exists():
            return view_func(request, *args, **kwargs)

        # Verifier si l'utilisateur est administrateur d'une federation
        if FederationAdministrator.objects.filter(user=request.user).exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, "Vous n'avez pas les permissions necessaires pour acceder a cette page.")
        return redirect('competitions:dashboard:index')

    return wrapper


def judge_required(view_func):
    """
    Décorateur qui vérifie si l'utilisateur est un juge.
    Redirige vers la page de connexion si l'utilisateur n'est pas connecté
    ou vers le tableau de bord s'il n'a pas les permissions nécessaires.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Vérifier si l'utilisateur a le rÃ´le de juge
        if not hasattr(request.user, 'role') or request.user.role != 'judge':
            messages.error(request, "Vous devez Ãªtre juge pour accéder Ã  cette page.")
            return redirect('competitions:dashboard:index')
            
        return view_func(request, *args, **kwargs)
    return wrapper


def federation_admin_required(view_func):
    """
    Décorateur pour vérifier si l'utilisateur est administrateur de la fédération.
    Redirige vers la page d'accueil en cas d'échec avec un message d'erreur.
    """
    @wraps(view_func)
    def _wrapped_view(request, federation_id, *args, **kwargs):
        # Importer le modèle Federation ici pour éviter les imports circulaires
        from apps.competitions.models import Federation
        
        try:
            federation = Federation.objects.get(id=federation_id)
            
            # Vérifier si l'utilisateur est le propriétaire
            if federation.owner == request.user:
                return view_func(request, federation_id, *args, **kwargs)
                
            # Vérifier via FederationAdministrator
            if hasattr(request.user, 'federation_admin_roles'):
                is_admin = federation.administrators.filter(user=request.user).exists()
                if is_admin:
                    return view_func(request, federation_id, *args, **kwargs)
            
            # Si on arrive ici, l'utilisateur n'a pas les droits
            messages.error(request, _("Vous n'avez pas les droits d'accès Ã  cette fédération."))
            return redirect('competitions:dashboard:index')
            
        except Federation.DoesNotExist:
            messages.error(request, _("Fédération non trouvée."))
            return redirect('competitions:dashboard:index')
    
    return _wrapped_view

def federation_permission_required(permission):
    """
    Décorateur qui vérifie si l'utilisateur a une permission spécifique 
    pour une fédération.
    
    Args:
        permission: Le nom de la permission Ã  vérifier
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Vérifier si l'utilisateur est connecté
            if not request.user.is_authenticated:
                return redirect(settings.LOGIN_URL)
            
            # Vérifier si l'utilisateur a la permission demandée
            federation_id = kwargs.get('federation_id') or kwargs.get('pk') or kwargs.get('slug')
            
            if federation_id:
                # Tenter de récupérer la fédération
                try:
                    if kwargs.get('slug'):
                        federation = Federation.objects.get(slug=federation_id)
                    else:
                        federation = Federation.objects.get(id=federation_id)
                    
                    # Vérifier si l'utilisateur a la permission pour cette fédération
                    if hasattr(request.user, 'has_federation_permission') and request.user.has_federation_permission(federation, permission):
                        # Ajouter la fédération Ã  la requÃªte pour faciliter l'accès dans la vue
                        request.federation = federation
                        return view_func(request, *args, **kwargs)
                except Federation.DoesNotExist:
                    pass
            
            # Rediriger vers une page d'erreur ou d'accueil
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder Ã  cette page."))
            return redirect('competitions:welcome')
        
        return _wrapped_view
    
    return decorator

def competition_management_permission_required(view_func):
    """
    Vérifie si l'utilisateur a les permissions nécessaires pour gérer une compétition.
    L'utilisateur doit Ãªtre soit:
    - Un administrateur de site
    - Un administrateur de fédération
    - Un gestionnaire assigné Ã  la compétition
    """
    @wraps(view_func)
    def wrapper(request, competition_id, *args, **kwargs):
        # Import ici pour éviter l'import circulaire
        from apps.competitions.models import Competition, CompetitionRole
        
        # Vérifier si l'utilisateur est admin
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, competition_id, *args, **kwargs)
        
        # Récupérer la compétition
        competition = get_object_or_404(Competition, pk=competition_id)

        # Vérifier si l'utilisateur est le créateur de la compétition
        if competition.created_by and competition.created_by == request.user:
            return view_func(request, competition_id, *args, **kwargs)

        # Vérifier si l'utilisateur est admin de fédération
        # Vérifier si la compétition a un champ federation (pour compatibilité avec anciennes versions)
        if hasattr(competition, 'federation') and competition.federation:
            if hasattr(request.user, 'is_federation_admin') and request.user.is_federation_admin(competition.federation):
                return view_func(request, competition_id, *args, **kwargs)
        
        # Vérifier via organizing_organization
        if competition.organizing_organization:
            # Vérifier si l'utilisateur est propriétaire de l'organisation
            if hasattr(competition.organizing_organization, 'owner') and competition.organizing_organization.owner == request.user:
                return view_func(request, competition_id, *args, **kwargs)
            
            # Vérifier si l'organisation est une fédération et si l'utilisateur est admin
            if hasattr(competition.organizing_organization, 'federation'):
                federation = competition.organizing_organization.federation
                if hasattr(request.user, 'is_federation_admin') and request.user.is_federation_admin(federation):
                    return view_func(request, competition_id, *args, **kwargs)
            
        # Vérifier si l'utilisateur est un gestionnaire assigné via CompetitionRole
        # Note: CompetitionRole n'a pas de champ user, donc cette vérification est désactivée
        # Si vous avez besoin de cette fonctionnalité, créez un modèle UserCompetitionRole
        
        # Si l'organisation n'est pas définie, permettre l'accès à tous les utilisateurs connectés
        # (pour les compétitions créées directement sans organisation)
        if not competition.organizing_organization:
            return view_func(request, competition_id, *args, **kwargs)
        
        # Si la compétition est publiée, permettre l'accès en lecture seule
        if competition.status == 'published':
            return view_func(request, competition_id, *args, **kwargs)
        
        # Si l'utilisateur n'a pas les permissions, rediriger
        messages.error(request, _("Vous n'avez pas les permissions nécessaires pour gérer cette compétition."))
        return redirect('competitions:competitions:detail', pk=competition_id)
        
    return wrapper


def permission_required(permission_name):
    """
    Décorateur pour vérifier si l'utilisateur a une permission spécifique pour le club.
    
    Args:
        permission_name: Nom de la permission Ã  vérifier (ex: 'can_manage_practitioners')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
                
            # Si l'utilisateur est admin ou superuser, autoriser
            if request.user.is_staff or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Récupérer le club
            club = None
            if hasattr(request, 'club'):
                club = request.club
            else:
                # Essayer de récupérer le club depuis les kwargs ou la session
                club_id = kwargs.get('club_id')
                if club_id:
                    club = get_object_or_404(Club, id=club_id)
                    
            if not club:
                messages.error(request, _("Aucun club spécifié."))
                return redirect('competitions:dashboard:index')
            
            # Vérifier si l'utilisateur est propriétaire du club
            if club.owner == request.user:
                return view_func(request, *args, **kwargs)
            
            # Vérifier les rÃ´les et permissions
            from apps.competitions.models.permissions import UserClubRole
            user_roles = UserClubRole.objects.filter(
                user=request.user,
                club=club,
                is_active=True
            ).select_related('role')
            
            # Vérifier si l'un des rÃ´les a la permission requise
            for user_role in user_roles:
                if getattr(user_role.role, permission_name, False):
                    return view_func(request, *args, **kwargs)
            
            messages.error(request, _("Vous n'avez pas les permissions nécessaires pour accéder Ã  cette page."))
            return redirect('competitions:club:dashboard')
            
        return wrapper
    return decorator

