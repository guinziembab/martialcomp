# competitions/middleware/context.py
"""
Middleware pour la gestion du contexte organisationnel dans MartialComp.
Ce middleware charge les informations de rôle et permissions de l'utilisateur.
"""

from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject


def get_current_club(request):
    """Charge le club courant depuis la session."""
    club_id = request.session.get('current_club_id')
    if club_id:
        from competitions.models import Club
        try:
            return Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            return None
    return None


def get_club_membership(request):
    """Charge l'appartenance au club courant."""
    if not request.user.is_authenticated:
        return None
    
    club = getattr(request, 'current_club', None)
    if not club:
        return None
    
    from competitions.models import ClubMember
    try:
        return ClubMember.objects.select_related('role').prefetch_related(
            'additional_roles'
        ).get(
            user=request.user,
            club=club,
            status='active'
        )
    except ClubMember.DoesNotExist:
        # Fallback sur ClubAdministrator existant
        from competitions.models import ClubAdministrator
        try:
            admin = ClubAdministrator.objects.get(user=request.user, club=club)
            # Créer un objet compatible
            return _create_membership_from_admin(admin)
        except ClubAdministrator.DoesNotExist:
            return None


def _create_membership_from_admin(admin):
    """
    Crée un objet compatible ClubMember depuis un ClubAdministrator.
    Pour la période de transition.
    """
    class LegacyMembership:
        def __init__(self, admin):
            self.admin = admin
            self.user = admin.user
            self.club = admin.club
            self.role_code = admin.role
            self.status = 'active'
            
            # Mapping des permissions par rôle
            self._permissions_map = {
                'owner': {'*'},
                'admin': {
                    'members.view', 'members.create', 'members.edit', 'members.delete',
                    'members.export', 'members.grades',
                    'competitions.view', 'competitions.create', 'competitions.edit',
                    'competitions.manage', 'competitions.register',
                    'finance.view', 'finance.create', 'finance.edit', 'finance.approve',
                    'finance.export', 'finance.reports',
                    'organization.view', 'organization.edit', 'organization.settings',
                    'roles.view', 'roles.assign',
                    'documents.view', 'documents.create', 'documents.delete',
                    'communication.send', 'communication.manage',
                },
                'coach': {
                    'members.view', 'members.grades',
                    'competitions.view', 'competitions.register',
                    'training.view', 'training.create', 'training.manage',
                },
                'secretary': {
                    'members.view', 'members.create', 'members.edit', 'members.export',
                    'documents.view', 'documents.create',
                    'communication.send', 'communication.manage',
                },
            }
        
        @property
        def role(self):
            """Retourne un objet role-like."""
            class RoleLike:
                def __init__(self, code, name, icon, color):
                    self.code = code
                    self.name = name
                    self.icon = icon
                    self.color = color
            
            role_info = {
                'owner': ('Propriétaire', 'fa-crown', '#FFD700'),
                'admin': ('Administrateur', 'fa-user-shield', '#DC3545'),
                'coach': ('Entraîneur', 'fa-chalkboard-teacher', '#6F42C1'),
                'secretary': ('Secrétaire', 'fa-user-edit', '#17A2B8'),
            }
            info = role_info.get(self.role_code, ('Membre', 'fa-user', '#6C757D'))
            return RoleLike(self.role_code, info[0], info[1], info[2])
        
        @property
        def effective_permissions(self):
            return self._permissions_map.get(self.role_code, {'members.view'})
        
        def has_permission(self, permission):
            perms = self.effective_permissions
            if '*' in perms:
                return True
            return permission in perms
        
        def has_any_permission(self, *permissions):
            return any(self.has_permission(p) for p in permissions)
    
    return LegacyMembership(admin)


class OrganizationalContextMiddleware(MiddlewareMixin):
    """
    Middleware pour gérer le contexte organisationnel de l'utilisateur.
    
    Ajoute au request:
    - current_club: Le club actif (lazy)
    - current_federation: La fédération active (lazy)
    - club_membership: L'appartenance au club avec ses permissions
    - active_context: Le contexte actif (practitioner, judge, organizational)
    - user_permissions: Set des permissions effectives
    
    Configuration dans settings.py:
        MIDDLEWARE = [
            ...
            'competitions.middleware.context.OrganizationalContextMiddleware',
        ]
    
    Note: Ce middleware doit être APRÈS AuthenticationMiddleware.
    """
    
    def process_request(self, request):
        # Toujours définir les attributs, même pour les utilisateurs non authentifiés
        request.active_context = {'type': 'anonymous'}
        request.current_club = None
        request.current_federation = None
        request.club_membership = None
        request.user_permissions = set()
        
        if not request.user.is_authenticated:
            return
        
        # Récupérer le contexte actif depuis la session
        active_context = request.session.get('active_context', {'type': 'practitioner'})
        request.active_context = active_context
        
        # Charger le club de manière lazy
        request.current_club = SimpleLazyObject(lambda: get_current_club(request))
        
        # Charger le membership si un club est défini
        if request.session.get('current_club_id'):
            request.club_membership = SimpleLazyObject(lambda: get_club_membership(request))
            
            # Charger les permissions (non-lazy pour faciliter les vérifications)
            membership = get_club_membership(request)
            if membership:
                request.user_permissions = membership.effective_permissions
        
        # Charger la fédération si contexte fédération
        if active_context.get('type') == 'federation':
            federation_id = active_context.get('federation_id')
            if federation_id:
                from competitions.models import Federation
                try:
                    request.current_federation = Federation.objects.get(id=federation_id)
                except Federation.DoesNotExist:
                    pass


class AutoClubSelectionMiddleware(MiddlewareMixin):
    """
    Middleware optionnel pour sélectionner automatiquement un club
    si l'utilisateur n'en a qu'un seul.
    
    À placer APRÈS OrganizationalContextMiddleware.
    """
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return
        
        # Ne pas interférer si un club est déjà sélectionné
        if request.session.get('current_club_id'):
            return
        
        # Vérifier si l'utilisateur a un seul club
        from competitions.models import ClubMember, ClubAdministrator
        
        # Essayer d'abord avec ClubMember
        memberships = ClubMember.objects.filter(
            user=request.user,
            status='active'
        ).values_list('club_id', flat=True)[:2]
        
        if len(memberships) == 1:
            request.session['current_club_id'] = memberships[0]
            return
        
        # Fallback sur ClubAdministrator
        if len(memberships) == 0:
            admins = ClubAdministrator.objects.filter(
                user=request.user
            ).values_list('club_id', flat=True)[:2]
            
            if len(admins) == 1:
                request.session['current_club_id'] = admins[0]
